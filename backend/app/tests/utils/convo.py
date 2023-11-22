from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.tests.utils.utils import random_string


async def create_random_convo(db: AsyncSession):
    conversation_name = random_string(20)
    return await crud.conversation.create(db=db, convo_name=conversation_name)
