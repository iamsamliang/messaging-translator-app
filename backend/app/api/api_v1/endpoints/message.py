from typing import Annotated
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status, Response, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import crud, models, schemas, translation
from app.api.dependencies import DatabaseDep, verify_current_user_w_cookie

router = APIRouter()


# Messages


@router.get("/{conversation_id}", response_model=list[schemas.MessageResponse])
async def get_messages_sent(
    db: DatabaseDep,
    current_user: Annotated[models.User, Depends(verify_current_user_w_cookie)],
    conversation_id: int,
) -> list[models.Message]:
    try:
        chat_history = []  # type: ignore
        convo = await crud.conversation.get(db=db, id=conversation_id)
        if convo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Convo w/ id {conversation_id} doesn't exist",
            )

        # Chat History: Grabbing the previous history as it was translated (if there is any history) irrespective of user's current language
        prev_msg = None
        for message in await convo.awaitable_attrs.messages:
            # GETTING CHAT HISTORY IN USER'S LANGUAGE
            # In the current conversation, for each previous message:

            # 1: Is there a translation of it in the user's selected language
            # YES: Modify Message. Append to chat_history. Proceed to #4
            # NO: Proceed to #4

            # 2: Did the user send this message?
            # YES: Append to chat_history. Proceed to #4
            # NO: Proceed to #4

            # 3: Is there a translation of it in the user's previous languages? (use target_user_id=current_user.id to grab)
            # YES: Modify Message. Append to chat_history. Proceed to #4
            # NO: Proceed to #4

            # 4: Inspect next Message in Conversation
            # NOTE: Has not been implemented yet. If implementing need to also change how the LATEST MESSAGE TRANSLATION is gotten in convo.py and crud_user.py

            if message.sender_id == current_user.id:
                setattr(message, "display_photo", False)
                if (
                    prev_msg
                    and prev_msg.sender_id == message.sender_id
                    and (message.sent_at - prev_msg.sent_at) < timedelta(hours=2)
                ):
                    setattr(
                        message,
                        "sender_name",
                        None,
                    )
                else:
                    setattr(
                        message,
                        "sender_name",
                        f"{current_user.first_name} {current_user.last_name}",
                    )

                    # prev msg display photo
                    if prev_msg:
                        setattr(chat_history[-1], "display_photo", True)

                chat_history.append(message)
            else:
                translation = (
                    (
                        await db.execute(
                            select(models.Translation.translation).filter_by(
                                message_id=message.id, target_user_id=current_user.id
                            )
                        )
                    )
                    .scalars()
                    .first()
                )

                # Case: there are messages sent before a user was added. Don't add anything but not an error
                if translation is None:
                    continue

                setattr(message, "display_photo", False)
                if (
                    prev_msg
                    and prev_msg.sender_id == message.sender_id
                    and (message.sent_at - prev_msg.sent_at) < timedelta(hours=2)
                ):
                    setattr(
                        message,
                        "sender_name",
                        None,
                    )
                else:
                    # grab sender's name
                    sender_user = await crud.user.get(db=db, id=message.sender_id)
                    set_val = "Deleted User"
                    if sender_user is not None:
                        set_val = f"{sender_user.first_name} {sender_user.last_name}"
                    setattr(
                        message,
                        "sender_name",
                        set_val,
                    )

                    if prev_msg:
                        setattr(chat_history[-1], "display_photo", True)

                # temp = jsonable_encoder(message)
                # msg_modified = {**temp, "original_text": translation}

                setattr(message, "original_text", translation)

                chat_history.append(message)

            prev_msg = message

        if prev_msg:
            setattr(chat_history[-1], "display_photo", True)

        return chat_history
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Not used nor up-to-date. Using the Websocket version in Websocket.py
# @router.post(
#     "",
#     response_model=schemas.MessageResponse,
#     status_code=status.HTTP_201_CREATED,
# )
# async def create_message(
#     db: DatabaseDep, request: schemas.MessageCreate, response: Response
# ) -> models.Message:
#     try:
#         # 1) use conversation_id to get all users in the conversation, exclude sender
#         # 2) for each user, grab their desired language
#         # 3) translate original_text to each desired language
#         # 4) Create a corresponding row in the translations table

#         convo = await crud.conversation.get(db=db, id=request.conversation_id)
#         if convo is None:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Convo w/ id {request.conversation_id} doesn't exist",
#             )
#         message = await crud.message.create(db=db, obj_in=request)

#         # TODO: Implement only grabbing the previous X messages in chat
#         chat_history = []
#         for history_msg in await convo.awaitable_attrs.messages:
#             if history_msg.orig_language == request.orig_language:
#                 chat_history.append((request.sender_id, history_msg.original_text))
#             else:
#                 # if the message isn't in the language of the sender, then see if there's a translation for it
#                 for tls in await history_msg.awaitable_attrs.translations:
#                     if tls.language == request.orig_language:
#                         chat_history.append((history_msg.sender_id, tls.translation))

#         (await convo.awaitable_attrs.messages).append(message)
#         await db.flush()

#         for member in await convo.awaitable_attrs.members:
#             if member.id != request.sender_id:
#                 text = await translation.gpt.translate(
#                     sender_id=request.sender_id,
#                     target_language=member.target_language,
#                     text_input=request.original_text,
#                     chat_history=chat_history,
#                 )

#                 if text is None:
#                     await db.rollback()
#                     raise HTTPException(
#                         status_code=status.HTTP_400_BAD_REQUEST,
#                         detail=f"translation of {request.original_text} to {member.target_language} for target user {member.id} could not be generated",
#                     )

#                 # create the translation row
#                 new_translation = await crud.translation.create(
#                     db=db,
#                     obj_in=schemas.TranslationCreate(
#                         translation=text,
#                         language=member.target_language,
#                         target_user_id=member.id,
#                         message_id=message.id,
#                         is_read=0,
#                     ),
#                 )
#                 (await message.awaitable_attrs.translations).append(new_translation)
#             else:
#                 # just add the same message as a translation
#                 new_translation = await crud.translation.create(
#                     db=db,
#                     obj_in=schemas.TranslationCreate(
#                         translation=request.original_text,
#                         language=member.target_language,
#                         target_user_id=member.id,
#                         message_id=message.id,
#                         is_read=1,
#                     ),
#                 )
#                 (await message.awaitable_attrs.translations).append(new_translation)

#         await db.commit()
#         response.headers["Location"] = (
#             f"/messages/{message.conversation_id}/{message.sender_id}"
#         )
#         return message
#     except IntegrityError as e:
#         await db.rollback()
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# TODO: a method to update received_at attribute of a Message
