import logging

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field, field_validator

from voxcpm_service.config import Settings
from voxcpm_service.engine import InferenceUnavailableError, VoxCPM2Engine

logger = logging.getLogger(__name__)


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)

    @field_validator("text")
    @classmethod
    def reject_blank(cls, text: str) -> str:
        if not text.strip():
            raise ValueError("Text must not be blank")
        return text


def create_app(engine: VoxCPM2Engine | None = None) -> FastAPI:
    app = FastAPI(title="NaijaVoice VoxCPM2 inference", version="0.1.0")
    provider = engine if engine is not None else VoxCPM2Engine(Settings.from_env())

    @app.get("/health")
    def health():
        # Liveness only: this does not load or verify the GPU model.
        return {"status": "ok", "model_loaded": provider.loaded}

    @app.post("/tts", response_class=Response, responses={
        200: {"content": {"audio/wav": {}}, "description": "Generated WAV"},
        503: {"description": "Inference unavailable"},
    })
    def tts(request: TTSRequest) -> Response:
        try:
            audio = provider.synthesize(request.text)
        except InferenceUnavailableError:
            logger.exception("VoxCPM2 generation failed")
            raise HTTPException(503, "Speech generation is unavailable.") from None
        return Response(audio, media_type="audio/wav")

    return app


app = create_app()
