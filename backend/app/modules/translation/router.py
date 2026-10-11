from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.modules.translation.dependencies import get_translation_service
from app.modules.translation.schemas import TranslationRequest, TranslationResponse
from app.modules.translation.service import TranslationService, TranslationUnavailableError

router = APIRouter(tags=["translation"])


@router.post(
    "/translate",
    response_model=TranslationResponse,
    responses={503: {"description": "Translation service unavailable"}},
)
def translate_english_to_yoruba(
    request: TranslationRequest,
    service: Annotated[TranslationService, Depends(get_translation_service)],
) -> TranslationResponse:
    try:
        translated = service.translate(request.text)
    except TranslationUnavailableError:
        raise HTTPException(
            status_code=503, detail="Translation is not available right now. Please try again later."
        ) from None
    return TranslationResponse(text=translated)
