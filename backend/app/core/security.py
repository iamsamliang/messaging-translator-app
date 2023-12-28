from typing import Any
from datetime import datetime, timedelta

from jose import jwt, JWTError
from fastapi import HTTPException, status
from pydantic import ValidationError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, models, crud
from app.core.config import settings

from devtools import debug

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

# Things to implement: refresh tokens, Token Blacklisting / Revocation, Rate Limiting on Authentication Endpoints, Logging for authentication attempts and token issues, Scope and Permission Checks (which actiosn can they perform), logging out (done on client side by deleting the stored token as it is not stored on the backend, so backend doesn't have to do anything. Token blacklisting unnecessary and introduces more complexity)


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


async def verify_token(db: AsyncSession, token: str) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_payload = schemas.TokenPayLoad(username=username)
    except (JWTError, ValidationError):
        raise credentials_exception

    start_idx = token_payload.username.find(":") + 1
    user = await crud.user.get_by_email(db=db, email=token_payload.username[start_idx:])
    if not user:
        raise credentials_exception
    return user
