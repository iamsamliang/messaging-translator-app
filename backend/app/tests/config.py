import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import AsyncSessionLocal


@pytest.fixture(scope="session")
def db() -> AsyncSession:
    # Create a new event loop for the fixture
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Set up the async session
    async def get_async_session():
        async with AsyncSessionLocal() as session:
            yield session

    # Use the event loop to get the session
    session_gen = get_async_session()
    session = loop.run_until_complete(session_gen.__anext__())

    try:
        yield session
    finally:
        # Clean up the session and close the event loop
        loop.run_until_complete(session_gen.aclose())
        loop.close()
