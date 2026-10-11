import os

from app.modules.translation.remote import RemoteTranslationEngine
from app.modules.translation.service import TranslationService


def get_translation_service() -> TranslationService:
    return TranslationService(RemoteTranslationEngine(os.getenv("TTS_INFERENCE_URL", "")))
