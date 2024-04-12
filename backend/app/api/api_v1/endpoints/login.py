from typing import Annotated
from datetime import timedelta, datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app import crud, schemas
from app.core import security
from app.core.config import settings
from app.api.dependencies import DatabaseDep

router = APIRouter()


# Login
@router.post("/access-token", response_model=schemas.TokenOut)
async def login_for_token(
    db: DatabaseDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> dict[str, str]:
    login_user = await crud.user.get_by_email(db, form_data.username)
    if not login_user or not security.verify_password(
        form_data.password, login_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not login_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Please verify your account first to login",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": f"userid:{login_user.id}", "iat": datetime.now(UTC)},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}
