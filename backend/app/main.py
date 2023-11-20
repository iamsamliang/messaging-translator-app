# main.py
from typing import Annotated
from datetime import timedelta

from fastapi import FastAPI, Depends, status
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app import crud, schemas, models, translation
from app.core import security
from app.core.config import settings
from .dependencies import get_db, get_current_user
from .exceptions import *
from .handlers import *

app = FastAPI()
app.add_exception_handler(
    UserAlreadyExistsException, user_already_exists_exception_handler
)
app.add_exception_handler(UserDoesNotExistException, user_does_not_exists_handler)


# Users
@app.get("/users/me", response_model=schemas.UserOut)
async def get_me(
    current_user: Annotated[models.User, Depends(get_current_user)]
) -> models.User:
    return current_user


@app.post("/users", response_model=schemas.UserOut)
async def create_user(
    db: Annotated[AsyncSession, Depends(get_db)], user_in: schemas.UserCreate
) -> models.User:
    try:
        user = await crud.user.create(db=db, obj_in=user_in)
        await db.commit()
        await db.refresh(user)
        return user
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserAlreadyExistsException:
        raise HTTPException(status_code=400, detail="Email already registered")


@app.patch("/users/{user_id}", response_model=schemas.UserOut)
async def update_user(
    db: Annotated[AsyncSession, Depends(get_db)],
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
        await db.refresh(res)
        return res
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.delete("/users/{user_id}", response_model=schemas.UserOut)
async def delete_user(db: Annotated[AsyncSession, Depends(get_db)], user_id: int):
    try:
        res = await crud.user.delete(db=db, id=user_id)
        if res is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User w/ id {user_id} doesn't exist",
            )
        await db.commit()
        return res
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Login
@app.post("/login/access-token", response_model=schemas.TokenOut)
async def login_for_token(
    db: Annotated[AsyncSession, Depends(get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> JSONResponse:
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
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# Conversation
## User needs to be able to find people to send messages to and receive friend requests

## User needs to be able to start a conversation with someone or receive a join invitation from someone


## User needs to be able to leave a groupchat - done
@app.get(
    "/conversations/{conversation_id}", response_model=schemas.ConversationResponse
)
async def get_convo(
    db: Annotated[AsyncSession, Depends(get_db)], conversation_id: int
) -> models.Conversation:
    convo = await crud.conversation.get(db=db, id=conversation_id)
    return convo


## How do we identify a conversation that already exists?
@app.post("/conversations", response_model=schemas.ConversationResponse)
async def create_convo(
    db: Annotated[AsyncSession, Depends(get_db)], request: schemas.ConversationCreate
) -> models.Conversation:
    users: set[models.User] = set()
    names = []
    for user_id in request.user_ids:
        user: models.User = await crud.user.get_by_email(db=db, email=user_id["email"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User w/ email {user_id['email']} doesn't exist",
            )
        names.append(user.first_name)
        users.add(user)

    name = request["conversation_name"]
    if not name:
        name = ", ".join(names)

    try:
        new_convo = await crud.conversation.create(
            db=db,
            convo=schemas.ConversationCreateDB(
                conversation_name=name, members=list(users)
            ),
        )
        await db.commit()  # For ACID compliancy w/ transactions (multiple CRUD ops per endpoint)
        await db.refresh(new_convo)  # Refresh so new_convo contains its ID as well
        return new_convo
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.patch(
    "/conversations/{convo_id}/update-name",
    response_model=schemas.ConversationResponse,
)
async def update_convo_name(
    db: Annotated[AsyncSession, Depends(get_db)],
    convo_id: int,
    request: schemas.ConversationNameUpdate,
):
    convo = await crud.conversation.get(db=db, id=convo_id)
    if convo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation w/ id {convo_id} doesn't exist",
        )
    try:
        res = await crud.conversation.update(db=db, db_obj=convo, obj_in=request)
        await db.commit()
        await db.refresh(res)
        return res
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.patch(
    "/conversations/{convo_id}/update-members",
    response_model=schemas.ConversationResponse,
)
async def update_convo_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    convo_id: int,
    request: schemas.ConversationMemberUpdate,
) -> models.Conversation:
    users: set[models.User] = set()
    for user_id in request.user_ids:
        user: models.User = await crud.user.get_by_email(db=db, email=user_id["email"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User w/ email {user_id['email']} doesn't exist",
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
        await db.refresh(res)
        return res
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.delete("/conversation/{convo_id}", response_model=schemas.ConversationResponse)
async def delete_convo(db: Annotated[AsyncSession, Depends(get_db)], convo_id: int):
    try:
        res = await crud.conversation.delete(db=db, id=convo_id)
        if res is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation w/ id {convo_id} doesn't exist",
            )
        await db.commit()
        return res
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Messages
## User needs to be able to create messages, get their messages (no update or delete, at least no delete internally)
@app.get("/messages/{conversation_id}/{user_id}")
async def get_messages(
    db: Annotated[AsyncSession, Depends(get_db)], conversation_id: int, user_id: int
):
    chat_history = []
    convo = await crud.conversation.get(db=db, id=conversation_id)

    for message in convo.messages:
        if message.sender_id == user_id:
            chat_history.append(message.original_text)
        else:
            translation = await db.execute(
                select(models.Translation.translation).filter_by(
                    message_id=message.id, target_user_id=user_id
                )
            )
            chat_history.append(translation)

    return {"history": chat_history}


@app.post("/messages", response_model=schemas.MessageResponse)
async def create_message(
    db: Annotated[AsyncSession, Depends(get_db)], request: schemas.MessageCreate
):
    try:
        # 1) use conversation_id to get all users in the conversation, exclude sender
        # 2) for each user, grab their desired language
        # 3) translate original_text to each desired language
        # 4) Create a corresponding row in the translations table

        message = await crud.message.create(db=db, obj_in=request)
        convo = await crud.conversation.get(db=db, id=request.conversation_id)

        chat_history = []
        for message in convo.messages:
            if message.orig_language == request.orig_language:
                chat_history.append((request.sender_id, message.original_text))
            else:
                # if the message isn't in the language of the sender, then see if there's a translation for it
                for tls in message.translations:
                    if tls.language == request.orig_language:
                        chat_history.append((message.sender_id, tls.translation))

        convo.messages.append(message)
        await db.flush()

        for member in convo.members:
            if member.id != request.sender_id:
                text = await translation.gpt.translate(
                    request.sender_id,
                    member.target_language,
                    request.original_text,
                    chat_history,
                )
                # create the translation row

                new_translation = await crud.translation.create(
                    db=db,
                    obj_in=schemas.TranslationCreate(
                        translation=text,
                        language=member.target_language,
                        target_user_id=member.id,
                        message_id=message.id,
                        user=member,
                    ),
                )
                message.translations.append(new_translation)

        await db.commit()
        return message
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# need a method to update received_at attribute of a Message
