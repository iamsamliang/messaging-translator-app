from pydantic import BaseModel, EmailStr, ConfigDict, StringConstraints
from typing import Annotated
from datetime import datetime

from app.schemas import MessageResponse, ConversationResponse


# shared for create and read (schema not needed for read though)
class UserBase(BaseModel):
    first_name: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ] | None
    last_name: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ] | None
    profile_photo: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=255)
    ] | None
    email: EmailStr | None
    target_language: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ] | None
    is_admin: bool | None


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

    password: str | None


class UserInDB(UserBase):
    """Input Schema for Database in function User.Create"""

    # user_id may not be created
    password_hash: str


class UserOut(UserBase):
    """Output Schema for any function returning User object"""

    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime | None = None

    messages_sent: list[MessageResponse] = []
    # messages_received: list[MessageOut] = []
    conversations: list[ConversationResponse] = []


class UserRequestModel(BaseModel):
    email: EmailStr
