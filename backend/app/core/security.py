from typing import Any
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from fastapi import HTTPException, status
from pydantic import ValidationError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from enum import Enum
from redis.asyncio import Redis

from app import schemas, models, crud
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


class VerifyType(str, Enum):
    EXTRA_INFO = "extra"
    DEFAULT = "default"


# Things to implement: refresh tokens, Token Blacklisting / Revocation, Rate Limiting on Authentication Endpoints, Logging for authentication attempts and token issues, Scope and Permission Checks (which actiosn can they perform), logging out (done on client side by deleting the stored token as it is not stored on the backend, so backend doesn't have to do anything. Token blacklisting unnecessary and introduces more complexity)


def create_access_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


async def verify_token(
    db: AsyncSession, token: str, type: VerifyType, redis_client: Redis | None = None
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        user_id = payload.get("sub")
        iat = payload.get("iat")

        if user_id is None or iat is None:
            raise credentials_exception

        token_payload = schemas.TokenPayLoad(userid=user_id, iat=iat)
    except (JWTError, ValidationError):
        raise credentials_exception

    start_idx = token_payload.userid.find(":") + 1

    if type == VerifyType.EXTRA_INFO:
        if redis_client is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Redis Client"
            )
        user, presigned_url = await crud.user.get_w_extra_info(
            db=db,
            user_id=int(token_payload.userid[start_idx:]),
            redis_client=redis_client,
        )
        setattr(
            user,
            "presigned_url",
            presigned_url,
        )
    else:
        user = await crud.user.get(db=db, id=int(token_payload.userid[start_idx:]))

    if not user:
        raise credentials_exception

    if user.pwd_changed.replace(tzinfo=timezone.utc) > token_payload.iat.replace(
        tzinfo=timezone.utc
    ):
        raise credentials_exception

    return user
