import pytest
from faker import Faker

from pydantic import ValidationError
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.schemas import UserCreate
from app.exceptions import UserAlreadyExistsException
from app.tests.utils.utils import random_string

# update
# delete
# authentication


@pytest.mark.parametrize(
    "expected_exception",
    [(None), (ValidationError), (UserAlreadyExistsException)],
)
@pytest.mark.anyio
async def test_create_user(expected_exception, db: AsyncSession, faker: Faker) -> None:
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
            await crud.user.create(db=db, obj_in=user_schema)
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
async def test_create_admin(db: AsyncSession, faker: Faker):
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
    await db.refresh(user)
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
async def test_get_by_email(db: AsyncSession, faker: Faker):
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
async def test_get_by_id(db: AsyncSession, faker: Faker):
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
    await db.refresh(create_user)

    get_user = await crud.user.get(db=db, id=create_user.id)

    assert get_user
    assert create_user.email == get_user.email
    assert jsonable_encoder(create_user) == jsonable_encoder(get_user)


@pytest.mark.anyio
async def test_get_nonexisting_user(db: AsyncSession):
    user1 = await crud.user.get(db=db, id=-1)
    user2 = await crud.user.get_by_email(db=db, email="thisdontexist@-1None.com")

    assert user1 is None
    assert user2 is None
