import pytest
from faker import Faker
from typing import Type

from pydantic import ValidationError
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.schemas import UserCreate, UserUpdate
from app.exceptions import UserAlreadyExistsException
from app.core.security import verify_password
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_string


@pytest.mark.parametrize(
    "expected_exception",
    [(None), (ValidationError), (UserAlreadyExistsException)],
)
@pytest.mark.anyio
async def test_create_user(
    expected_exception: Type[Exception] | None,
    db: AsyncSession,
    faker: Faker,
) -> None:
    first_name = random_string(100)
    last_name = random_string(100)
    profile_photo = random_string(200)
    target_language = "english"
    email = faker.email()
    password = faker.password()
    if expected_exception is ValidationError:
        with pytest.raises(expected_exception):
            profile_photo = random_string(300)
            user_schema = UserCreate(
                first_name=first_name,
                last_name=last_name,
                profile_photo=profile_photo,
                email=email,
                target_language=target_language,
                password=password,
            )
            await crud.user.create(db=db, obj_in=user_schema)
            await db.commit()  # to ensure it doesn't commit
    elif expected_exception is UserAlreadyExistsException:
        with pytest.raises(expected_exception):
            user_schema = UserCreate(
                first_name=first_name,
                last_name=last_name,
                profile_photo=profile_photo,
                email=email,
                target_language=target_language,
                password=password,
            )
            await crud.user.create(db=db, obj_in=user_schema)
            await db.commit()
            await crud.user.create(db=db, obj_in=user_schema)  # creating duplicate
            await db.commit()
    else:
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
async def test_create_admin(db: AsyncSession, faker: Faker) -> None:
    first_name = random_string(8)
    last_name = random_string(15)
    profile_photo = random_string(20)
    email = faker.email()
    password = faker.password()
    target_language = "ENGLISH"
    is_admin = True
    user_schema = UserCreate(
        first_name=first_name,
        last_name=last_name,
        profile_photo=profile_photo,
        email=email,
        target_language=target_language,
        is_admin=is_admin,
        password=password,
    )
    user = await crud.user.create(db=db, obj_in=user_schema)
    await db.commit()
    assert user.first_name == first_name.lower()
    assert user.last_name == last_name.lower()
    assert user.profile_photo == profile_photo
    assert user.target_language == target_language.lower()
    assert user.email == email
    assert user.is_admin == True
    assert hasattr(user, "created_at")
    assert hasattr(user, "password_hash")
    assert hasattr(user, "id")
    assert await user.awaitable_attrs.messages_sent == []
    assert await user.awaitable_attrs.messages_received == []
    assert await user.awaitable_attrs.conversations == []


@pytest.mark.anyio
async def test_get_by_email(db: AsyncSession, faker: Faker) -> None:
    first_name = random_string(8)
    last_name = random_string(15)
    profile_photo = random_string(20)
    email = faker.email()
    password = faker.password()
    target_language = "ENGLISH"
    is_admin = False
    user_schema = UserCreate(
        first_name=first_name,
        last_name=last_name,
        profile_photo=profile_photo,
        email=email,
        target_language=target_language,
        is_admin=is_admin,
        password=password,
    )
    create_user = await crud.user.create(db=db, obj_in=user_schema)
    await db.commit()

    get_user = await crud.user.get_by_email(db=db, email=email)

    assert get_user
    assert create_user.email == get_user.email
    assert jsonable_encoder(create_user) == jsonable_encoder(get_user)


@pytest.mark.anyio
async def test_get_by_id(db: AsyncSession, faker: Faker) -> None:
    first_name = random_string(5)
    last_name = random_string(10)
    profile_photo = random_string(5)
    email = faker.email()
    password = faker.password()
    target_language = "mandarin"
    is_admin = False
    user_schema = UserCreate(
        first_name=first_name,
        last_name=last_name,
        profile_photo=profile_photo,
        email=email,
        target_language=target_language,
        is_admin=is_admin,
        password=password,
    )
    create_user = await crud.user.create(db=db, obj_in=user_schema)
    await db.commit()

    get_user = await crud.user.get(db=db, id=create_user.id)

    assert get_user
    assert create_user.email == get_user.email
    assert jsonable_encoder(create_user) == jsonable_encoder(get_user)


@pytest.mark.anyio
async def test_get_nonexisting_user(db: AsyncSession) -> None:
    user1 = await crud.user.get(db=db, id=-1)
    user2 = await crud.user.get_by_email(db=db, email="thisdontexist@-1None.com")

    assert user1 is None
    assert user2 is None


@pytest.mark.anyio
async def test_update_user(db: AsyncSession, faker: Faker) -> None:
    first_name = random_string(5)
    last_name = random_string(5)
    profile_photo = random_string(5)
    email = faker.email()
    password = faker.password()
    target_language = "spanish"
    is_admin = False
    user_schema = UserCreate(
        first_name=first_name,
        last_name=last_name,
        profile_photo=profile_photo,
        email=email,
        target_language=target_language,
        is_admin=is_admin,
        password=password,
    )
    user = await crud.user.create(db=db, obj_in=user_schema)
    password_hash = user.password_hash
    await db.commit()
    id = user.id
    created_at = user.created_at
    new_password = faker.password()
    update_schema = UserUpdate(
        target_language="french",
        profile_photo=random_string(5),
        is_admin=True,
        password=new_password,
    )
    updated_user = await crud.user.update(db=db, db_obj=user, obj_in=update_schema)
    await db.commit()
    assert id == updated_user.id
    assert first_name.lower() == updated_user.first_name
    assert last_name.lower() == updated_user.last_name
    assert email == updated_user.email
    assert created_at == updated_user.created_at
    assert target_language.lower() != updated_user.target_language
    assert profile_photo != updated_user.profile_photo
    assert is_admin != updated_user.is_admin
    assert password_hash != updated_user.password_hash
    assert verify_password(new_password, updated_user.password_hash)


@pytest.mark.anyio
async def test_delete_user(db: AsyncSession, faker: Faker) -> None:
    user = await create_random_user(
        db=db,
        email=faker.email(),
        password=faker.password(),
        fname_len=3,
        lname_len=3,
        photo_len=10,
        target_lang="english",
        is_admin=False,
    )
    await db.commit()
    id = user.id
    assert jsonable_encoder((await crud.user.get(db=db, id=id))) == jsonable_encoder(
        user
    )
    await crud.user.delete(db=db, id=user.id)
    await db.commit()
    assert await crud.user.get(db=db, id=id) is None
