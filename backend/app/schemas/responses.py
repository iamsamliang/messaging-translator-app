from typing import Annotated
from pydantic import EmailStr, ConfigDict, BaseModel, StringConstraints
from datetime import datetime
from .user import UserBase


class TranslationResponse(BaseModel):
    pass


class UserOut(UserBase):
    """Output Schema for any function returning User object"""

    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

    # messages_sent: list["MessageResponse"] = []
    # # messages_received: list["MessageOut"] = []
    # conversations: list["ConversationResponse"] = []


class UserRequestModel(BaseModel):
    email: EmailStr


class MessageResponse(BaseModel):
    """Output Schema for returning a Message object"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    sender_id: int
    # receiver_id: int
    # original_text: str
    # orig_language: Annotated[
    #     str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    # ]
    # conversation: "ConversationResponse"
    # translations: list["TranslationResponse"]


class ConversationResponse(BaseModel):
    """Output Schema for any function returning Conversation object"""

    model_config = ConfigDict(from_attributes=True)

    id: int

    # need forward references for type hints to avoid NameErrors and help circular importd
    conversation_name: Annotated[str, StringConstraints(max_length=255)]
    # messages: list[MessageResponse] = []
    # members: list[UserOut] = []
