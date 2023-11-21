from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.models import User
from app.schemas import UserCreate
from .utils import random_string


async def create_random_user(
    db: AsyncSession,
    faker: Faker,
    fname_len: int,
    lname_len: int,
    photo_len: int,
    target_lang: str,
    is_admin: bool,
) -> User:
    first_name = random_string(fname_len)
    last_name = random_string(lname_len)
    profile_photo = random_string(photo_len)
    email = faker.email()
    password = faker.password()
    target_language = target_lang
    is_admin = is_admin
    user_schema = UserCreate(
        first_name=first_name,
        last_name=last_name,
        profile_photo=profile_photo,
        email=email,
        target_language=target_language,
        is_admin=is_admin,
        password=password,
    )
    return await crud.user.create(db=db, obj_in=user_schema)
