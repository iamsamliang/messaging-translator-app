from fastapi import FastAPI

from app.exceptions import UserAlreadyExistsException
from app.handlers import user_already_exists_exception_handler

from app.api.api_v1.api import api_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(api_router)

app.add_exception_handler(
    UserAlreadyExistsException, user_already_exists_exception_handler
)
