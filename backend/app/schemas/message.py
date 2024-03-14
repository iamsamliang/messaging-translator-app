from __future__ import annotations

from pydantic import BaseModel, StringConstraints
from typing import Annotated
from datetime import datetime

# if TYPE_CHECKING:
#     from .conversation import ConversationResponse
#     from .translation import TranslationResponse

# no schema for read because can only get a message by it's ID (only unique identifier)


class MessageCreate(BaseModel):
    """Input Schema for function Message.Create"""

    conversation_id: int
    sender_id: int
    original_text: str
    orig_language: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=100)
    ]


class MessageUpdate(BaseModel):
    """Input Schema for function Message.Update"""

    received_at: datetime
