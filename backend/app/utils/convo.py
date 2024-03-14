from redis.asyncio import Redis

from app.models import Conversation
from app.core.config import settings
from app.utils.aws import (
    generate_presigned_get_url,
    get_cached_presigned_obj,
    CacheMethod,
)


async def convo_name_url_processing(
    convo: Conversation, curr_user_id: int, redis_client: Redis
) -> None:
    presigned_url = None

    if not convo.is_group_chat:
        # guaranteed to have only 2 members
        for member in await convo.awaitable_attrs.members:
            if member.id != curr_user_id:
                other_user = member

        setattr(
            convo,
            "conversation_name",
            f"{other_user.first_name} {other_user.last_name}",  # type: ignore
        )

        obj_key = other_user.profile_photo  # type: ignore
        if obj_key:
            _, presigned_url = await get_cached_presigned_obj(
                object_key=obj_key,
                redis_client=redis_client,
                method=CacheMethod.GET,
            )

            if not presigned_url:
                presigned_url = await generate_presigned_get_url(
                    bucket_name="translation-messaging-bucket",
                    object_key=obj_key,
                    expire_in_secs=settings.S3_PRESIGNED_URL_GET_EXPIRE_SECS,
                    redis_client=redis_client,
                )
    elif convo.conversation_photo:
        obj_key = convo.conversation_photo

        _, presigned_url = await get_cached_presigned_obj(
            object_key=obj_key,
            redis_client=redis_client,
            method=CacheMethod.GET,
        )

        if not presigned_url:
            presigned_url = await generate_presigned_get_url(
                bucket_name="translation-messaging-bucket",
                object_key=obj_key,
                expire_in_secs=settings.S3_PRESIGNED_URL_GET_EXPIRE_SECS,
                redis_client=redis_client,
            )

    setattr(
        convo,
        "presigned_url",
        presigned_url,
    )
