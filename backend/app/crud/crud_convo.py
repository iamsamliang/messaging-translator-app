from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Conversation, User
from app.schemas import ConversationCreateDB, ConversationNameUpdate, Method
from .base import CRUDBase


class CRUDConversation(
    CRUDBase[Conversation, ConversationCreateDB, ConversationNameUpdate]
):
    async def create(
        self, db: AsyncSession, *, obj_in: ConversationCreateDB
    ) -> Conversation:
        """When we create a conversation, we must have users that we want to add already

        Args:
            db (AsyncSession)
            convo (ConversationCreateDB)

        Returns:
            Conversation: the created Conversation object
        """
        # 1. add the new convo to the conversation table
        # 2. update group_member_assoication table to add the existing users to the new convo
        # NOTE: Check if conversation already exists
        return await super().create(db=db, obj_in=obj_in)

    async def update_users(
        self, db: AsyncSession, *, convo_id: int, users: set[User], method: Method
    ) -> Conversation | None:
        convo = (
            (await db.execute(select(Conversation).filter_by(id=convo_id)))
            .scalars()
            .first()
        )
        if not convo:
            return None

        if method == Method.ADD:
            for user in users:
                if user not in await convo.awaitable_attrs.members:  # not in group
                    (await convo.awaitable_attrs.members).append(
                        user
                    )  # NOTE: need to validate if user exists
        else:
            for user in users:
                if user in await convo.awaitable_attrs.members:  # user is in group
                    (await convo.awaitable_attrs.members).remove(
                        user
                    )  # NOTE: need to check if user exists maybe
        # await db.commit()
        return convo


conversation = CRUDConversation(Conversation)
