from pydantic import BaseModel, ConfigDict, StringConstraints
from typing import Annotated, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .user import UserRequestModel, UserOut
    from .message import MessageResponse


class Method(str, Enum):
    REMOVE = "remove"
    ADD = "add"


class ConversationCreate(BaseModel):
    conversation_name: Annotated[str, StringConstraints(max_length=255)]
    user_ids: list["UserRequestModel"]


class ConversationCreateDB(BaseModel):
    """Input Schema for function Conversation.Create"""

    model_config = ConfigDict(from_attributes=True)

    conversation_name: Annotated[str, StringConstraints(max_length=255)]
    members: list["UserOut"]


class ConversationNameUpdate(BaseModel):
    conversation_name: Annotated[str, StringConstraints(max_length=255)]


class ConversationMemberUpdate(BaseModel):
    method: Method
    user_ids: list["UserRequestModel"]


class ConversationResponse(BaseModel):
    """Output Schema for any function returning Conversation object"""

    model_config = ConfigDict(from_attributes=True)

    id: int

    # need forward references for type hints to avoid NameErrors and help circular importd
    conversation_name: Annotated[str, StringConstraints(max_length=255)]
    messages: list["MessageResponse"] = []
    members: list["UserOut"] = []
