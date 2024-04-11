import json
import asyncio
import logging
from app.exceptions import OpenAIAuthenticationException
from fastapi.websockets import WebSocketState
import openai

from redis.asyncio import Redis
from redis.asyncio.client import PubSub
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, crud, schemas
from app import translation
from app.api.dependencies import get_db
from app.utils.aws import (
    get_cached_presigned_obj,
    CacheMethod,
    generate_presigned_get_url,
)
from app.core.config import settings

from fastapi import (
    APIRouter,
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
    user_id: int,
    websocket: WebSocket,
    channel: PubSub,
    subscription_queue: asyncio.Queue[tuple[str, str]],
) -> None:
    try:
        while True:
            message = await channel.get_message(ignore_subscribe_messages=True)
            if message:
                channel_name = message["channel"]
                msg = json.loads(message["data"])
                msg_type = msg["type"]

                # channel for handling text messages
                if channel_name == str(user_id):
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
                    logging.error(
                        f"Received message from unknown channel: {channel_name}"
                    )
    except WebSocketDisconnect:
        logging.error("Websocket disconnected")
        raise
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logging.error(f"Unexpected exception in rlistener", exc_info=True)
        raise


async def create_message_ws(
    db: AsyncSession, obj_in: schemas.MessageCreate, curr_user: models.User
) -> tuple[models.Message, dict[str, str], list[models.Translation]]:
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

        # Grab previous N messages
        chat_history = []

        # optimal
        recent_msgs = await crud.message.get_most_recent_messages(
            db=db,
            convo_id=convo.id,
            offset=0,
            limit=settings.CHAT_HISTORY_NUM_PREV_MSGS,
        )

        for history_msg in reversed(recent_msgs):
            if history_msg.orig_language == obj_in.orig_language:
                chat_history.append((obj_in.sender_id, history_msg.original_text))
            else:
                # if the message isn't in the language of the sender, then see if there's a translation for it
                for tls in await history_msg.awaitable_attrs.translations:
                    if tls.language == obj_in.orig_language:
                        chat_history.append((history_msg.sender_id, tls.translation))

        seen_translations = {obj_in.orig_language: obj_in.original_text}

        message = await crud.message.create(db=db, obj_in=obj_in)
        await db.flush()

        created_translations = []

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
            created_translations.append(new_translation)
            # (await message.awaitable_attrs.translations).append(new_translation)

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
        return message, seen_translations, created_translations
    except IntegrityError:
        await db.rollback()
        raise
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
    token: str,
    user_email: str,
) -> None:
    # redis_client is shared among all consumers connected to
    # this websocket endpoint (efficiency)
    redis_client: Redis = websocket.app.state.redis_client

    try:
        # User Auth
        redis_ws_token = await redis_client.get(user_email)

        if not redis_ws_token or redis_ws_token != token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # after used to authenticate user in websocket endpoint, delete it from redis cache
        await redis_client.delete(user_email)
    except Exception as e:
        logging.error(
            "Error in authenticating websocket connection or Redis Error",
            exc_info=True,
        )
        return

    user = None
    user_convos = []
    async for db in get_db():
        user = await crud.user.get_by_email(db=db, email=user_email)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user_convos = await user.awaitable_attrs.conversations

    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    listener_task = None
    subscription_task = None

    max_retries = 3
    retry_delay = 2  # seconds

    # though the redis_client is shared, the pubsub managers and their subscriptions are unique to each websocket connection
    async with redis_client.pubsub() as pubsub:
        try:
            await pubsub.subscribe(f"{user.id}")
            for convo in user_convos:
                # await pubsub.subscribe(f"chat_{convo.id}_{user.target_language}")
                await pubsub.subscribe(f"chat_{convo.id}")

            subscription_queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()

            # start subscription manager task
            subscription_task = asyncio.create_task(
                subscription_manager(pubsub, subscription_queue)
            )

            # start message listener task
            listener_task = asyncio.create_task(
                rlistener(user.id, websocket, pubsub, subscription_queue)
            )

            # handles this user sending a message to this group chat
            while True:
                data = (
                    await websocket.receive_text()
                )  # necessary bc you can't send JSON directly over websockets
                message = json.loads(data)
                chat_id = message["conversation_id"]
                new_message = None
                created_translations = None

                # verify user is part of this conversation. if so get the convo
                try:
                    async for db in get_db():
                        if not (
                            await crud.conversation.is_user_in_conversation(
                                db=db, user_id=user.id, conversation_id=chat_id
                            )
                        ):
                            raise WebSocketException(
                                code=status.WS_1008_POLICY_VIOLATION,
                                reason="User is not authorized to send messages to this chat",
                            )

                        # update user
                        user = await crud.user.get(db=db, id=user.id)
                        if user is None:
                            raise WebSocketException(
                                code=status.WS_1014_BAD_GATEWAY,
                                reason="You (user) do not exist",
                            )

                        obj_in = schemas.MessageCreate(
                            conversation_id=message["conversation_id"],
                            sender_id=message["sender_id"],
                            orig_language=message["orig_language"],
                            original_text=message["original_text"],
                        )

                        new_message, _, created_translations = await create_message_ws(
                            db=db, obj_in=obj_in, curr_user=user
                        )
                except (openai.AuthenticationError, OpenAIAuthenticationException):
                    await websocket.send_json(
                        {
                            "type": "error",
                            "data": "Your message failed to send because your OpenAI API key is invalid or expired. Please update the key in your user settings.",
                        }
                    )

                    continue
                except openai.OpenAIError as e:
                    error_message = "Your message failed to send because an error occurred with the translation service."

                    if isinstance(e, openai.RateLimitError):
                        error_message = "Your message failed to send because your OpenAI rate limit exceeded. Check your OpenAI API usage."
                    elif isinstance(e, openai.APIConnectionError):
                        error_message = "Issue connecting to OpenAI services. Please wait a few seconds and try sending your message again."
                    elif isinstance(e, (openai.InternalServerError, openai.APIError)):
                        error_message = "A server error occured on OpenAI's side. Check their status page for any ongoing incidents before trying to send your message again."
                    elif isinstance(e, openai.APITimeoutError):
                        error_message = "Your message took too long to translate and OpenAI closed the connection. Wait a few seconds and try sending your message again. If it still doesn't work, try splitting up your message into smaller chunks."
                    elif isinstance(e, openai.PermissionDeniedError):
                        error_message = "Your message failed to send because you don't have access to GPT-4. Ensure you are using a valid and correct OpenAI API key."

                    await websocket.send_json({"type": "error", "data": error_message})

                    continue
                except IntegrityError:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "data": "Your message failed to send. Please try again.",
                        }
                    )

                    continue

                formatted_sent_at = new_message.sent_at.isoformat() + (  # type: ignore
                    "Z" if new_message.sent_at.utcoffset() is None else ""  # type: ignore
                )

                # Check if the sender's presigned URL is expired
                new_url = None

                # Ignore errors bc not being able to get presigned URL
                # shouldn't cancel sending message
                try:
                    if user.profile_photo:
                        _, cached_url = await get_cached_presigned_obj(
                            object_key=user.profile_photo,
                            redis_client=redis_client,
                            method=CacheMethod.GET,
                        )

                        if not cached_url:  # sender_id expired
                            new_url = await generate_presigned_get_url(
                                bucket_name=settings.S3_BUCKET_NAME,
                                object_key=user.profile_photo,
                                expire_in_secs=settings.S3_PRESIGNED_URL_GET_EXPIRE_SECS,
                                redis_client=redis_client,
                            )
                except Exception as e:
                    logging.error(
                        "Exception in getting presigned object from Redis cache or generating presigned URL",
                        exc_info=True,
                    )

                # User sends message to all channels of all the languages in this group chat
                # All subscribed users will get message
                pub_messages = []
                for translation in created_translations:  # type: ignore
                    # used to publish to: f"chat_{chat_id}_{translation.language}"
                    if (
                        translation.target_user_id != user.id
                    ):  # don't send to sender's channel
                        pub_messages.append(
                            (
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
                        )
                        # await redis_client.publish(
                        #     f"{translation.target_user_id}",
                        #     json.dumps(
                        #         {
                        #             "type": "message",
                        #             "data": {
                        #                 **message,
                        #                 "sent_at": formatted_sent_at,
                        #                 "original_text": translation.translation,
                        #                 "translation_id": translation.id,
                        #                 "target_user_id": translation.target_user_id,
                        #                 "new_presigned": new_url,
                        #             },
                        #         }
                        #     ),
                        # )

                # Retry publish attempts on error
                for attempt in range(max_retries):
                    try:
                        await asyncio.gather(
                            *(
                                redis_client.publish(channel, message)
                                for channel, message in pub_messages
                            )
                        )
                        break
                    except Exception as e:
                        logging.error(
                            f"Error during message publishing, attempt {attempt + 1}",
                            exc_info=True,
                        )
                        await asyncio.sleep(retry_delay)  # wait before retrying
        except WebSocketDisconnect:
            pass  # if client disconnects, don't need to do anything
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
