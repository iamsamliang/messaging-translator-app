from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings

db_url = settings.DATABASE_URL

engine = create_async_engine(
    url=db_url,
    echo=False,
    # pool_size=10, # optimization params
    # max_overflow=20,
    # pool_timeout=30,
    # pool_recycle=1800,  # e.g., 30 minutes
    pool_pre_ping=True,
)


# Using Alembic so don't call this
# async def create_tables():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
# Must run the async function using asyncio.run
# asyncio.run(create_tables())

AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base.metadata.create_all(engine)  # create tables if they don't exist, can't do this in async
