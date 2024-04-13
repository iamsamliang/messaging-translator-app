import logging
import asyncio

from sqlalchemy import select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)  # type: ignore
async def init() -> None:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(select(1))  # Check DB is responsive
    except Exception as e:
        logger.error(e)
        raise e


async def main() -> None:
    logger.info("Testing DB Connection")
    await init()
    logger.info("DB Connection Works!")


if __name__ == "__main__":
    asyncio.run(main())
