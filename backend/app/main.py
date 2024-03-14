import redis.asyncio as redis

from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi.middleware.cors import CORSMiddleware
from app.exceptions import UserAlreadyExistsException
from app.handlers import user_already_exists_exception_handler

from app.api.api_v1.api import api_router
from app.core.config import settings


# redis_client: redis.Redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    app.state.redis_client = redis.Redis(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True
    )
    # redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    yield
    await app.state.redis_client.aclose()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

allowed_origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_credentials=True,
)

app.include_router(api_router)

app.add_exception_handler(
    UserAlreadyExistsException, user_already_exists_exception_handler
)
