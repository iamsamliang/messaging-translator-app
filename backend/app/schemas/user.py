from pydantic import BaseModel, EmailStr, ConfigDict, StringConstraints
from typing import Annotated, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .message import MessageResponse
    from .conversation import ConversationResponse


# shared for create and read (schema not needed for read though)
class UserBase(BaseModel):
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
    target_language: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ]
    is_admin: bool = False


class UserCreate(UserBase):
    """Input Schema for function User.Create"""

    password: str


class UserUpdate(BaseModel):
    """Input Schema for function User.Update"""

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
    ] | None = None
    is_admin: bool | None = None
    password: str | None = None


class UserInDB(UserBase):
    """Input Schema for Database in function User.Create"""

    # user_id may not be created
    password_hash: str


class UserOut(UserBase):
    """Output Schema for any function returning User object"""

    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

    messages_sent: list["MessageResponse"] = []
    # messages_received: list["MessageOut"] = []
    conversations: list["ConversationResponse"] = []


class UserRequestModel(BaseModel):
    email: EmailStr
