from __future__ import annotations

from typing import Annotated
from pydantic import BaseModel, StringConstraints


class TranslationCreate(BaseModel):
    translation: str
    language: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ]
    target_user_id: int
    message_id: int
    is_read: int


class TranslationUpdate(BaseModel):
    is_read: int
