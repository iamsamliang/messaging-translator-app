from typing import Annotated
from pydantic import ConfigDict, BaseModel, StringConstraints, field_validator
from datetime import datetime
from pydantic.functional_serializers import PlainSerializer

from app.schemas.email_type import CustomEmailStr


class TranslationResponse(BaseModel):
    pass


class UserCreateOut(BaseModel):
    # model_config = ConfigDict(from_attributes=True)
    id: int
    cookie_expire_secs: int


class MembersOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: Annotated[str, StringConstraints(strip_whitespace=True)]
    last_name: Annotated[str, StringConstraints(strip_whitespace=True)]
    profile_photo: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=4096)] | None
    )
    email: CustomEmailStr
    target_language: Annotated[str, StringConstraints(strip_whitespace=True)]
    is_admin: bool
    presigned_url: str | None


class UserOut(BaseModel):
    """Output Schema for any function returning User object"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: Annotated[str, StringConstraints(strip_whitespace=True)]
    last_name: Annotated[str, StringConstraints(strip_whitespace=True)]
    profile_photo: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=4096)] | None
    )
    email: CustomEmailStr
    target_language: Annotated[str, StringConstraints(strip_whitespace=True)]
    is_admin: bool
    created_at: datetime

    @field_validator("target_language")
    @classmethod
    def capitalize_language(cls, v: str) -> str:
        return v.title()


class UserOutExtraInfo(UserOut):
    presigned_url: str | None
    top_n_convos: list["ConversationResponse"]


class MessageResponse(BaseModel):
    """Output Schema for returning a Message object"""

    model_config = ConfigDict(from_attributes=True)

    conversation_id: int
    sender_id: int
    original_text: str
    orig_language: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ]
    sent_at: Annotated[
        datetime,
        PlainSerializer(
            lambda v: v.isoformat() + ("Z" if v.utcoffset() is None else ""),
            return_type=str,
        ),
    ]

    # sender name
    sender_name: str | None
    display_photo: bool

    # translations: list["TranslationResponse"]


class LatestMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    sender_id: int
    sent_at: Annotated[
        datetime,
        PlainSerializer(
            lambda v: v.isoformat() + ("Z" if v.utcoffset() is None else ""),
            return_type=str,
        ),
    ]
    relevant_translation: str | None = None
    translation_id: int | None = None
    is_read: int | None = None


class ExistingConversationResponse(BaseModel):
    existing_id: int


class ConversationResponse(BaseModel):
    """Output Schema for any function returning Conversation object"""

    model_config = ConfigDict(from_attributes=True)

    id: int

    conversation_name: Annotated[str, StringConstraints(max_length=255)]
    latest_message: LatestMessageResponse | None = None

    is_group_chat: bool
    presigned_url: str | None
    # messages: list[MessageResponse] = []


class GetMembersResponse(BaseModel):
    members: dict[int, MembersOut]
    sorted_member_ids: list[int]
    gc_url: str | None


UserOutExtraInfo.model_rebuild()
