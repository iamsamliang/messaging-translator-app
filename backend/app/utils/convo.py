import hashlib

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation, Translation, Message
from app.core.config import settings
from app.utils.aws import (
    generate_presigned_get_url,
    get_cached_presigned_obj,
    CacheMethod,
)


def generate_convo_identifier(user_ids: list[int]) -> str:
    sorted_ids = sorted(user_ids)
    concatenated_ids = "-".join(map(str, sorted_ids))
    hash_object = hashlib.sha256(concatenated_ids.encode())
    return hash_object.hexdigest()


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
                    bucket_name=settings.S3_BUCKET_NAME,
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
                bucket_name=settings.S3_BUCKET_NAME,
                object_key=obj_key,
                expire_in_secs=settings.S3_PRESIGNED_URL_GET_EXPIRE_SECS,
                redis_client=redis_client,
            )

    setattr(
        convo,
        "presigned_url",
        presigned_url,
    )


async def convo_latest_msg_processing(
    db: AsyncSession, convo: Conversation, curr_user_id: int, convo_latest_msg: Message
) -> None:
    translation = (
        await db.execute(
            select(
                Translation.translation,
                Translation.id,
                Translation.is_read,
            ).where(
                Translation.message_id == convo.latest_message_id,
                Translation.target_user_id == curr_user_id,
            )
        )
    ).first()

    if translation:
        setattr(
            convo_latest_msg,
            "relevant_translation",
            translation.translation,
        )
        setattr(
            convo_latest_msg,
            "translation_id",
            translation.id,
        )
        setattr(
            convo_latest_msg,
            "is_read",
            translation.is_read,
        )

    setattr(
        convo,
        "latest_message",
        convo_latest_msg,
    )
