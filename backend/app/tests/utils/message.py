from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.models import Message
from app.schemas import MessageCreate
from app.tests.utils.user import create_random_user_stochastic
from app.tests.utils.convo import create_random_convo


async def create_random_message(
    db: AsyncSession, faker: Faker, text: str, language: str
) -> Message:
    random_user = await create_random_user_stochastic(db=db, faker=faker)
    random_convo = await create_random_convo(db=db)
    await db.flush()

    msg_schema = MessageCreate(
        conversation_id=random_convo.id,
        sender_id=random_user.id,
        original_text=text,
        orig_language=language,
    )
    return await crud.message.create(db=db, obj_in=msg_schema)
