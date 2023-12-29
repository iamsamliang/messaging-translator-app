from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from pydantic import EmailStr

from app.models import User, Conversation, Translation
from app.schemas.user import UserCreate, UserUpdate
from app.exceptions import UserAlreadyExistsException
from app.core import security
from .base import CRUDBase


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_email(self, db: AsyncSession, email: EmailStr) -> User | None:
        user = (
            (
                await db.execute(
                    select(User)
                    .where(User.email == email)
                    .options(
                        selectinload(User.conversations).joinedload(
                            Conversation.latest_message
                        )
                    )
                )
            )
            .scalars()
            .first()
        )

        latest_message_ids = [
            conversation.latest_message.id for conversation in user.conversations
        ]

        # Assuming `user.target_language` holds the desired language of the user
        relevant_translations = await db.execute(
            select(Translation.message_id, Translation.translation).where(
                Translation.message_id.in_(latest_message_ids),
                Translation.language == user.target_language,
            )
        )

        relevant_translations = relevant_translations.all()

        translation_map = {
            trans.message_id: trans.translation for trans in relevant_translations
        }

        for conversation in user.conversations:
            setattr(
                conversation.latest_message,
                "relevant_translation",
                translation_map.get(
                    conversation.latest_message.id,
                ),
            )

        return user

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        exists = await db.execute(select(User).filter_by(email=obj_in.email))
        if exists.scalars().first():
            raise UserAlreadyExistsException(email=obj_in.email)
        # if db.query(User).filter_by(email=obj_in.email).first():
        #     raise UserAlreadyExistsException(email=obj_in.email)
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
        if update_data["password"]:
            hashed_pw = security.hash_password(update_data["password"])
            del update_data["password"]
            update_data["password_hash"] = hashed_pw
        return await super().update(db, db_obj=db_obj, obj_in=update_data)


user = CRUDUser(User)

# # Authenticating a user
# is_authenticated = user_service.authenticate_user(
#     email="jane@example.com", password="securepassword"
# )

# # Changing a user's preferred language
# user_service.change_user_language(user_id=new_user.user_id, new_language="es")
