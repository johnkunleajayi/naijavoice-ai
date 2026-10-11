from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from app.modules.tts.dependencies import get_tts_service
from app.modules.tts.engine import EngineUnavailableError
from app.modules.tts.schemas import TTSRequest
from app.modules.tts.service import TTSService

router = APIRouter(tags=["tts"])


@router.post(
    "/tts",
    response_class=Response,
    responses={
        200: {"description": "Generated WAV audio", "content": {"audio/wav": {}}},
        503: {"description": "Speech engine unavailable"},
    },
)
def synthesize_speech(
    request: TTSRequest,
    service: Annotated[TTSService, Depends(get_tts_service)],
) -> Response:
    try:
        audio = service.synthesize(request)
    except EngineUnavailableError:
        raise HTTPException(
            status_code=503, detail="Speech generation is not available yet."
        ) from None
    return Response(content=audio, media_type="audio/wav")
