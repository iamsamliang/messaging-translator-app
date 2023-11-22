import pytest

from faker import Faker
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.schemas import MessageCreate
from app.tests.utils.user import create_random_user_stochastic
from app.tests.utils.convo import create_random_convo


@pytest.mark.anyio
async def test_create_and_get_message(db: AsyncSession, faker: Faker):
    random_user = await create_random_user_stochastic(db=db, faker=faker)
    random_convo = await create_random_convo(db=db)
    await db.flush()

    msg_schema = MessageCreate(
        conversation_id=random_convo.id,
        sender_id=random_user.id,
        original_text="hello how are you",
        orig_language="english",
    )

    created_msg = await crud.message.create(db=db, obj_in=msg_schema)
    await db.commit()

    get_msg = await crud.message.get(db=db, id=created_msg.id)
    assert get_msg
    assert get_msg.original_text == created_msg.original_text
    assert jsonable_encoder(created_msg) == jsonable_encoder(get_msg)


@pytest.mark.anyio
async def test_delete_msg(db: AsyncSession, faker: Faker):
    random_user = await create_random_user_stochastic(db=db, faker=faker)
    random_convo = await create_random_convo(db=db)
    await db.flush()

    msg_schema = MessageCreate(
        conversation_id=random_convo.id,
        sender_id=random_user.id,
        original_text="hello how are you",
        orig_language="english",
    )

    created_msg = await crud.message.create(db=db, obj_in=msg_schema)
    await db.commit()
    msg_id = created_msg.id

    await crud.message.delete(db=db, id=msg_id)
    await db.commit()
    assert await crud.message.get(db=db, id=msg_id) is None


# functionality not implemented yet
@pytest.mark.anyio
async def test_update_msg(db: AsyncSession, faker: Faker):
    pass
