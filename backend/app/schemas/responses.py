from typing import Annotated
from pydantic import ConfigDict, BaseModel, StringConstraints
from datetime import datetime
from pydantic.functional_serializers import PlainSerializer
from .user import UserBase


class TranslationResponse(BaseModel):
    pass


class UserCreateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int


class UserOut(UserBase):
    """Output Schema for any function returning User object"""

    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

    # messages_sent: list["MessageResponse"] = []
    # # messages_received: list["MessageOut"] = []
    conversations: list["ConversationResponse"] = []


class MessageResponse(BaseModel):
    """Output Schema for returning a Message object"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    sender_id: int
    # receiver_id: int
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
    # sent_at: datetime
    # conversation: "ConversationResponse"
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
    relevant_translation: str
    translation_id: int
    is_read: int


class ConversationResponse(BaseModel):
    """Output Schema for any function returning Conversation object"""

    model_config = ConfigDict(from_attributes=True)

    id: int

    # need forward references for type hints to avoid NameErrors and help circular importd
    conversation_name: Annotated[str, StringConstraints(max_length=255)]
    latest_message: LatestMessageResponse | None = None
    # messages: list[MessageResponse] = []
    # members: list[UserOut] = []


UserOut.model_rebuild()
