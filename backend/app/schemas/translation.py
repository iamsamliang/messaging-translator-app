from __future__ import annotations

from typing import Annotated, TYPE_CHECKING
from pydantic import BaseModel, StringConstraints

# if TYPE_CHECKING:
#     from .user import UserOut


class TranslationCreate(BaseModel):
    translation: str
    language: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ]
    target_user_id: int
    message_id: int


class TranslationUpdate(BaseModel):
    translation: str | None
    language: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ] | None
    target_user_id: int | None
    message_id: int | None
