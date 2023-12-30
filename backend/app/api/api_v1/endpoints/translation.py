from fastapi import APIRouter, HTTPException, status

from app import crud, schemas
from app.api.dependencies import DatabaseDep

router = APIRouter()


@router.patch("/{translation_id}")
async def update_read_status(
    db: DatabaseDep, translation_id: int, request: schemas.TranslationUpdate
) -> None:
    translation = await crud.translation.get(db=db, id=translation_id)
    if translation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Translation w/ id {translation_id} does not exist",
        )

    await crud.translation.update(db=db, db_obj=translation, obj_in=request)
    await db.commit()
