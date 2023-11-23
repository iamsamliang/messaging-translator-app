import pytest
from typing import AsyncGenerator
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db


# specifies pytest to use asyncio for anyio markers
@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


# @pytest.fixture(scope="session", autouse=True)
# def faker_seed() -> int:
#     return 484


@pytest.fixture(scope="session")
def faker() -> Faker:
    return Faker()


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():  # iteratoring over the generator and returning individual elems
        yield session
