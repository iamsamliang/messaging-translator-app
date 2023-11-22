import pytest

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder

from app import crud
from app.tests.utils.user import create_random_user_stochastic


@pytest.mark.anyio
async def test_create_convo(db: AsyncSession):
    conversation_name = "conversation test"
    created_convo = await crud.conversation.create(db=db, convo_name=conversation_name)
    await db.commit()

    assert created_convo.conversation_name == conversation_name


@pytest.mark.anyio
async def test_get_convo(db: AsyncSession):
    conversation_name = "conversation test"
    created_convo = await crud.conversation.create(db=db, convo_name=conversation_name)
    await db.commit()

    get_convo = await crud.conversation.get(db=db, id=created_convo.id)
    assert get_convo
    assert get_convo.conversation_name == created_convo.conversation_name
    assert jsonable_encoder(get_convo) == jsonable_encoder(created_convo)


@pytest.mark.anyio
async def test_delete_convo(db: AsyncSession):
    conversation_name = "conversation test"
    created_convo = await crud.conversation.create(db=db, convo_name=conversation_name)
    await db.commit()

    await crud.conversation.delete(db=db, id=created_convo.id)
