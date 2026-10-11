from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.modules.tts.config import TTSSettings
from app.modules.tts.diacritization import PassthroughYorubaDiacritizer, YorubaDiacritizer
from app.modules.tts.preprocessing import YorubaPreprocessor
from app.modules.tts.engine import TTSEngine
from app.modules.tts.f5_yoruba import F5TTSYorubaEngine
from app.modules.tts.remote import RemoteTTSEngine
from app.modules.tts.remote_diacritization import RemoteYorubaDiacritizer
from app.modules.tts.service import TTSService


@lru_cache(maxsize=1)
def get_tts_engine() -> TTSEngine:
    # Configuration and adapter are cheap; no F5-TTS import or model load here.
    settings = TTSSettings.from_env()
    if settings.inference_url:
        return RemoteTTSEngine(settings.inference_url)
    return F5TTSYorubaEngine(settings)


def get_yoruba_diacritizer() -> YorubaDiacritizer:
    settings = TTSSettings.from_env()
    if settings.inference_url:
        return RemoteYorubaDiacritizer(settings.inference_url)
    return PassthroughYorubaDiacritizer()


def get_tts_service(
    engine: Annotated[TTSEngine, Depends(get_tts_engine)],
    diacritizer: Annotated[YorubaDiacritizer, Depends(get_yoruba_diacritizer)],
) -> TTSService:
    return TTSService(engine, YorubaPreprocessor(diacritizer))
