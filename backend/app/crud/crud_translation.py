from app.models import Translation
from app.schemas import TranslationCreate, TranslationUpdate
from .base import CRUDBase


class CRUDTranslation(CRUDBase[Translation, TranslationCreate, TranslationUpdate]):
    pass


translation = CRUDTranslation(Translation)
