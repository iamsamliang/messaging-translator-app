from pydantic import BaseModel, ConfigDict, StringConstraints
from typing import Annotated
from datetime import datetime

from .conversation import ConversationOut

# no schema for read because can only get a message by it's ID (only unique identifier)


class MessageBase(BaseModel):
    conversation_id: int
    sender_id: int
    receiver_id: int
    original_text: str
    translated_text: str
    orig_language: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ]


class MessageCreate(MessageBase):
    """Input Schema for function Message.Create"""

    pass


class MessageUpdate(BaseModel):
    """Input Schema for function Message.Update"""

    received_at: datetime


class MessageOut(MessageBase):
    """Output Schema for returning a Message object"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int | None = None
    sender_id: int | None = None
    # receiver_id: int | None = None
    original_text: str | None = None
    translated_text: str | None = None
    orig_language: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ] | None = None
    conversations: list[ConversationOut] = []
