import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.core import security
from app.tests.utils.user import create_random_user


@pytest.mark.anyio
async def test_authenticate_user(db: AsyncSession, faker: Faker) -> None:
    email = faker.email()
    password = faker.password()
    target_language = "ENGLISH"
    is_admin = False
    await create_random_user(
        db=db,
        email=email,
        password=password,
        fname_len=8,
        lname_len=15,
        photo_len=10,
        target_lang=target_language,
        is_admin=is_admin,
    )
    await db.commit()

    get_user = await crud.user.get_by_email(db=db, email=email)
    # authenticate user
    assert get_user
    assert email == get_user.email
    assert security.verify_password(password, get_user.password_hash)
    assert not security.verify_password(faker.password(), get_user.password_hash)
