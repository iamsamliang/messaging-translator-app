import json
import asyncio
import logging
from typing import Annotated
from app.exceptions import OpenAIAuthenticationException
from fastapi.websockets import WebSocketState
import openai

from redis.asyncio import Redis
from redis.asyncio.client import PubSub
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, crud, schemas
from app import translation
from app.api.dependencies import get_db, verify_current_user_w_cookie
from app.utils.aws import (
    get_cached_presigned_obj,
    CacheMethod,
    generate_presigned_get_url,
)
from app.core.config import settings

from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)

router = APIRouter()


async def subscription_manager(
    pubsub: PubSub, subscription_queue: asyncio.Queue[tuple[str, str]]
) -> None:
    while True:
        action, target_channel = await subscription_queue.get()

        if action == "subscribe":
            await pubsub.subscribe(target_channel)
        elif action == "unsubscribe":
            await pubsub.unsubscribe(target_channel)


async def rlistener(
    user: models.User,
    websocket: WebSocket,
    channel: PubSub,
    subscription_queue: asyncio.Queue[tuple[str, str]],
) -> None:
    while True:
        try:
            message = await channel.get_message(ignore_subscribe_messages=True)
            if message:
                channel_name = message["channel"]
                msg = json.loads(message["data"])
                msg_type = msg["type"]

                # channel for handling text messages
                if channel_name == str(user.id):
                    if msg_type == "message":
                        await websocket.send_text(message["data"])
                    elif msg_type == "create_convo":
                        convo_id = msg["convo_id"]
                        # new_channel = f"chat_{convo_id}_{user.target_language}"
                        new_channel = f"chat_{convo_id}"
                        await subscription_queue.put(("subscribe", new_channel))
                    else:
                        convo_id = msg["data"]["convo_id"]
                        res_channel = f"chat_{convo_id}"

                        if msg_type == "add_self":
                            action = "subscribe"
                        elif msg_type == "delete_self":
                            action = "unsubscribe"
                        else:
                            return

                        await subscription_queue.put((action, res_channel))
                        await websocket.send_text(message["data"])
                # channel for handling real-time modifications
                elif channel_name.startswith("chat_"):
                    if (
                        msg_type == "update_convo_name"
                        or msg_type == "update_convo_photo"
                        or msg_type == "delete_members"
                        or msg_type == "add_members"
                    ):
                        await websocket.send_text(message["data"])
                else:
                    logging.warning(
                        f"Received message from unknown channel: {channel_name}"
                    )
        except WebSocketDisconnect:
            logging.info("Websocket disconnected")
            break
        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.exception(f"Unexpected exception in rlistener {str(e)}")
            break


async def create_message_ws(
    db: AsyncSession, obj_in: schemas.MessageCreate, curr_user: models.User
) -> tuple[models.Message, dict[str, str]]:
    try:
        # 1) use conversation_id to get all users in the conversation, exclude sender
        # 2) for each user, grab their desired language
        # 3) translate original_text to each desired language
        # 4) Create a corresponding row in the translations table

        convo = await crud.conversation.get(db=db, id=obj_in.conversation_id)
        if convo is None:
            raise Exception(
                f"Convo w/ id {obj_in.conversation_id} doesn't exist",
            )

        message = await crud.message.create(db=db, obj_in=obj_in)

        # Grab previous N messages
        chat_history = []
        N = 25
        recent_msgs = (await convo.awaitable_attrs.messages)[-N:]

        for history_msg in recent_msgs:
            if history_msg.orig_language == obj_in.orig_language:
                chat_history.append((obj_in.sender_id, history_msg.original_text))
            else:
                # if the message isn't in the language of the sender, then see if there's a translation for it
                for tls in await history_msg.awaitable_attrs.translations:
                    if tls.language == obj_in.orig_language:
                        chat_history.append((history_msg.sender_id, tls.translation))

        (await convo.awaitable_attrs.messages).append(message)
        await db.flush()

        seen_translations = {obj_in.orig_language: obj_in.original_text}

        for member in await convo.awaitable_attrs.members:
            # if member.id != obj_in.sender_id:
            if member.target_language not in seen_translations:
                text = await translation.gpt.translate(
                    sender_id=obj_in.sender_id,
                    target_language=member.target_language,
                    text_input=obj_in.original_text,
                    chat_history=chat_history,
                    api_key=curr_user.api_key,
                )

                if text is None:
                    # await db.rollback()
                    raise openai.OpenAIError()
                    # raise Exception(
                    #     f"translation of {obj_in.original_text} to {member.target_language} for target user {member.id} could not be generated",
                    # )

                seen_translations[member.target_language] = text
            else:
                text = seen_translations[member.target_language]

            # create the translation row
            new_translation = await crud.translation.create(
                db=db,
                obj_in=schemas.TranslationCreate(
                    translation=text,
                    language=member.target_language,
                    target_user_id=member.id,
                    message_id=message.id,
                    is_read=int(member.id == obj_in.sender_id),
                ),
            )
            (await message.awaitable_attrs.translations).append(new_translation)
            # else:
            # just add the same message as a translation and set is_read=1 bc you are the one sending the message
            # new_translation = await crud.translation.create(
            #     db=db,
            #     obj_in=schemas.TranslationCreate(
            #         translation=obj_in.original_text,
            #         language=member.target_language,
            #         target_user_id=member.id,
            #         message_id=message.id,
            #         is_read=1,
            #     ),
            # )
            # (await message.awaitable_attrs.translations).append(new_translation)

        convo.latest_message_id = message.id
        await db.commit()
        return message, seen_translations
    except IntegrityError as e:
        await db.rollback()
        raise Exception(str(e))
    except openai.AuthenticationError:
        await db.rollback()
        raise
    except openai.OpenAIError:
        await db.rollback()
        raise
    except OpenAIAuthenticationException:
        await db.rollback()
        raise


@router.websocket("/comms")
async def websocket_endpoint(
    websocket: WebSocket,
    user: Annotated[models.User, Depends(verify_current_user_w_cookie)],
) -> None:
    await websocket.accept()
    # redis_client is shared among all consumers connected to
    # this websocket endpoint (efficiency)
    redis_client: Redis = websocket.app.state.redis_client
    listener_task = None
    subscription_task = None

    # though the redis_client is shared, the pubsub managers and their subscriptions are unique to each websocket connection
    async with redis_client.pubsub() as pubsub:
        try:
            await pubsub.subscribe(f"{user.id}")
            for convo in await user.awaitable_attrs.conversations:
                # await pubsub.subscribe(f"chat_{convo.id}_{user.target_language}")
                await pubsub.subscribe(f"chat_{convo.id}")

            subscription_queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()

            # start subscription manager task
            subscription_task = asyncio.create_task(
                subscription_manager(pubsub, subscription_queue)
            )

            # start message listener task
            listener_task = asyncio.create_task(
                rlistener(user, websocket, pubsub, subscription_queue)
            )

            # handles this user sending a message to this group chat
            while True:
                data = (
                    await websocket.receive_text()
                )  # necessary bc you can't send JSON directly over websockets
                message = json.loads(data)
                chat_id = message["conversation_id"]
                new_message = None
                # result_translations = {}

                # verify user is part of this conversation. if so get the convo
                async for db in get_db():
                    if not await crud.conversation.is_user_in_conversation(
                        db=db, user_id=user.id, conversation_id=chat_id
                    ):
                        raise WebSocketException(
                            code=status.WS_1008_POLICY_VIOLATION,
                            reason="User is not authorized to send messages to this chat",
                        )

                    obj_in = schemas.MessageCreate(
                        conversation_id=message["conversation_id"],
                        sender_id=message["sender_id"],
                        orig_language=message["orig_language"],
                        original_text=message["original_text"],
                    )
                    new_message, _ = await create_message_ws(
                        db=db, obj_in=obj_in, curr_user=user
                    )

                formatted_sent_at = new_message.sent_at.isoformat() + (  # type: ignore
                    "Z" if new_message.sent_at.utcoffset() is None else ""  # type: ignore
                )

                # Check if the sender's presigned URL is expired
                new_url = None

                if user.profile_photo:
                    _, cached_url = await get_cached_presigned_obj(
                        object_key=user.profile_photo,
                        redis_client=redis_client,
                        method=CacheMethod.GET,
                    )

                    if not cached_url:  # sender_id expired
                        new_url = await generate_presigned_get_url(
                            bucket_name="translation-messaging-bucket",
                            object_key=user.profile_photo,
                            expire_in_secs=settings.S3_PRESIGNED_URL_GET_EXPIRE_SECS,
                            redis_client=redis_client,
                        )

                # User sends message to all channels of all the languages in this group chat
                # All subscribed users will get message
                for translation in await new_message.awaitable_attrs.translations:  # type: ignore
                    # used to publish to: f"chat_{chat_id}_{translation.language}"
                    if (
                        translation.target_user_id != user.id
                    ):  # don't send to sender's channel
                        await redis_client.publish(
                            f"{translation.target_user_id}",
                            json.dumps(
                                {
                                    "type": "message",
                                    "data": {
                                        **message,
                                        "sent_at": formatted_sent_at,
                                        "original_text": translation.translation,
                                        "translation_id": translation.id,
                                        "target_user_id": translation.target_user_id,
                                        "new_presigned": new_url,
                                    },
                                }
                            ),
                        )
        except WebSocketDisconnect:
            pass  # if client disconnects, don't need to do anything
        except (openai.AuthenticationError, OpenAIAuthenticationException):
            await websocket.send_json(
                {
                    "type": "error",
                    "data": "Your OpenAI API key is invalid, expired, or revoked. Please generate a new one and update it here for use.",
                }
            )
        except openai.OpenAIError as e:
            error_message = "An error occurred with the translation service."

            if isinstance(e, openai.RateLimitError):
                error_message = (
                    "Your OpenAI rate limit exceeded. Check your OpenAI API usage."
                )
            elif isinstance(e, openai.APIConnectionError):
                error_message = "Issue connecting to OpenAI services. Please wait a few seconds and try again."
            elif isinstance(e, (openai.InternalServerError, openai.APIError)):
                error_message = "A server error occured on OpenAI's side. Check their status page for any ongoing incidents. And, wait a few seconds and try again."
            elif isinstance(e, openai.APITimeoutError):
                error_message = "Your message took too long to translate and OpenAI closed the connection. Wait a few seconds and retry your request. If it still doesn't work, try splitting up your message into smaller chunks."
            elif isinstance(e, openai.PermissionDeniedError):
                error_message = "You don't have access to GPT-4. Ensure you are using a valid and correct OpenAI API key."

            await websocket.send_json({"type": "error", "data": error_message})
        finally:
            # Cancel and await the listener and subscription tasks to ensure clean shutdown
            if listener_task is not None:
                listener_task.cancel()
                try:
                    await listener_task
                except asyncio.CancelledError:
                    pass

            if subscription_task is not None:
                subscription_task.cancel()
                try:
                    await subscription_task
                except asyncio.CancelledError:
                    pass

            # Close the websocket if it's not already closed.
            if not websocket.client_state == WebSocketState.DISCONNECTED:
                await websocket.close(code=1000, reason="Server Shutdown")

            await pubsub.unsubscribe()
