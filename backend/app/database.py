from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_async_engine("postgresql+psycopg2://user:password@localhost/dbname")
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
