from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.models import Conversation
from app.schemas import ConversationCreateDB
from app.tests.utils.utils import random_string


async def create_random_convo(db: AsyncSession) -> Conversation:
    conversation_name = random_string(20)
    return await crud.conversation.create(
        db=db, obj_in=ConversationCreateDB(conversation_name=conversation_name)
    )
