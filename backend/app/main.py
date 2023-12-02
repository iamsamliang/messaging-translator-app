# main.py
from typing import Annotated
from datetime import timedelta

from fastapi import FastAPI, Depends, Response, status
from sqlalchemy import select
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app import crud, schemas, models, translation
from app.core import security
from app.core.config import settings
from .dependencies import get_db, verify_current_user
from .exceptions import UserAlreadyExistsException
from .handlers import user_already_exists_exception_handler

app = FastAPI()
app.add_exception_handler(
    UserAlreadyExistsException, user_already_exists_exception_handler
)

# Shared Annotated Dependencies
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


# Users
@app.get("/users/me", response_model=schemas.UserOut)
async def get_me(
    current_user: Annotated[models.User, Depends(verify_current_user)]
) -> models.User:
    return current_user


@app.post("/users", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    db: DatabaseDep,
    user_in: schemas.UserCreate,
    response: Response,
) -> models.User:
    try:
        user = await crud.user.create(db=db, obj_in=user_in)
        await db.commit()
        response.headers["Location"] = f"/users/{user.id}"
        return user
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserAlreadyExistsException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )


@app.patch("/users/{user_id}", response_model=schemas.UserOut)
async def update_user(
    db: DatabaseDep,
    user_id: int,
    request: schemas.UserUpdate,
) -> models.User:
    try:
        curr_user = await crud.user.get(db=db, id=user_id)
        if curr_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User w/ id {user_id} doesn't exist",
            )
        res = await crud.user.update(db=db, db_obj=curr_user, obj_in=request)

        await db.commit()
        return res
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(db: DatabaseDep, user_id: int) -> None:
    try:
        res = await crud.user.delete(db=db, id=user_id)
        if res is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User w/ id {user_id} doesn't exist",
            )
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Login
@app.post("/login/access-token", response_model=schemas.TokenOut)
async def login_for_token(
    db: DatabaseDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> dict[str, str]:
    login_user = await crud.user.get_by_email(db, form_data.username)
    if not login_user or not security.verify_password(
        form_data.password, login_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": f"email:{form_data.username}"}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# Conversation
## User needs to be able to find people to send messages to and receive friend requests

## User needs to be able to start a conversation with someone or receive a join invitation from someone


## User needs to be able to leave a groupchat - done
@app.get(
    "/conversations/{conversation_id}", response_model=schemas.ConversationResponse
)
async def get_convo(db: DatabaseDep, conversation_id: int) -> models.Conversation:
    convo = await crud.conversation.get(db=db, id=conversation_id)
    if convo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Convo w/ id {conversation_id} doesn't exist",
        )
    return convo


# TODO: How do we identify a conversation that already exists?
@app.post(
    "/conversations",
    response_model=schemas.ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_convo(
    db: DatabaseDep, request: schemas.ConversationCreate, response: Response
) -> models.Conversation:
    try:
        new_convo = await crud.conversation.create(
            db=db,
            obj_in=schemas.ConversationCreateDB(
                conversation_name=request.conversation_name
            ),
        )
        members = await new_convo.awaitable_attrs.members
        user_emails: set[str] = set()
        for user_id in request.user_ids:
            email = user_id.email
            if email not in user_emails:
                user_emails.add(email)
                user = await crud.user.get_by_email(db=db, email=email)
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"User w/ email {user_id.email} doesn't exist",
                    )
                members.append(user)
        # note this needs to be here for the group_member table to update
        await db.commit()
        response.headers["Location"] = f"/conversations/{new_convo.id}"
        return new_convo
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.patch(
    "/conversations/{convo_id}/update-name",
    response_model=schemas.ConversationResponse,
)
async def update_convo_name(
    db: DatabaseDep,
    convo_id: int,
    request: schemas.ConversationNameUpdate,
) -> models.Conversation:
    convo = await crud.conversation.get(db=db, id=convo_id)
    if convo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation w/ id {convo_id} doesn't exist",
        )
    try:
        res = await crud.conversation.update(db=db, db_obj=convo, obj_in=request)
        await db.commit()
        return res
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.patch(
    "/conversations/{convo_id}/update-members",
    response_model=schemas.ConversationResponse,
)
async def update_convo_users(
    db: DatabaseDep,
    convo_id: int,
    request: schemas.ConversationMemberUpdate,
) -> models.Conversation:
    users: set[models.User] = set()
    for user_id in request.user_ids:
        user = await crud.user.get_by_email(db=db, email=user_id.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User w/ email {user_id.email} doesn't exist",
            )
        users.add(user)
    try:
        res = await crud.conversation.update_users(
            db=db, convo_id=convo_id, users=users, method=request.method
        )
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation w/ id {convo_id} doesn't exist",
            )
        await db.commit()
        return res
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.delete(
    "/conversations/{convo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_convo(db: DatabaseDep, convo_id: int) -> None:
    try:
        res = await crud.conversation.delete(db=db, id=convo_id)
        if res is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation w/ id {convo_id} doesn't exist",
            )
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Messages


# this is getting messages to display in the UI, so we know who's messages are who's
@app.get("/messages/{conversation_id}/{user_id}")
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


@app.post(
    "/messages",
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
