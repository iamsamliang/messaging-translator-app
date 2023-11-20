# what happens when the user changes their language?
# we start from scratch unless someone else in the group chat has been using the user's new language
from app.models import Translation
from app.schemas import TranslationCreate, TranslationUpdate
from .base import CRUDBase


class CRUDTranslation(CRUDBase[Translation, TranslationCreate, TranslationUpdate]):
    pass


translation = CRUDTranslation(Translation)
