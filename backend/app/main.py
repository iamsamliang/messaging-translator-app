# main.py
from typing import Annotated
from datetime import timedelta

from fastapi import FastAPI, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app import crud, schemas, models
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
        await db.refresh()
        return user
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserAlreadyExistsException:
        raise HTTPException(status_code=400, detail="Email already registered")


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
@app.post("/conversations", response_model=schemas.ConversationOut)
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
        await db.refresh()  # Refresh so new_convo contains its ID as well
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
    res = await crud.conversation.update(db=db, db_obj=convo, obj_in=request)
    await db.commit()
    await db.refresh()
    return res


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
        await db.refresh()
        return res
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


## User needs to be able to create messages, read messages, (no update or delete, at least no delete internally)


## User needs to be able to find people to send messages to and receive friend requests

## User needs to be able to start a conversation with someone or receive a join invitation from someone
## How do we identify a conversation that already exists?

## User needs to be able to leave a groupchat - done

## App needs to translate incoming/outgoing messages to the target user's desired language
## For translation, we want to feed context back to the model. But given a user, we want to feed the
## context in his language.
## So: userA -> inputA in lang A -> prefix w/ chat history in lang A -> In english, ask to translate inputA (stil in lang A) to lang B
## However, has been noted (7 months ago) that the instructions also in lang A would product better results
