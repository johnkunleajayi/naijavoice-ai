from fastapi import APIRouter
from app.modules.health.router import router as health_router
from app.modules.tts.router import router as tts_router

from app.modules.translation.router import router as translation_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(tts_router)
api_router.include_router(translation_router)
