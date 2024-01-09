from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.exc import IntegrityError

from app import crud, models, schemas
from app.api.dependencies import DatabaseDep, verify_current_user
from app.exceptions import UserAlreadyExistsException


router = APIRouter()


# Users
@router.get("/me", response_model=schemas.UserOut)
async def get_me(
    current_user: Annotated[models.User, Depends(verify_current_user)]
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
        user = await crud.user.create(db=db, obj_in=user_in)
        await db.commit()
        response.headers["Location"] = f"/users/{user.id}"
        return user
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserAlreadyExistsException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )


@router.patch("/{user_id}", response_model=schemas.UserOut)
async def update_user(
    db: DatabaseDep,
    user_id: int,
    request: schemas.UserUpdate,
) -> models.User:
    try:
        curr_user = await crud.user.get(db=db, id=user_id)
        if curr_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User w/ id {user_id} doesn't exist",
            )
        res = await crud.user.update(db=db, db_obj=curr_user, obj_in=request)

        await db.commit()
        return res
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(db: DatabaseDep, user_id: int) -> None:
    try:
        res = await crud.user.delete(db=db, id=user_id)
        if res is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User w/ id {user_id} doesn't exist",
            )
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
