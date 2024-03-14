from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app import crud, schemas, models
from app.api.dependencies import DatabaseDep, verify_current_user_w_cookie

router = APIRouter()


@router.patch("/{translation_id}")
async def update_read_status(
    db: DatabaseDep,
    translation_id: int,
    request: schemas.TranslationUpdate,
    _: Annotated[models.User, Depends(verify_current_user_w_cookie)],
) -> None:
    try:
        translation = await crud.translation.get(db=db, id=translation_id)
        if translation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Translation w/ id {translation_id} does not exist",
            )

        await crud.translation.update(db=db, db_obj=translation, obj_in=request)
        await db.commit()
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
