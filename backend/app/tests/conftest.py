import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import AsyncSessionLocal
from ..dependencies import get_db


@pytest.fixture(scope="session", autouse=True)
def faker_seed() -> int:
    return 484


@pytest.fixture
async def db() -> AsyncSession:
    async for session in get_db():  # iteratoring over the generator and returning individual elems
        yield session
