from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from app.api.router import api_router


def create_app() -> FastAPI:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    application = FastAPI(title="NaijaVoice AI", version="0.1.0")
    application.include_router(api_router)
    return application


app = create_app()
