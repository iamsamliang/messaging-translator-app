from pydantic import BaseModel, EmailStr, ConfigDict, StringConstraints
from typing import Annotated
from datetime import datetime

from .message import MessageOut
from .conversation import ConversationOut


# shared for create and read (schema not needed for read though)
class UserBase(BaseModel):
    first_name: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ] | None = None
    last_name: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ] | None = None
    profile_photo: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=255)
    ] | None = None
    email: EmailStr | None = None
    target_language: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ] = None
    is_admin: bool | None = None


class UserCreate(UserBase):
    """Input Schema for function User.Create"""

    first_name: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ]
    last_name: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ]
    profile_photo: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=255)
    ]
    email: EmailStr
    password: str
    target_language: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ]
    is_admin: bool = False


class UserUpdate(UserBase):
    """Input Schema for function User.Update"""

    password: str | None = None


class UserInDB(UserBase):
    """Input Schema for Database in function User.Create"""

    # user_id may not be created
    password_hash: str


class UserOut(UserBase):
    """Output Schema for any function returning User object"""

    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime | None = None

    messages_sent: list[MessageOut] = []
    # messages_received: list[MessageOut] = []
    conversations: list[ConversationOut] = []


class UserRequestModel(BaseModel):
    email: EmailStr
