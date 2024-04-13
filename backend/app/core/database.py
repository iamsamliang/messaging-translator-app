from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings

engine = create_async_engine(
    url=str(settings.SQLALCHEMY_DATABASE_URI),
    echo=False,
    pool_size=10,  # higher size for higher concurrency requirements in app
    max_overflow=20,  # pool can open up to N additional connections beyond the pool_size if required during peak loads
    pool_timeout=30,  # number of seconds to wait before giving up on returning a connection from the pool. If all connections are in use, and no connection becomes available within the pool_timeout period, an exception is raised
    pool_recycle=1800,  # sets the maximum age (in seconds) of connections in the pool. After this time, a connection will be replaced with a new one. Helps avoid DB timeouts or issues with stale connections
    pool_pre_ping=True,  # before each DB operation, ping the database w/ a connection from the connection pool. If the ping fails, the connection is discarded and replaced with a new one. This helps avoid errors due to stale or broken connections.
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
