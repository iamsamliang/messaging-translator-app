import pytest
from faker import Faker

from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.schemas import UserCreate
from app.tests.utils.utils import random_string

# get_by_id
# create
# update
# delete
# superuser
# authentication


@pytest.mark.anyio
async def test_create_valid_user(db: AsyncSession, faker: Faker) -> None:
    first_name = random_string(100)
    last_name = random_string(100)
    profile_photo = random_string(200)
    target_language = "english"
    email = faker.email()
    password = faker.password()
    user_schema = UserCreate(
        first_name=first_name,
        last_name=last_name,
        profile_photo=profile_photo,
        email=email,
        target_language=target_language,
        password=password,
    )
    user = await crud.user.create(db=db, obj_in=user_schema)
    await db.commit()
    await db.refresh(user)
    assert user.first_name == first_name.lower()
    assert user.last_name == last_name.lower()
    assert user.profile_photo == profile_photo
    assert user.target_language == target_language.lower()
    assert user.email == email
    assert user.is_admin == False
    assert hasattr(user, "created_at")
    assert hasattr(user, "password_hash")
    assert hasattr(user, "id")


@pytest.mark.anyio
async def test_create_invalid_user(db: AsyncSession, faker: Faker) -> None:
    first_name = random_string(100)
    last_name = random_string(100)
    profile_photo = random_string(300)
    target_language = "english"
    email = faker.email()
    password = faker.password()
    user_schema = UserCreate(
        first_name=first_name,
        last_name=last_name,
        profile_photo=profile_photo,
        email=email,
        target_language=target_language,
        password=password,
    )
    user = await crud.user.create(db=db, obj_in=user_schema)
    await db.commit()
    await db.refresh(user)
