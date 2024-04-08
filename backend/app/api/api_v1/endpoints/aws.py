import boto3
import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Annotated
from botocore.exceptions import ClientError, TokenRetrievalError, NoCredentialsError
from redis.asyncio import Redis

from app import models, schemas, crud
from app.api.dependencies import verify_current_user_w_cookie, DatabaseDep
from app.utils.aws import (
    generate_presigned_get_url,
    get_cached_presigned_obj,
    CacheMethod,
)
from app.core.config import settings

router = APIRouter()


@router.post(
    "/s3/generate-presigned-post/{group}",
    response_model=schemas.S3PreSignedURLPOSTResponse,
)
async def generate_presigned_post(
    db: DatabaseDep,
    current_user: Annotated[models.User, Depends(verify_current_user_w_cookie)],
    request: schemas.S3PreSignedURLPOSTRequest,
    group: bool,
    req: Request,
) -> dict[str, dict[str, str]]:
    """Generate a pre-signed URL for file uploads."""

    redis_client: Redis = req.app.state.redis_client

    if group:
        if not request.convo_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing conversation id",
            )
        if not await crud.conversation.is_user_in_conversation(
            db=db, user_id=current_user.id, conversation_id=request.convo_id
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not authorized to this chat",
            )
        pic_key = f"chat/{request.convo_id}/{request.filename}"
    else:
        pic_key = f"user/{current_user.id}/{request.filename}"

    cache_key, cached_post_response = await get_cached_presigned_obj(
        object_key=pic_key, redis_client=redis_client, method=CacheMethod.POST
    )

    if cached_post_response:
        # necessary bc FastAPI expects return values to not be serialized to JSON string
        # so they can check the correct response models and we won't have double
        # serialization issues
        return json.loads(cached_post_response)  # type: ignore

    session = boto3.Session()
    s3_client = session.client("s3")

    try:
        if group:
            # group chats
            response = s3_client.generate_presigned_post(
                Bucket=settings.S3_BUCKET_NAME,
                Key=pic_key,
                Fields={
                    "Content-Type": "image/jpeg",
                    "x-amz-meta-about": f"{request.about}",
                },
                Conditions=[
                    [
                        "content-length-range",
                        1000,
                        5242880,
                    ],  # Optional: File size between 1000 Bytes - 5 MB
                    {"Content-Type": "image/jpeg"},
                    ["starts-with", "$x-amz-meta-about", ""],
                ],
                ExpiresIn=settings.S3_PRESIGNED_URL_POST_EXPIRE_SECS,  # URL expires in 1 hour
            )
        else:
            # users
            response = s3_client.generate_presigned_post(
                Bucket=settings.S3_BUCKET_NAME,
                Key=pic_key,
                Fields={
                    "Content-Type": "image/jpeg",
                    "x-amz-meta-user": f"{current_user.first_name} {current_user.last_name}",
                    "x-amz-meta-about": f"{request.about}",
                },
                Conditions=[
                    [
                        "content-length-range",
                        1000,
                        5242880,
                    ],  # Optional: File size between 1000 Bytes - 5 MB
                    {"Content-Type": "image/jpeg"},
                    ["starts-with", "$x-amz-meta-user", ""],
                    ["starts-with", "$x-amz-meta-about", ""],
                ],
                ExpiresIn=settings.S3_PRESIGNED_URL_POST_EXPIRE_SECS,  # URL expires in 1 hour
            )

        # must serialize dictionary to JSON string bc dict can't be value in redis cache
        response_json = json.dumps(response)
        await redis_client.set(
            cache_key,
            response_json,
            ex=(settings.S3_PRESIGNED_URL_POST_EXPIRE_SECS - 2),
        )

        return response  # type: ignore
    except TokenRetrievalError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except NoCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except ClientError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/s3/generate-presigned-get")
async def generate_presigned_get(
    _unused_user: Annotated[models.User, Depends(verify_current_user_w_cookie)],
    db: DatabaseDep,
    request: schemas.S3PreSignedURLGETRequest,
    req: Request,
) -> dict[int, str]:

    # Note: return value should never be an empty dictionary bc this endpoint should
    # only be called from the frontend when the user or convo has an associated
    # object key stored in DB

    redis_client: Redis = req.app.state.redis_client

    try:
        if request.user_ids:
            # {"user_id": "profile_photo"}
            result = await crud.user.get_user_profiles(db=db, user_ids=request.user_ids)
        elif request.convo_id:
            convo = await crud.conversation.get(db=db, id=request.convo_id)
            if convo is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation {request.convo_id} not found",
                )

            result = {}
            if convo.conversation_photo:
                # {"convo_id": "convo_photo"}
                result[convo.id] = convo.conversation_photo
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request",
            )

        for id in result:
            _, cached_url = await get_cached_presigned_obj(
                object_key=result[id],
                redis_client=redis_client,
                method=CacheMethod.GET,
            )

            if cached_url:
                url = cached_url
            else:
                url = await generate_presigned_get_url(
                    bucket_name=settings.S3_BUCKET_NAME,
                    object_key=result[id],
                    expire_in_secs=settings.S3_PRESIGNED_URL_GET_EXPIRE_SECS,
                    redis_client=redis_client,
                )

            result[id] = url

        # {"user_id": "presigned_URL"} or {"convo_id": "presigned_URL"}
        return result
    except TokenRetrievalError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except NoCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except ClientError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
