import json
from fastapi import APIRouter, HTTPException, Request, status, Response
from sqlalchemy.exc import IntegrityError
from redis.asyncio import Redis

from app import crud, models, schemas
from app.api.dependencies import DatabaseDep

router = APIRouter()


# Conversation
## User needs to be able to find people to send messages to and receive friend requests
## User needs to be able to start a conversation with someone or receive a join invitation from someone
## User needs to be able to leave a groupchat - done


@router.get("/{conversation_id}", response_model=schemas.ConversationResponse)
async def get_convo(db: DatabaseDep, conversation_id: int) -> models.Conversation:
    convo = await crud.conversation.get(db=db, id=conversation_id)
    if convo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Convo w/ id {conversation_id} doesn't exist",
        )
    return convo


# TODO: How do we identify a conversation that already exists?
@router.post(
    "",
    response_model=schemas.ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_convo(
    db: DatabaseDep,
    request: schemas.ConversationCreate,
    response: Response,
    req: Request,
) -> models.Conversation:
    try:
        new_convo = await crud.conversation.create(
            db=db,
            obj_in=schemas.ConversationCreateDB(
                conversation_name=request.conversation_name
            ),
        )
        await db.flush()

        members = await new_convo.awaitable_attrs.members
        user_emails: set[str] = set()
        redis_client: Redis = req.app.state.redis_client
        for email in request.user_ids:
            if email not in user_emails:
                user_emails.add(email)
                user = await crud.user.get_by_email(db=db, email=email)
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"User w/ email {email} doesn't exist",
                    )
                members.append(user)
                # let others know a new channel is being created so they subscribe to it
                await redis_client.publish(
                    f"{user.id}", json.dumps({"convo_id": new_convo.id})
                )
        # note this needs to be here for the group_member table to update
        await db.commit()

        response.headers["Location"] = f"/conversations/{new_convo.id}"
        return new_convo
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{convo_id}/update-name",
)
async def update_convo_name(
    db: DatabaseDep,
    convo_id: int,
    request: schemas.ConversationNameUpdate,
) -> None:
    convo = await crud.conversation.get(db=db, id=convo_id)
    if convo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation w/ id {convo_id} doesn't exist",
        )
    try:
        res = await crud.conversation.update(db=db, db_obj=convo, obj_in=request)
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{convo_id}/update-members",
    response_model=schemas.ConversationResponse,
)
async def update_convo_users(
    db: DatabaseDep,
    convo_id: int,
    request: schemas.ConversationMemberUpdate,
) -> models.Conversation:
    users: set[models.User] = set()
    for user_email in request.user_ids:
        user = await crud.user.get_by_email(db=db, email=user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User w/ email {user_email} doesn't exist",
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


# @router.patch("/{convo_id}/update-message")
# async def update_convo_latest_msg(
#     db: DatabaseDep, convo_id: int, request: schemas.ConversationMessageUpdate
# ) -> None:
#     try:
#         rows_updated = await crud.conversation.update_latest_msg(
#             db=db, convo_id=convo_id, new_latest_msg_id=request.new_latest_msg_id
#         )

#         if rows_updated == 0:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Conversation w/ id {convo_id} doesn't exist",
#             )
#         await db.commit()
#     except IntegrityError as e:
#         await db.rollback()
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{convo_id}",
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
