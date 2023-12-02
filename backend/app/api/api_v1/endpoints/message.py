from fastapi import APIRouter, HTTPException, status, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import crud, models, schemas, translation
from app.api.dependencies import DatabaseDep

router = APIRouter()


# Messages


# this is getting messages to display in the UI, so we know who's messages are who's
@router.get("/{conversation_id}/{user_id}")
async def get_messages_sent(
    db: DatabaseDep, conversation_id: int, user_id: int
) -> dict[str, list[str]]:
    chat_history = []
    convo = await crud.conversation.get(db=db, id=conversation_id)
    if convo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Convo w/ id {conversation_id} doesn't exist",
        )

    # this is getting the chat history in the sender's language. Either there is a chat history
    # in their language, or their isn't bc the sender changed their set langauge
    for message in await convo.awaitable_attrs.messages:
        if message.sender_id == user_id:
            chat_history.append(message.original_text)
        else:
            translation = (
                (
                    await db.execute(
                        select(models.Translation.translation).filter_by(
                            message_id=message.id, target_user_id=user_id
                        )
                    )
                )
                .scalars()
                .first()
            )
            if translation is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"translation w/ message id {message.id} and target user id {user_id} could not be found",
                )
            chat_history.append(translation)

    return {"history": chat_history}


# TODO: I might need to append the user id to each message so I can use that in the front end to display the message left or right
@router.post(
    "",
    response_model=schemas.MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    db: DatabaseDep, request: schemas.MessageCreate, response: Response
) -> models.Message:
    try:
        # 1) use conversation_id to get all users in the conversation, exclude sender
        # 2) for each user, grab their desired language
        # 3) translate original_text to each desired language
        # 4) Create a corresponding row in the translations table

        message = await crud.message.create(db=db, obj_in=request)
        convo = await crud.conversation.get(db=db, id=request.conversation_id)
        if convo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Convo w/ id {request.conversation_id} doesn't exist",
            )

        # TODO: Implement only grabbing the previous X messages in chat
        chat_history = []
        for history_msg in await convo.awaitable_attrs.messages:
            if history_msg.orig_language == request.orig_language:
                chat_history.append((request.sender_id, history_msg.original_text))
            else:
                # if the message isn't in the language of the sender, then see if there's a translation for it
                for tls in await history_msg.awaitable_attrs.translations:
                    if tls.language == request.orig_language:
                        chat_history.append((history_msg.sender_id, tls.translation))

        (await convo.awaitable_attrs.messages).append(message)
        await db.flush()

        for member in await convo.awaitable_attrs.members:
            if member.id != request.sender_id:
                text = await translation.gpt.translate(
                    sender_id=request.sender_id,
                    target_language=member.target_language,
                    text_input=request.original_text,
                    chat_history=chat_history,
                )

                if text is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"translation of {request.original_text} to {member.target_language} for target user {member.id} could not be generated",
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

        await db.commit()
        response.headers[
            "Location"
        ] = f"/messages/{message.conversation_id}/{message.sender_id}"
        return message
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# TODO: a method to update received_at attribute of a Message
