from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.core import security
from app.core.config import settings
from ..database import AsyncSessionLocal

# tokenURL is used for documentation. Tells client where to get an access token
reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"login/access-token")

# async def get_db() -> Generator:
#     try:
#         db = await AsyncSessionLocal()
#         yield db
#     finally:
#         await db.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        yield db  # produces an AsyncGenerator


async def verify_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(reusable_oauth2)],
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_payload = schemas.TokenPayLoad(username=username)
    except (JWTError, ValidationError):
        raise credentials_exception

    user = await crud.user.get_by_email(db=db, email=token_payload.username)
    if not user:
        raise credentials_exception
    return user


async def verify_current_admin(
    current_user: Annotated[models.User, Depends(verify_current_user)],
) -> models.User:
    if not current_user.is_admin:
        raise HTTPException(status_code=400, detail="The user is not an admin")
    return current_user


# Shared Annotated Dependencies
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]
