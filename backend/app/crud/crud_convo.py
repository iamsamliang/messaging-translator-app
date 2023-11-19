from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models import Conversation, User
from app.schemas import ConversationCreateDB, ConversationNameUpdate, Method
from .base import CRUDBase


class CRUDConversation(
    CRUDBase[Conversation, ConversationCreateDB, ConversationNameUpdate]
):
    async def create(
        self, db: AsyncSession, *, convo: ConversationCreateDB
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
        db_convo = Conversation(**convo.model_dump())
        db.add(db_convo)
        # await db.commit()
        # await db.refresh(db_convo)
        return db_convo

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
                if user not in convo.members:  # not in group
                    convo.members.append(user)  # NOTE: need to validate if user exists
        else:
            for user in users:
                if user in convo.members:  # user is in group
                    convo.members.remove(
                        user
                    )  # NOTE: need to check if user exists maybe
        # await db.commit()
        return convo


conversation = CRUDConversation(Conversation)
