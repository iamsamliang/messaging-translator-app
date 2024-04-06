import random
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.models import User
from app.schemas import UserCreate
from app.schemas.email_type import CustomEmailStr
from .utils import random_string


async def create_random_user_stochastic(
    db: AsyncSession, faker: Faker, target_lang: str = "english"
) -> User:
    first_name = random_string(random.randint(5, 30))
    last_name = random_string(random.randint(5, 30))
    profile_photo = random_string(random.randint(5, 30))
    user_schema = UserCreate(
        first_name=first_name,
        last_name=last_name,
        profile_photo=profile_photo,
        email=faker.email(),
        target_language=target_lang,
        is_admin=False,
        password=faker.password(),
    )
    return await crud.user.create(db=db, obj_in=user_schema)


async def create_random_user(
    db: AsyncSession,
    email: CustomEmailStr,
    password: str,
    fname_len: int,
    lname_len: int,
    photo_len: int,
    target_lang: str,
    is_admin: bool,
) -> User:
    first_name = random_string(fname_len)
    last_name = random_string(lname_len)
    profile_photo = random_string(photo_len)
    user_schema = UserCreate(
        first_name=first_name,
        last_name=last_name,
        profile_photo=profile_photo,
        email=email,
        target_language=target_lang,
        is_admin=is_admin,
        password=password,
    )
    return await crud.user.create(db=db, obj_in=user_schema)
