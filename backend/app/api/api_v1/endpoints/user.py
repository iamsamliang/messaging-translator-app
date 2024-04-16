from typing import Annotated
from datetime import datetime
import secrets

from app.schemas.email_type import CustomEmailStr
from app.utils.aws import generate_presigned_get_url
from redis.asyncio import Redis
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    status,
    Response,
    Form,
)
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app import crud, models, schemas
from app.api.dependencies import (
    DatabaseDep,
    verify_current_user_factory,
    verify_current_user_w_cookie,
)
from app.utils.email import (
    send_account_verification_email,
    verify_verification_token,
    send_reset_password_email,
    verify_reset_password_token,
)
from app.core.security import VerifyType
from app.exceptions import UserAlreadyExistsException
from app.core.config import settings


router = APIRouter()


# Users
@router.get("/me/default", response_model=schemas.UserOut)
async def get_me_default(
    current_user: Annotated[
        models.User, Depends(verify_current_user_factory(type=VerifyType.DEFAULT))
    ]
) -> models.User:
    return current_user


@router.get("/me/extra-info", response_model=schemas.UserOutExtraInfo)
async def get_me_extra_info(
    current_user: Annotated[
        models.User, Depends(verify_current_user_factory(type=VerifyType.EXTRA_INFO))
    ],
    request: Request,
) -> models.User:
    websocket_token_val = secrets.token_urlsafe(64)
    setattr(current_user, "websocket_token", websocket_token_val)

    # set websocket token val in a Redis cache with a TTL of 3 min
    redis_client: Redis = request.app.state.redis_client
    await redis_client.set(
        current_user.email,
        websocket_token_val,
        ex=(settings.WEBSOCKET_ACCESS_TOKEN_EXPIRE_SECS),
    )

    return current_user


@router.post(
    "", response_model=schemas.UserCreateOut, status_code=status.HTTP_201_CREATED
)
async def create_user(
    db: DatabaseDep,
    user_in: schemas.UserCreate,
    response: Response,
    background_tasks: BackgroundTasks,
) -> schemas.UserCreateOut:
    try:
        user_in.first_name = user_in.first_name.title()
        user_in.last_name = user_in.last_name.title()

        user = await crud.user.create(db=db, obj_in=user_in)
        await db.commit()
        response.headers["Location"] = f"/users/me/default"

        # Send Account Verification Email Here
        await send_account_verification_email(
            new_user_email=user.email, background_tasks=background_tasks
        )

        return schemas.UserCreateOut(
            id=user.id,
            cookie_expire_secs=settings.ACCOUNT_VERIFICATION_TOKEN_EXPIRE_HOURS
            * 60
            * 60,
        )
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserAlreadyExistsException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )


@router.get("/resend-verify-email")
async def resend_verification_email(
    email: CustomEmailStr, background_tasks: BackgroundTasks
) -> JSONResponse:
    await send_account_verification_email(
        new_user_email=email, background_tasks=background_tasks
    )
    return JSONResponse(
        {
            "message": "A verification link has been sent to your email. Remember to check your spam if it's not in your inbox."
        }
    )


@router.post("/verify-account")
async def verify_user_account(
    db: DatabaseDep, request_data: schemas.VerificationPayLoad
) -> JSONResponse:
    await verify_verification_token(db=db, verification_token=request_data.token)
    return JSONResponse({"message": "Your account has been successfully verified."})


@router.post("/forgot-password")
async def forgot_password(
    db: DatabaseDep,
    email: Annotated[CustomEmailStr, Form()],
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    req_response = JSONResponse(
        {
            "message": "A password reset link has been sent to your email. Remember to check your spam if it's not in your inbox."
        }
    )

    user = await crud.user.get_by_email(db=db, email=email)
    if user is None:
        return req_response

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Please verify your account.",
        )

    await send_reset_password_email(
        email=email, curr_pw=user.password_hash, background_tasks=background_tasks
    )
    return req_response


@router.post("/reset-password")
async def reset_password(
    db: DatabaseDep, token: Annotated[str, Form()], password: Annotated[str, Form()]
) -> JSONResponse:
    await verify_reset_password_token(db=db, reset_token=token, new_password=password)
    return JSONResponse({"message": "Your password has been changed."})


@router.patch("/update")
async def update_user(
    db: DatabaseDep,
    request: Request,
    user: Annotated[models.User, Depends(verify_current_user_w_cookie)],
    firstname: Annotated[str | None, Form(max_length=100)] = None,
    lastname: Annotated[str | None, Form(max_length=100)] = None,
    email: Annotated[str | None, Form()] = None,
    language: Annotated[str | None, Form(max_length=100)] = None,
    password: Annotated[str | None, Form()] = None,
    profilePhoto: Annotated[str | None, Form(max_length=4096)] = None,
    apiKey: Annotated[str | None, Form(max_length=255)] = None,
) -> dict[str, str]:
    try:
        form_data = {
            key: value
            for key, value in {
                "first_name": firstname,
                "last_name": lastname,
                "profile_photo": profilePhoto,
                "email": email,
                "target_language": language,
                "api_key": apiKey,
            }.items()
            if value is not None
        }

        if password:
            user_update = schemas.UserUpdate(**form_data, password=password, pwd_changed=datetime.utcnow())  # type: ignore
        else:
            user_update = schemas.UserUpdate(**form_data)  # type: ignore

        if user_update.first_name:
            user_update.first_name = user_update.first_name.title()

        if user_update.last_name:
            user_update.last_name = user_update.last_name.title()

        await crud.user.update(db=db, db_obj=user, obj_in=user_update)

        await db.commit()

        # generate new presigned GET and replace it in cache. Necessary so frontend
        # fetches the new photo instead of using cached one
        if user.profile_photo:
            _ = await generate_presigned_get_url(
                bucket_name=settings.S3_BUCKET_NAME,
                object_key=user.profile_photo,
                expire_in_secs=settings.S3_PRESIGNED_URL_GET_EXPIRE_SECS,
                redis_client=request.app.state.redis_client,
            )

        return form_data
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/delete",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    db: DatabaseDep, user: Annotated[models.User, Depends(verify_current_user_w_cookie)]
) -> None:
    try:
        await crud.user.delete(db=db, id=user.id)
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
