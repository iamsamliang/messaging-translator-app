from __future__ import annotations
from re import S

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints
from typing import Annotated, TYPE_CHECKING
from enum import Enum

# if TYPE_CHECKING:
# from .user import UserRequestModel, UserOut
# from .message import MessageResponse


class Method(str, Enum):
    REMOVE = "remove"
    ADD = "add"


class ConversationCreate(BaseModel):
    conversation_name: Annotated[str, StringConstraints(max_length=255)]
    user_ids: list[EmailStr]
    # latest_message_id: int


class ConversationCreateDB(BaseModel):
    """Input Schema for function Conversation.Create"""

    conversation_name: Annotated[str, StringConstraints(max_length=255)]
    # latest_message_id: int
    # members: list[UserOut]


class ConversationNameUpdate(BaseModel):
    conversation_name: Annotated[str, StringConstraints(max_length=255)]


class ConversationMemberUpdate(BaseModel):
    method: Method
    user_ids: list[EmailStr]


# class ConversationMessageUpdate(BaseModel):
#     new_latest_msg_id: int
