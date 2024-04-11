import redis.asyncio as redis

from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi.middleware.cors import CORSMiddleware
from app.exceptions import UserAlreadyExistsException
from app.handlers import user_already_exists_exception_handler

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.cron.db_cleanup import delete_expired_unverified_users
from app.logger import setup_logger


setup_logger()

import logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    app.state.redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
        ssl=settings.REDIS_SSL,
        password=settings.REDIS_PASSWORD,
        # ssl_cert_reqs="none",
    )

    try:
        await app.state.redis_client.ping()
    except Exception as e:
        logging.error(f"Error connecting to Redis", exc_info=True)
        raise e

    await delete_expired_unverified_users()
    yield
    await app.state.redis_client.aclose()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

app.include_router(api_router)

app.add_exception_handler(
    UserAlreadyExistsException, user_already_exists_exception_handler
)
