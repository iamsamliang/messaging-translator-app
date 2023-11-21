# app/handlers.py

from fastapi import Request
from fastapi.responses import JSONResponse

from .exceptions import *


async def user_already_exists_exception_handler(
    request: Request, exc: UserAlreadyExistsException
):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message},
    )
