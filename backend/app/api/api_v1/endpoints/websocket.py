import json
import asyncio
import logging
from typing import Annotated
from fastapi.websockets import WebSocketState

from redis.asyncio import Redis
from redis.asyncio.client import PubSub
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, crud, schemas
from app import translation
from app.api.dependencies import get_db, verify_current_user_w_cookie

from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)

router = APIRouter()


async def rlistener(websocket: WebSocket, channel: PubSub) -> None:
    while True:
        try:
            message = await channel.get_message(ignore_subscribe_messages=True)
            if message:
                # send received text from other users in this chat room back to this user
                await websocket.send_text(message["data"])
        except WebSocketDisconnect:
            logging.info("Websocket disconnected")
            break
        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.exception(f"Unexpected exception in rlistener {str(e)}")
            break


# TODO: I might need to append the user id to each message so I can use that in the front end to display the message left or right
async def create_message_ws(
    db: AsyncSession, obj_in: schemas.MessageCreate
) -> models.Message:
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

        # TODO: Implement only grabbing the previous X messages in chat
        chat_history = []
        for history_msg in await convo.awaitable_attrs.messages:
            if history_msg.orig_language == obj_in.orig_language:
                chat_history.append((obj_in.sender_id, history_msg.original_text))
            else:
                # if the message isn't in the language of the sender, then see if there's a translation for it
                for tls in await history_msg.awaitable_attrs.translations:
                    if tls.language == obj_in.orig_language:
                        chat_history.append((history_msg.sender_id, tls.translation))

        (await convo.awaitable_attrs.messages).append(message)
        await db.flush()

        # await crud.conversation.update_latest_msg(
        #     db=db, convo_id=convo.id, new_latest_msg_id=message.id
        # )
        convo.latest_message_id = message.id

        for member in await convo.awaitable_attrs.members:
            if member.id != obj_in.sender_id:
                text = await translation.gpt.translate(
                    sender_id=obj_in.sender_id,
                    target_language=member.target_language,
                    text_input=obj_in.original_text,
                    chat_history=chat_history,
                )

                if text is None:
                    await db.rollback()
                    raise Exception(
                        f"translation of {obj_in.original_text} to {member.target_language} for target user {member.id} could not be generated",
                    )

                # create the translation row
                new_translation = await crud.translation.create(
                    db=db,
                    obj_in=schemas.TranslationCreate(
                        translation=text,
                        language=member.target_language,
                        target_user_id=member.id,
                        message_id=message.id,
                    ),
                )
                (await message.awaitable_attrs.translations).append(new_translation)
            else:
                # just add the same message as a translation
                new_translation = await crud.translation.create(
                    db=db,
                    obj_in=schemas.TranslationCreate(
                        translation=obj_in.original_text,
                        language=member.target_language,
                        target_user_id=member.id,
                        message_id=message.id,
                    ),
                )
                (await message.awaitable_attrs.translations).append(new_translation)

        await db.commit()
        return message
    except IntegrityError as e:
        await db.rollback()
        raise Exception(str(e))


@router.websocket("/comms")
async def websocket_endpoint(
    websocket: WebSocket,
    user: Annotated[models.User, Depends(verify_current_user_w_cookie)],
) -> None:
    await websocket.accept()
    redis_client: Redis = websocket.app.state.redis_client

    async with redis_client.pubsub() as pubsub:
        try:
            for convo in user.conversations:
                await pubsub.subscribe(f"chat_{convo.id}_{user.target_language}")

            future = asyncio.create_task(rlistener(websocket, pubsub))

            while True:
                # handles this user sending a message to this chat room
                data = (
                    await websocket.receive_text()
                )  # necessary bc you can't send JSON directly over websockets
                message = json.loads(data)
                chat_id = message["conversation_id"]
                new_message = None

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
                    # translations = list of sent message in translated languages
                    new_message = await create_message_ws(db=db, obj_in=obj_in)

                # first publish to the sender's language channel
                formatted_sent_at = new_message.sent_at.isoformat() + (
                    "Z" if new_message.sent_at.utcoffset() is None else ""
                )
                await redis_client.publish(
                    f"chat_{chat_id}_{message['orig_language']}",
                    json.dumps({**message, "sent_at": formatted_sent_at}),
                )

                # User sends message to all channels of all the languages in this group chat
                # All subscribed users will get message
                for translation in await new_message.awaitable_attrs.translations:  # type: ignore
                    await redis_client.publish(
                        f"chat_{chat_id}_{translation.language}",
                        json.dumps(
                            {
                                **message,
                                "sent_at": formatted_sent_at,
                                "original_text": translation.translation,
                            }
                        ),
                    )

                # await manager.broadcast(data, websocket, chat_id)
        finally:
            # Cancel and await the listener task to ensure clean shutdown
            future.cancel()
            try:
                await future
            except asyncio.CancelledError:
                pass

            # Close the websocket if it's not already closed.
            if not websocket.client_state == WebSocketState.DISCONNECTED:
                await websocket.close(code=1000, reason="Server Shutdown")

            await pubsub.unsubscribe()
