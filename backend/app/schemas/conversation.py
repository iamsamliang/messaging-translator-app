from pydantic import BaseModel, ConfigDict, StringConstraints
from typing import Annotated

from app.models import User
from .message import MessageOut
from .user import UserOut, UserRequestModel


class ConversationBase(BaseModel):
    conversation_name: Annotated[str, StringConstraints(max_length=255)] | None = None


class ConversationCreate(ConversationBase):
    """Input Schema for function Conversation.Create"""

    conversation_name: Annotated[str, StringConstraints(max_length=255)]


class ConversationRequest(ConversationBase):
    id: int | None = None
    user_ids: list[UserRequestModel]


class ConversationUpdate(ConversationBase):
    """Input Schema for function Conversation.Update"""

    pass


class ConversationOut(ConversationBase):
    """Output Schema for any function returning Conversation object"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_name: Annotated[str, StringConstraints(max_length=255)]
    messages: list[MessageOut] = []
    members: list[UserOut] = []
