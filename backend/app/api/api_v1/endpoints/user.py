from typing import Annotated
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Response,
    Form,
)
from sqlalchemy.exc import IntegrityError

from app import crud, models, schemas
from app.api.dependencies import (
    DatabaseDep,
    verify_current_user_factory,
    verify_current_user_w_cookie,
)
from app.core.security import VerifyType
from app.exceptions import UserAlreadyExistsException


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
    ]
) -> models.User:
    return current_user


@router.post(
    "", response_model=schemas.UserCreateOut, status_code=status.HTTP_201_CREATED
)
async def create_user(
    db: DatabaseDep,
    user_in: schemas.UserCreate,
    response: Response,
) -> models.User:
    try:
        user_in.first_name = user_in.first_name.title()
        user_in.last_name = user_in.last_name.title()

        user = await crud.user.create(db=db, obj_in=user_in)
        await db.commit()
        response.headers["Location"] = f"/users/me/default"
        return user
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserAlreadyExistsException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )


@router.patch("/update")
async def update_user(
    db: DatabaseDep,
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
