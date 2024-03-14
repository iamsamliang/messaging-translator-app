from typing import Annotated, AsyncGenerator, Callable
import logging

from fastapi import Cookie, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.core.security import verify_token, VerifyType
from ..database import AsyncSessionLocal


# tokenURL is used for documentation. Tells client where to get an access token
reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"login/access-token")

# async def get_db() -> Generator:
#     try:
#         db = await AsyncSessionLocal()
#         yield db
#     finally:
#         await db.close()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        yield db  # produces an AsyncGenerator


def verify_current_user_factory(type: VerifyType) -> Callable[..., models.User]:
    async def verify_current_user(
        db: Annotated[AsyncSession, Depends(get_db)],
        token: Annotated[str, Depends(reusable_oauth2)],
        request: Request,
    ) -> models.User:
        return await verify_token(
            db=db, token=token, type=type, redis_client=request.app.state.redis_client
        )

    return verify_current_user  # type: ignore


# async def verify_current_user(
#     db: Annotated[AsyncSession, Depends(get_db)],
#     token: Annotated[str, Depends(reusable_oauth2)],
# ) -> models.User:
# return await verify_token(db=db, token=token, type=VerifyType.EXTRA_INFO)


async def verify_current_user_w_cookie(
    db: Annotated[AsyncSession, Depends(get_db)],
    jwt: Annotated[str, Cookie()],
) -> models.User:
    return await verify_token(
        db=db,
        token=jwt,
        type=VerifyType.DEFAULT,
    )


async def verify_current_admin(
    current_user: Annotated[models.User, Depends(verify_current_user_w_cookie)],
) -> models.User:
    if not current_user.is_admin:
        raise HTTPException(status_code=400, detail="The user is not an admin")
    return current_user


# Shared Annotated Dependencies
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]
