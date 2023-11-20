from pydantic import BaseModel, ConfigDict, StringConstraints
from typing import Annotated
from enum import Enum

from app.models import User
from .message import MessageResponse
from .user import UserOut, UserRequestModel


class Method(str, Enum):
    REMOVE = "remove"
    ADD = "add"


class ConversationCreate(BaseModel):
    conversation_name: Annotated[str, StringConstraints(max_length=255)]
    user_ids: list[UserRequestModel]


class ConversationCreateDB(BaseModel):
    """Input Schema for function Conversation.Create"""

    conversation_name: Annotated[str, StringConstraints(max_length=255)]
    members: list[User]


class ConversationNameUpdate(BaseModel):
    conversation_name: Annotated[str, StringConstraints(max_length=255)]


class ConversationMemberUpdate(BaseModel):
    method: Method
    user_ids: list[UserRequestModel]


class ConversationResponse(BaseModel):
    """Output Schema for any function returning Conversation object"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_name: Annotated[str, StringConstraints(max_length=255)]
    messages: list[MessageResponse] = []
    members: list[UserOut] = []
