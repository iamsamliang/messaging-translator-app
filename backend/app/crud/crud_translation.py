# what happens when the user changes their language?
# we start from scratch unless someone else in the group chat has been using the user's new language
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Translation
from app.schemas import TranslationCreate, TranslationUpdate
from .base import CRUDBase


class CRUDTranslation(CRUDBase[Translation, TranslationCreate, TranslationUpdate]):
    # async def get_translations_by_userid_convoids(
    #     self, db: AsyncSession, user_id: int, convo_id: list[int]
    # ) -> list[]:
    #     latest_message_ids = [conversation.latest_message.id for conversation in user.conversations]
    pass


translation = CRUDTranslation(Translation)
