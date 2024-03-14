from __future__ import annotations

from pydantic import BaseModel, EmailStr, StringConstraints
from typing import Annotated
from enum import Enum

# if TYPE_CHECKING:
# from .user import UserRequestModel, UserOut
# from .message import MessageResponse


class Method(str, Enum):
    REMOVE = "remove"
    ADD = "add"


class ConversationCreate(BaseModel):
    conversation_name: Annotated[str, StringConstraints(max_length=255)] | None = None
    user_ids: list[EmailStr]
    is_group_chat: bool


class ConversationCreateDB(BaseModel):
    """Input Schema for function Conversation.Create"""

    conversation_name: Annotated[str, StringConstraints(max_length=255)] | None
    is_group_chat: bool
    # latest_message_id: int
    # members: list[UserOut]


class ConversationUpdate(BaseModel):
    conversation_name: Annotated[str, StringConstraints(max_length=255)] | None = None
    conversation_photo: Annotated[str, StringConstraints(max_length=255)] | None = None


class ConversationMemberUpdate(BaseModel):
    method: Method
    user_ids: list[EmailStr]
    sorted_ids: list[int]


# class ConversationMessageUpdate(BaseModel):
#     new_latest_msg_id: int
