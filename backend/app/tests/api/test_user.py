from app.core.security import verify_password
from fastapi.encoders import jsonable_encoder
import pytest
import asyncio
import time
from faker import Faker
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.main import app
from app.tests.utils.utils import random_string

# These tests test concurrency as well


@pytest.mark.anyio
async def test_concurrent_create_users(db: AsyncSession, faker: Faker) -> None:
    # base_url isn't used but needed to work
    async with AsyncClient(app=app, base_url="http://test") as ac:
        data = {
            "first_name": "John",
            "last_name": "Smith",
            "profile_photo": "profilephoto",
            "email": "johnsmith@example.com",
            "target_language": "english",
            "password": faker.password(),
        }
        response = await ac.post(
            "/users",
            json={
                **data,
                "miscellaneous": "bad data",
            },
        )
        assert response.status_code == 201

        created_user = response.json()

        get_user = await crud.user.get_by_email(db, email="johnsmith@example.com")

        assert get_user
        assert get_user.email == created_user["email"]
        assert jsonable_encoder(get_user, exclude={"password_hash"}) == created_user

        assert response.headers["Location"] == f"/users/{response.json()['id']}"

        # testing concurrency
        start_time = time.time()
        tasks = [
            ac.post(
                "/users",
                json={
                    "first_name": random_string(5),
                    "last_name": random_string(6),
                    "profile_photo": "profilephoto",
                    "email": f"{random_string(5)}@example.com",
                    "target_language": "english",
                    "miscellaneous": "bad data",
                    "password": faker.password(),
                },
            )
            for _ in range(10)
        ]  # simulating 10 concurrent requests
        responses = await asyncio.gather(*tasks)
        end_time = time.time()

        total_time = end_time - start_time
        assert total_time < 10  # kind of tests endpoint concurrency

        # tests endpoint logic and functionality
        for response in responses:
            assert response.status_code == 201
            created_user = response.json()

            get_user = await crud.user.get(db, id=created_user["id"])

            assert get_user
            assert get_user.email == created_user["email"]
            assert jsonable_encoder(get_user, exclude={"password_hash"}) == created_user
            assert response.headers["Location"] == f"/users/{response.json()['id']}"


@pytest.mark.anyio
async def test_update_users(db: AsyncSession, faker: Faker) -> None:
    # base_url isn't used but needed to work
    async with AsyncClient(app=app, base_url="http://test") as ac:
        data = {
            "first_name": random_string(5),
            "last_name": random_string(6),
            "profile_photo": "profilephoto",
            "email": faker.email(),
            "target_language": "english",
            "password": faker.password(),
        }
        response = await ac.post("/users", json={**data})
        assert response.status_code == 201

        created_user = response.json()

        response = await ac.patch(
            f"/users/{created_user['id']}",
            json={"first_name": "Joe", "last_name": "Schmoe", "password": "123abchaha"},
        )
        assert response.status_code == 200

        updated_user = response.json()

        get_updated_user = await crud.user.get_by_email(
            db=db, email=updated_user["email"]
        )

        assert get_updated_user
        assert get_updated_user.email == updated_user["email"]
        assert (
            jsonable_encoder(get_updated_user, exclude={"password_hash"})
            == updated_user
        )

        # make sure this updated user is different from the original but has same id
        assert get_updated_user.id == created_user["id"]
        assert get_updated_user.first_name == "joe"
        assert get_updated_user.first_name != created_user["first_name"]
        assert get_updated_user.last_name != created_user["last_name"]
        assert verify_password("123abchaha", get_updated_user.password_hash)


@pytest.mark.anyio
async def test_concurrent_delete_users(db: AsyncSession, faker: Faker) -> None:
    # base_url isn't used but needed to work
    async with AsyncClient(app=app, base_url="http://test") as ac:
        data = {
            "first_name": random_string(5),
            "last_name": random_string(6),
            "profile_photo": "profilephoto",
            "email": faker.email(),
            "target_language": "english",
            "password": faker.password(),
        }
        response = await ac.post("/users", json={**data})
        assert response.status_code == 201

        created_user = response.json()
        get_user = await crud.user.get_by_email(db, email=created_user["email"])

        assert get_user

        response = await ac.delete(
            f"/users/{created_user['id']}",
        )
        assert response.status_code == 204

        deleted_user = await crud.user.get_by_email(db, email=created_user["email"])
        assert deleted_user != get_user
        assert deleted_user is None
