import io
import wave

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.tts.dependencies import get_tts_engine
from app.modules.tts.engine import EngineUnavailableError


def make_wav():
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(24000)
        audio.writeframes(b"\x00\x00" * 24)
    return output.getvalue()


class FakeEngine:
    def __init__(self):
        self.calls = []
        self.audio = make_wav()

    def synthesize(self, text, language):
        self.calls.append((text, language))
        return self.audio


@pytest.fixture
def client_and_engine():
    app = create_app()
    engine = FakeEngine()
    app.dependency_overrides[get_tts_engine] = lambda: engine
    with TestClient(app) as client:
        yield client, engine


def test_tts_returns_audio_and_normalizes_before_engine(client_and_engine):
    client, engine = client_and_engine
    response = client.post("/api/tts", json={"text": "Ẹ káàárọ̀, Ọrẹ́!", "language": "yo"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content == engine.audio
    assert engine.calls == [("ẹ káàárọ̀, ọrẹ́!", "yo")]


def test_lowercase_request(client_and_engine):
    client, engine = client_and_engine
    response = client.post("/api/tts", json={"text": "ẹ káàárọ̀", "language": "yo"})
    assert response.status_code == 200
    assert engine.calls == [("ẹ káàárọ̀.", "yo")]


@pytest.mark.parametrize("payload", [
    {"text": "hello", "language": "ig"},
    {"text": "hello", "language": "ha"},
    {"text": "hello", "language": "YO"},
    {"text": "", "language": "yo"},
    {"text": " \n\t", "language": "yo"},
    {"text": "x" * 5001, "language": "yo"},
    {"text": 123, "language": "yo"},
    {"text": None, "language": "yo"},
    {"language": "yo"},
    {"text": "hello"},
    {},
])
def test_invalid_request_never_calls_engine(client_and_engine, payload):
    client, engine = client_and_engine
    assert client.post("/api/tts", json=payload).status_code == 422
    assert engine.calls == []


def test_maximum_length_is_accepted(client_and_engine):
    client, engine = client_and_engine
    assert client.post("/api/tts", json={"text": "Ẹ" * 5000, "language": "yo"}).status_code == 200
    assert engine.calls == [("ẹ" * 5000 + ".", "yo")]


def test_unconfigured_engine_returns_503():
    with TestClient(create_app()) as client:
        response = client.post("/api/tts", json={"text": "ẹ káàárọ̀", "language": "yo"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Speech generation is not available yet."}


def test_engine_unavailable_error_is_sanitized():
    class UnavailableEngine:
        def synthesize(self, text, language):
            raise EngineUnavailableError("Private model path or configuration")

    app = create_app()
    app.dependency_overrides[get_tts_engine] = UnavailableEngine
    with TestClient(app) as client:
        response = client.post("/api/tts", json={"text": "Ẹ", "language": "yo"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Speech generation is not available yet."}
