from app.utils.convo import convo_name_url_processing
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from pydantic import EmailStr
from redis.asyncio import Redis

from app import crud

from app.models import User, Conversation, Translation
from app.schemas.user import UserCreate, UserUpdate
from app.exceptions import UserAlreadyExistsException
from app.core import security
from app.core.config import settings
from app.utils.aws import (
    generate_presigned_get_url,
    get_cached_presigned_obj,
    CacheMethod,
)
from .base import CRUDBase


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):

    async def get_w_extra_info(
        self,
        db: AsyncSession,
        user_id: int,
        redis_client: Redis,
    ) -> tuple[User | None, str | None]:
        # optimized
        user = (
            (
                await db.execute(
                    select(User)
                    .where(User.id == user_id)
                    .options(selectinload(User.conversations))
                )
            )
            .scalars()
            .first()
        )

        if not user:
            return None, None

        presigned_url = None

        if user.profile_photo:
            _, presigned_url = await get_cached_presigned_obj(
                object_key=user.profile_photo,
                redis_client=redis_client,
                method=CacheMethod.GET,
            )

            if not presigned_url:
                presigned_url = await generate_presigned_get_url(
                    bucket_name="translation-messaging-bucket",
                    object_key=user.profile_photo,
                    expire_in_secs=settings.S3_PRESIGNED_URL_GET_EXPIRE_SECS,
                    redis_client=redis_client,
                )

        latest_message_ids = [
            conversation.latest_message_id
            for conversation in user.conversations
            if conversation.latest_message_id is not None
        ]

        # Assuming `user.target_language` holds the desired language of the user
        relevant_translations = await db.execute(
            select(
                Translation.message_id,
                Translation.translation,
                Translation.id,
                Translation.is_read,
            ).where(
                Translation.message_id.in_(latest_message_ids),
                Translation.target_user_id == user.id,
            )
        )

        translations = relevant_translations.all()

        translation_map = {
            trans.message_id: (trans.translation, trans.id, trans.is_read)
            for trans in translations
        }

        for conversation in user.conversations:
            if conversation.latest_message_id:
                val = translation_map.get(conversation.latest_message_id)
                convo_latest_msg = await crud.message.get(
                    db=db, id=conversation.latest_message_id
                )
                if val:
                    setattr(
                        convo_latest_msg,
                        "relevant_translation",
                        val[0],
                    )
                    setattr(
                        convo_latest_msg,
                        "translation_id",
                        val[1],
                    )
                    setattr(
                        convo_latest_msg,
                        "is_read",
                        val[2],
                    )

                setattr(
                    conversation,
                    "latest_message",
                    convo_latest_msg,
                )

            await convo_name_url_processing(
                convo=conversation, curr_user_id=user.id, redis_client=redis_client
            )

        return user, presigned_url

    async def get_by_email(self, db: AsyncSession, email: EmailStr) -> User | None:
        user = (
            (await db.execute(select(User).where(User.email == email)))
            .scalars()
            .first()
        )

        return user

    async def get_user_profiles(
        self, db: AsyncSession, user_ids: list[int]
    ) -> dict[int, str]:
        # optimized
        result = await db.execute(
            select(User.id, User.profile_photo).where(User.id.in_(user_ids))
        )

        user_photos_dict = {user_id: photo for user_id, photo in result.all() if photo}

        return user_photos_dict

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        exists = await db.execute(select(User).filter_by(email=obj_in.email))
        if exists.scalars().first():
            raise UserAlreadyExistsException(email=obj_in.email)
        hashed_pw = security.hash_password(obj_in.password)

        # Exclude the password from the input model and add the hashed password
        db_obj = User(
            **obj_in.model_dump(exclude={"password"}), password_hash=hashed_pw
        )
        db.add(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: User, obj_in: UserUpdate | dict[str, Any]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if "password" in update_data:
            hashed_pw = security.hash_password(update_data["password"])
            del update_data["password"]
            update_data["password_hash"] = hashed_pw

        return await super().update(db, db_obj=db_obj, obj_in=update_data)


user = CRUDUser(User)
