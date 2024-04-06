from __future__ import annotations

from pydantic import BaseModel, StringConstraints
from typing import Annotated
from enum import Enum

from app.schemas.email_type import CustomEmailStr

# if TYPE_CHECKING:
# from .user import UserRequestModel, UserOut
# from .message import MessageResponse


class Method(str, Enum):
    REMOVE = "remove"
    ADD = "add"


class ConversationCreate(BaseModel):
    conversation_name: Annotated[str, StringConstraints(max_length=255)] | None = None
    user_ids: list[CustomEmailStr]
    is_group_chat: bool


class ConversationCreateDB(BaseModel):
    """Input Schema for function Conversation.Create"""

    conversation_name: Annotated[str, StringConstraints(max_length=255)] | None
    is_group_chat: bool
    chat_identifier: Annotated[str, StringConstraints(max_length=64)]
    # latest_message_id: int
    # members: list[UserOut]


class ConversationUpdate(BaseModel):
    conversation_name: Annotated[str, StringConstraints(max_length=255)] | None = None
    conversation_photo: Annotated[str, StringConstraints(max_length=255)] | None = None


class ConversationMemberUpdate(BaseModel):
    method: Method
    user_ids: list[CustomEmailStr]
    sorted_ids: list[int]
