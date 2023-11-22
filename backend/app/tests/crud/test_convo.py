import pytest

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder

from app import crud
from app.schemas import ConversationNameUpdate
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
    id = created_convo.id

    await crud.conversation.delete(db=db, id=id)
    await db.commit()
    assert await crud.conversation.get(db=db, id=id) is None


@pytest.mark.anyio
async def test_update_name(db: AsyncSession):
    conversation_name = "conversation test"
    created_convo = await crud.conversation.create(db=db, convo_name=conversation_name)
    await db.commit()
    old_id = created_convo.id
    new_name = "new conversation test"
    await crud.conversation.update(
        db=db,
        db_obj=created_convo,
        obj_in=ConversationNameUpdate(conversation_name=new_name),
    )
    await db.commit()
    updated_convo = await crud.conversation.get(db=db, id=old_id)

    assert updated_convo.conversation_name == new_name
    assert updated_convo.id == old_id


@pytest.mark.anyio
async def test_add_remove_users(db: AsyncSession, faker: Faker):
    conversation_name = "add/delete users"
    created_convo = await crud.conversation.create(db=db, convo_name=conversation_name)
    await db.commit()
    assert await created_convo.awaitable_attrs.members == []
    assert await created_convo.awaitable_attrs.messages == []

    # test add users
    users = set()
    user1 = await create_random_user_stochastic(db=db, faker=faker)
    users.add(user1)
    users.add(user1)
    assert len(users) == 1
    for _ in range(4):
        users.add(await create_random_user_stochastic(db=db, faker=faker))
    assert len(users) == 5
    updated_convo = await crud.conversation.update_users(
        db=db, convo_id=created_convo.id, users=users, method="add"
    )
    await db.commit()

    assert updated_convo
    assert len(set(await created_convo.awaitable_attrs.members)) == 5
    for member in await created_convo.awaitable_attrs.members:
        assert member in users

    # test remove users
    removed_users = set()
    for _ in range(3):
        removed_users.add(users.pop())

    assert len(users) == 2

    await crud.conversation.update_users(
        db=db, convo_id=created_convo.id, users=removed_users, method="remove"
    )
    await db.commit()

    updated_convo = await crud.conversation.get(db=db, id=created_convo.id)

    assert updated_convo
    assert len(set(await created_convo.awaitable_attrs.members)) == 2
    for member in await created_convo.awaitable_attrs.members:
        assert member in users
        assert member not in removed_users
