from unittest import removeResult
from app import crud
from app.main import app
from app.models.models import User
from app.tests.utils.convo import create_random_convo
from app.tests.utils.utils import random_string
from sqlalchemy.orm import selectinload
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient
import pytest
from devtools import debug
from faker import Faker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.tests.utils.user import create_random_user_stochastic


@pytest.mark.anyio
async def test_create_convos(db: AsyncSession, faker: Faker) -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        random_user1 = await create_random_user_stochastic(db=db, faker=faker)
        random_user2 = await create_random_user_stochastic(db=db, faker=faker)
        await db.commit()

        convo_json = {
            "conversation_name": random_string(10),
            "user_ids": [{"email": random_user1.email}, {"email": random_user2.email}],
        }

        response = await ac.post(
            "/conversations", json={**convo_json, "bad_data": "BADD"}
        )

        assert response.status_code == 201
        created_convo = response.json()
        assert response.headers["Location"] == f"/conversations/{created_convo['id']}"

        get_new_convo = await crud.conversation.get(db=db, id=created_convo["id"])

        assert get_new_convo
        assert get_new_convo.conversation_name == created_convo["conversation_name"]
        assert jsonable_encoder(get_new_convo) == created_convo
        for idx, member in enumerate(await get_new_convo.awaitable_attrs.members):
            assert convo_json["user_ids"][idx]["email"] == member.email  # type: ignore


@pytest.mark.anyio
async def test_get_convos(db: AsyncSession) -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. create convo and commit it
        # 2. use endpoint to get convo
        # 3. grab created convo from database
        # 4. Compare to response
        convo = await create_random_convo(db=db)
        await db.commit()

        response = await ac.get(f"/conversations/{convo.id}")
        assert response.status_code == 200

        resp_convo = response.json()
        get_convo = await crud.conversation.get(db=db, id=resp_convo["id"])

        assert get_convo
        assert jsonable_encoder(get_convo) == resp_convo


@pytest.mark.anyio
async def test_update_convo_name(db: AsyncSession) -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. create convo and commit it
        # 2. use endpoint to update that convo's name
        # 3. grab it from database and compare to
        # endpoint response
        convo = await create_random_convo(db=db)
        old_name = convo.conversation_name
        await db.commit()

        response = await ac.patch(
            f"/conversations/{convo.id}/update-name",
            json={"conversation_name": random_string(10)},
        )
        new_convo = await crud.conversation.get(db=db, id=convo.id)
        # need this to refresh the cached version
        await db.refresh(new_convo)

        assert new_convo
        assert new_convo.conversation_name == response.json()["conversation_name"]
        assert jsonable_encoder(new_convo) == response.json()
        assert new_convo.conversation_name != old_name


@pytest.mark.anyio
async def test_update_convo_members(db: AsyncSession, faker: Faker) -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. create convo and three users
        # 2. commit them
        # 3. Use endpoint to do the following
        #     - Add users
        #     - Check it was added
        #     - Remove users
        #     - Check that they were removed
        # 4. use endpoint to update that convo's name
        # 5. grab it from database and compare to
        # endpoint response
        convo = await create_random_convo(db=db)
        user_emails = []
        for _ in range(3):
            user = await create_random_user_stochastic(db=db, faker=faker)

            user_emails.append({"email": user.email})

        await db.commit()

        response = await ac.patch(
            f"/conversations/{convo.id}/update-members",
            json={"method": "add", "user_ids": user_emails},
        )

        new_convo = await crud.conversation.get(db=db, id=convo.id)
        # need this to refresh the cached version
        await db.refresh(new_convo)

        assert new_convo
        assert jsonable_encoder(new_convo) == response.json()
        assert len(await new_convo.awaitable_attrs.members) == 3
        for idx, member in enumerate(await new_convo.awaitable_attrs.members):
            assert member.email == user_emails[idx]["email"]  # type: ignore

        stay_user_email = user_emails.pop()["email"]
        user_emails.pop()

        stay_user = await crud.user.get_by_email(db=db, email=stay_user_email)
        assert stay_user
        assert len(await stay_user.awaitable_attrs.conversations) == 1

        response = await ac.patch(
            f"/conversations/{convo.id}/update-members",
            json={"method": "remove", "user_ids": user_emails},
        )

        new_convo = await crud.conversation.get(db=db, id=convo.id)
        # need this to refresh the cached version
        await db.refresh(new_convo)

        assert new_convo
        assert jsonable_encoder(new_convo) == response.json()
        assert len(await new_convo.awaitable_attrs.members) == 2

        result = (
            (
                await db.execute(
                    select(User)
                    .where(User.email == user_emails[0]["email"])
                    .options(selectinload(User.conversations))
                )
            )
            .scalars()
            .first()
        )

        assert result

        assert len(result.conversations) == 0


@pytest.mark.anyio
async def test_delete_convos(db: AsyncSession, faker: Faker) -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. create users
        # 2. create convo with those users
        # 3. Delete convo
        # 4. verified it was deleted
        # 5. verify the relationships were also
        # removed in group_members table
        # 6. verified convo was removed from users

        random_user1 = await create_random_user_stochastic(db=db, faker=faker)
        random_user2 = await create_random_user_stochastic(db=db, faker=faker)
        await db.commit()

        convo_json = {
            "conversation_name": random_string(10),
            "user_ids": [{"email": random_user1.email}, {"email": random_user2.email}],
        }

        response = await ac.post("/conversations", json=convo_json)

        assert response.status_code == 201

        created_convo = response.json()

        response = await ac.delete(f"/conversations/{created_convo['id']}")
        assert response.status_code == 204
        assert await crud.conversation.get(db=db, id=created_convo["id"]) is None

        user1 = await crud.user.get(db=db, id=random_user1.id)
        user2 = await crud.user.get(db=db, id=random_user2.id)

        assert user1
        assert await user1.awaitable_attrs.conversations == []
        assert user2
        assert await user2.awaitable_attrs.conversations == []
