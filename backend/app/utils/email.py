from datetime import timedelta
from datetime import datetime
from app.core.security import hash_password
from app.schemas.email_type import CustomEmailStr
from jose import jwt, JWTError
from fastapi import BackgroundTasks, HTTPException, status
from app.core.config import settings
from app.core.email import send_email
from app import crud
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError


async def send_account_verification_email(
    new_user_email: str, background_tasks: BackgroundTasks
) -> None:
    # create a account verification token that I use as a query parameter
    # in my verifcation link that is sent in the email body
    # the token must include a expiration date, so I can check if the verification
    # link has expired or not
    acc_verification_token = generate_acc_verification_token(
        new_user_email=new_user_email
    )

    verification_url = (
        f"{settings.FRONTEND_HOST}/verify-account?token={acc_verification_token}"
    )
    subject = f"{settings.PROJECT_NAME} - Account Verification"
    template_body = {
        "project_name": settings.PROJECT_NAME,
        "verification_link": verification_url,
        "expire_hours": settings.ACCOUNT_VERIFICATION_TOKEN_EXPIRE_HOURS,
    }

    await send_email(
        recipients=[new_user_email],
        subject=subject,
        template_body=template_body,
        template_name="verify_account.html",
        background_tasks=background_tasks,
    )


def generate_acc_verification_token(new_user_email: str) -> str:
    delta = timedelta(hours=settings.ACCOUNT_VERIFICATION_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    encoded_jwt = jwt.encode(
        {"exp": expires, "nbf": now, "sub": new_user_email},
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    return encoded_jwt


async def verify_verification_token(db: AsyncSession, verification_token: str) -> None:
    invalid_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"The link is invalid or expired. You will need to create your account again if {settings.ACCOUNT_VERIFICATION_TOKEN_EXPIRE_HOURS} hours have passed.",
    )

    try:
        payload = jwt.decode(
            verification_token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
        )
        user_email = payload.get("sub")

        if user_email is None:
            raise invalid_exception

        user = await crud.user.get_by_email(db=db, email=user_email)

        if user is None:
            raise invalid_exception

        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already verified your account.",
            )

        user.is_verified = True
        await db.commit()  # db.add(user) not needed before this

    except JWTError:
        raise invalid_exception
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


async def send_reset_password_email(
    email: CustomEmailStr, curr_pw: str, background_tasks: BackgroundTasks
) -> None:
    token = generate_reset_password_token(email=email, curr_pw=curr_pw)
    reset_link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"

    subject = f"{settings.PROJECT_NAME} - Reset Password"
    template_body = {
        "project_name": settings.PROJECT_NAME,
        "reset_link": reset_link,
        "expire_minutes": settings.RESET_PASSWORD_TOKEN_EXPIRE_MINUTES,
    }

    await send_email(
        recipients=[email],
        subject=subject,
        template_body=template_body,
        template_name="reset_password.html",
        background_tasks=background_tasks,
    )


def generate_reset_password_token(email: CustomEmailStr, curr_pw: str) -> str:
    """
    One-time use JWT token
    """
    delta = timedelta(minutes=settings.RESET_PASSWORD_TOKEN_EXPIRE_MINUTES)
    now = datetime.utcnow()
    expires = now + delta

    token = jwt.encode(
        {"exp": expires, "nbf": now, "sub": email, "pw": curr_pw},
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    return token


async def verify_reset_password_token(
    db: AsyncSession, reset_token: str, new_password: str
) -> None:
    invalid_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"The link is invalid or expired.",
    )

    try:
        payload = jwt.decode(
            reset_token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
        )
        user_email = payload.get("sub")

        if user_email is None:
            raise invalid_exception

        user = await crud.user.get_by_email(db=db, email=user_email)

        if user is None:
            raise invalid_exception

        token_pw_hash = payload.get("pw")

        if user.password_hash != token_pw_hash:
            raise invalid_exception

        user.password_hash = hash_password(new_password)
        await db.commit()  # db.add(user) not needed before this

    except JWTError:
        raise invalid_exception
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
