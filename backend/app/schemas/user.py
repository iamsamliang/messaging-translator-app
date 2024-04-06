from __future__ import annotations

from pydantic import BaseModel, StringConstraints
from typing import Annotated

from datetime import datetime

from app.schemas.email_type import CustomEmailStr

# if TYPE_CHECKING:
#     from .message import MessageResponse
#     from .conversation import ConversationResponse


# shared for create and read (schema not needed for read though)
class UserBase(BaseModel):
    first_name: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ]
    last_name: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ]
    profile_photo: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=4096)] | None
    ) = None
    email: CustomEmailStr
    target_language: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ]
    is_admin: bool = False
    api_key: Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]


class UserCreate(UserBase):
    """Input Schema for function User.Create"""

    password: str


class UserUpdate(BaseModel):
    """Input Schema for function User.Update"""

    first_name: (
        Annotated[
            str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
        ]
        | None
    ) = None
    last_name: (
        Annotated[
            str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
        ]
        | None
    ) = None
    profile_photo: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=4096)] | None
    ) = None
    email: CustomEmailStr | None = None
    target_language: (
        Annotated[
            str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
        ]
        | None
    ) = None
    is_admin: bool | None = None
    password: str | None = None
    pwd_changed: datetime | None = None
    api_key: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)] | None
    ) = None


# class UserInDB(UserBase):
#     """Input Schema for Database in function User.Create"""

#     # user_id may not be created
#     password_hash: str
