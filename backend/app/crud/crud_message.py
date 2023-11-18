from app.models import Message
from app.schemas import MessageCreate, MessageUpdate

from .base import CRUDBase


class CRUDMessage(CRUDBase[Message, MessageCreate, MessageUpdate]):
    pass


message = CRUDMessage(Message)
