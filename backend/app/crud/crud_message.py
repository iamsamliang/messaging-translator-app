from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Message
from app.schemas import MessageCreate, MessageUpdate

from .base import CRUDBase


class CRUDMessage(CRUDBase[Message, MessageCreate, MessageUpdate]):
    async def get_most_recent_messages(
        self, *, db: AsyncSession, convo_id: int, offset: int, limit: int
    ) -> Sequence[Message]:
        latest_n_msgs = (
            (
                await db.execute(
                    select(Message)
                    .where(Message.conversation_id == convo_id)
                    .order_by(Message.sent_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )

        return latest_n_msgs


message = CRUDMessage(Message)
