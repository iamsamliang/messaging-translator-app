import asyncio
import json

from typing import Annotated, Sequence
from app.crud import crud_association
from app.utils.convo import (
    convo_latest_msg_processing,
    convo_name_url_processing,
    generate_convo_identifier,
)
from fastapi import APIRouter, HTTPException, Request, status, Response, Depends
from sqlalchemy.exc import IntegrityError
from redis.asyncio import Redis
from botocore.exceptions import ClientError, TokenRetrievalError, NoCredentialsError

from app import crud, models, schemas
from app.api.dependencies import DatabaseDep, verify_current_user_w_cookie
from app.utils.aws import (
    generate_presigned_get_url,
    get_cached_presigned_obj,
    CacheMethod,
)
from app.core.config import settings

router = APIRouter()


# Conversation
## User needs to be able to find people to send messages to and receive friend requests
## User needs to be able to start a conversation with someone or receive a join invitation from someone
## User needs to be able to leave a groupchat - done


@router.get("/{conversation_id}", response_model=schemas.ConversationResponse)
async def get_convo(
    db: DatabaseDep,
    conversation_id: int,
    current_user: Annotated[models.User, Depends(verify_current_user_w_cookie)],
    get_latest_msg: bool,
    request: Request,
) -> models.Conversation:
    convo = await crud.conversation.get(db=db, id=conversation_id)

    if convo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Convo w/ id {conversation_id} doesn't exist",
        )

    if get_latest_msg and convo.latest_message_id:
        convo_latest_msg = await crud.message.get(db=db, id=convo.latest_message_id)

        await convo_latest_msg_processing(
            db=db,
            convo=convo,
            curr_user_id=current_user.id,
            convo_latest_msg=convo_latest_msg,  # type: ignore
        )

    redis_client: Redis = request.app.state.redis_client

    await convo_name_url_processing(
        convo=convo, curr_user_id=current_user.id, redis_client=redis_client
    )

    return convo


@router.get("", response_model=list[schemas.ConversationResponse])
async def get_convos(
    db: DatabaseDep,
    current_user: Annotated[models.User, Depends(verify_current_user_w_cookie)],
    offset: int,
    limit: int,
    request: Request,
) -> Sequence[models.Conversation]:
    convos = await crud.conversation.get_user_convos(
        db=db, user_id=current_user.id, offset=offset, limit=limit
    )

    redis_client: Redis = request.app.state.redis_client

    for convo in convos:
        if convo.latest_message_id:
            convo_latest_msg = await crud.message.get(db=db, id=convo.latest_message_id)

            await convo_latest_msg_processing(
                db=db,
                convo=convo,
                curr_user_id=current_user.id,
                convo_latest_msg=convo_latest_msg,  # type: ignore
            )

        await convo_name_url_processing(
            convo=convo, curr_user_id=current_user.id, redis_client=redis_client
        )

    return convos


@router.get("/{conversation_id}/members", response_model=schemas.GetMembersResponse)
async def get_members(
    db: DatabaseDep,
    conversation_id: int,
    _unused_user: Annotated[models.User, Depends(verify_current_user_w_cookie)],
    request: Request,
) -> dict[str, dict[int, models.User] | list[int] | bool | str | None]:
    convo = await crud.conversation.get(db=db, id=conversation_id)
    if convo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Convo w/ id {conversation_id} doesn't exist",
        )

    members = await crud.conversation.get_members(
        db=db, conversation_id=conversation_id
    )
    redis_client: Redis = request.app.state.redis_client

    sorted_member_ids = []
    members_dict = {}

    try:
        gc_url = None

        if convo.conversation_photo:
            _, gc_url = await get_cached_presigned_obj(
                object_key=convo.conversation_photo,
                redis_client=redis_client,
                method=CacheMethod.GET,
            )

            if not gc_url:
                gc_url = await generate_presigned_get_url(
                    bucket_name=settings.S3_BUCKET_NAME,
                    object_key=convo.conversation_photo,
                    expire_in_secs=settings.S3_PRESIGNED_URL_GET_EXPIRE_SECS,
                    redis_client=redis_client,
                )

        for member in sorted(
            members, key=lambda user: (user.first_name, user.last_name)
        ):
            url = None

            if member.profile_photo:
                _, url = await get_cached_presigned_obj(
                    object_key=member.profile_photo,
                    redis_client=redis_client,
                    method=CacheMethod.GET,
                )

                if not url:
                    url = await generate_presigned_get_url(
                        bucket_name=settings.S3_BUCKET_NAME,
                        object_key=member.profile_photo,
                        expire_in_secs=settings.S3_PRESIGNED_URL_GET_EXPIRE_SECS,
                        redis_client=redis_client,
                    )

            setattr(
                member,
                "presigned_url",
                url,
            )

            sorted_member_ids.append(member.id)
            members_dict[member.id] = member

        return {
            "members": members_dict,
            "sorted_member_ids": sorted_member_ids,
            "gc_url": gc_url,
        }
    except TokenRetrievalError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except NoCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except ClientError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# TODO: How do we identify a conversation that already exists?
@router.post(
    "/create",
    response_model=schemas.ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_convo(
    db: DatabaseDep,
    request: schemas.ConversationCreate,
    response: Response,
    req: Request,
    curr_user: Annotated[models.User, Depends(verify_current_user_w_cookie)],
) -> models.Conversation:
    try:
        user_emails: set[str] = set()
        user_ids: list[int] = []

        for email in request.user_ids:
            if email not in user_emails:
                user_emails.add(email)
                user = await crud.user.get_by_email(db=db, email=email)
                if not user:
                    # await db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"User w/ email {email} doesn't exist",
                    )
                user_ids.append(user.id)

        convo_identifier = generate_convo_identifier(user_ids=user_ids)

        # if convo_identifier already exists in convo table, return convo
        existing_convo = await crud.conversation.get_convo_by_identifier(
            db=db, convo_identifier=convo_identifier
        )
        redis_client: Redis = req.app.state.redis_client
        if existing_convo:
            await convo_name_url_processing(
                convo=existing_convo,
                curr_user_id=curr_user.id,
                redis_client=redis_client,
            )
            return existing_convo

        # create a new convo
        new_convo = await crud.conversation.create(
            db=db,
            obj_in=schemas.ConversationCreateDB(
                conversation_name=request.conversation_name,
                is_group_chat=request.is_group_chat,
                chat_identifier=convo_identifier,
            ),
        )
        await db.flush()

        member_associations = []
        pub_messages = []

        for user_id in user_ids:
            member_associations.append(
                {"user_id": user_id, "conversation_id": new_convo.id}
            )
            pub_messages.append(
                (
                    f"{user_id}",
                    json.dumps({"type": "create_convo", "convo_id": new_convo.id}),
                )
            )

        await crud_association.associate_users_to_convo(
            db=db, member_associations=member_associations
        )

        await asyncio.gather(
            *(
                redis_client.publish(channel, message)
                for channel, message in pub_messages
            )
        )

        # for user in users:
        #     members.append(user)
        #     # let others know a new channel is being created so they subscribe to it
        #     await redis_client.publish(
        #         f"{user.id}",
        #         json.dumps({"type": "create_convo", "convo_id": new_convo.id}),
        #     )

        # note this needs to be here for the group_member table to update
        await db.commit()

        response.headers["Location"] = f"/conversations/{new_convo.id}"

        await convo_name_url_processing(
            convo=new_convo, curr_user_id=curr_user.id, redis_client=redis_client
        )

        return new_convo
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{convo_id}/update",
)
async def update_convo(
    db: DatabaseDep,
    convo_id: int,
    request: schemas.ConversationUpdate,
    req: Request,
    _unused_user: Annotated[models.User, Depends(verify_current_user_w_cookie)],
) -> None:
    convo = await crud.conversation.get(db=db, id=convo_id)
    if convo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation w/ id {convo_id} doesn't exist",
        )

    try:
        res = await crud.conversation.update(db=db, db_obj=convo, obj_in=request)

        redis_client: Redis = req.app.state.redis_client
        # signal to all users in convo that the convo name or photo is updated
        if request.conversation_name:
            json_data = {
                "type": "update_convo_name",
                "data": {
                    "convo_id": convo_id,
                    "new_name": res.conversation_name,
                },
            }
        elif request.conversation_photo:
            presigned_url = await generate_presigned_get_url(
                bucket_name=settings.S3_BUCKET_NAME,
                object_key=request.conversation_photo,
                expire_in_secs=settings.S3_PRESIGNED_URL_GET_EXPIRE_SECS,
                redis_client=redis_client,
            )
            json_data = {
                "type": "update_convo_photo",
                "data": {
                    "convo_id": convo_id,
                    "url": presigned_url,
                },
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request",
            )

        # for user_in_convo in users_in_convo:
        #     if user_in_convo.id != current_user.id:
        #         await redis_client.publish(
        #             f"{user_in_convo.id}",
        #             json.dumps(json_data),
        #         )

        await redis_client.publish(f"chat_{convo_id}", json.dumps(json_data))

        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{convo_id}/update-members",
)
async def update_convo_users(
    db: DatabaseDep,
    convo_id: int,
    request: schemas.ConversationMemberUpdate,
    req: Request,
    _unused_user: Annotated[models.User, Depends(verify_current_user_w_cookie)],
) -> None:
    user_emails: set[str] = set()
    users: list[models.User] = []

    if request.method == schemas.conversation.Method.ADD:
        for user_email in request.user_ids:
            if user_email not in user_emails:
                user = await crud.user.get_by_email(db=db, email=user_email)
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"User w/ email {user_email} doesn't exist",
                    )
                user_emails.add(user_email)

                if not (
                    await crud.conversation.is_user_in_conversation(
                        db=db, user_id=user.id, conversation_id=convo_id
                    )
                ):
                    users.append(user)
    # can only delete one user at a time
    else:
        user_email = request.user_ids[0]
        user = await crud.user.get_by_email(db=db, email=user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User w/ email {user_email} doesn't exist",
            )

        if await crud.conversation.is_user_in_conversation(
            db=db, user_id=user.id, conversation_id=convo_id
        ):
            users.append(user)

    try:
        if users:
            redis_client: Redis = req.app.state.redis_client
            res = await crud.conversation.update_users(
                db=db,
                convo_id=convo_id,
                users=users,
                method=request.method,
                redis=redis_client,
                sorted_curr_ids=request.sorted_ids,
            )
            if not res:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation {convo_id} (ID) doesn't exist",
                )
            # await db.commit()

            # convo_members = await res.awaitable_attrs.members

            # if request.method == schemas.conversation.Method.ADD:
            #     members_dict = {}
            #     sorted_curr_ids = request.sorted_ids
            #     if sorted_curr_ids is None:
            #         raise HTTPException(
            #             status_code=status.HTTP_400_BAD_REQUEST,
            #             detail=f"Missing sorted user IDs",
            #         )

            #     for added_user in users:
            #         sorted_curr_ids.append(added_user.id)

            #         url = None

            #         if added_user.profile_photo:
            #             _, url = await get_cached_presigned_obj(
            #                 object_key=added_user.profile_photo,
            #                 redis_client=redis_client,
            #                 method=CacheMethod.GET,
            #             )

            #             if not url:
            #                 url = await generate_presigned_get_url(
            #                     bucket_name=settings.S3_BUCKET_NAME,
            #                     object_key=added_user.profile_photo,
            #                     expire_in_secs=settings.S3_PRESIGNED_URL_GET_EXPIRE_SECS,
            #                     redis_client=redis_client,
            #                 )

            #         setattr(
            #             added_user,
            #             "presigned_url",
            #             url,
            #         )

            #         members_dict[added_user.id] = added_user

            #     await db.commit()

            #     return {
            #         "members": members_dict,
            #         "sorted_member_ids": sorted_curr_ids,
            #     }

            await db.commit()

        return None

    except TokenRetrievalError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except NoCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except ClientError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{convo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_convo(
    db: DatabaseDep,
    convo_id: int,
    _: Annotated[models.User, Depends(verify_current_user_w_cookie)],
) -> None:
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
