from typing import Annotated
from pydantic import BaseModel, StringConstraints

from app.models import User


class TranslationCreate(BaseModel):
    translation: str
    language: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ]
    target_user_id: int
    message_id: int
    user: User


class TranslationUpdate(BaseModel):
    translation: str | None
    language: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ] | None
    target_user_id: int | None
    message_id: int | None


class TranslationResponse(BaseModel):
    pass
