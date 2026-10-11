import io
import json
import wave

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.tts.config import TTSSettings
from app.modules.tts.dependencies import get_tts_engine
from app.modules.tts.remote import RemoteTTSEngine


def wav_bytes():
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(b"\x00\x00" * 24)
    return output.getvalue()


def post_with_transport(handler, payload=None):
    app = create_app()
    engine = RemoteTTSEngine("https://inference.example/", transport=httpx.MockTransport(handler))
    app.dependency_overrides[get_tts_engine] = lambda: engine
    with TestClient(app) as client:
        return client.post("/api/tts", json=payload or {"text": "Ẹ Ọ káàárọ̀", "language": "yo"})


def test_normalized_utf8_json_and_exact_wav_passthrough():
    audio = wav_bytes()

    def handler(request):
        assert str(request.url) == "https://inference.example/tts"
        assert request.method == "POST"
        assert json.loads(request.content.decode("utf-8")) == {"text": "ẹ ọ káàárọ̀."}
        assert "ẹ ọ".encode("utf-8") in request.content
        assert request.headers["content-type"] == "application/json; charset=utf-8"
        assert request.headers["ngrok-skip-browser-warning"] == "true"
        assert request.extensions["timeout"] == {"connect": 5.0, "read": 120.0, "write": 10.0, "pool": 5.0}
        return httpx.Response(200, content=audio, headers={"Content-Type": "audio/wav"})

    response = post_with_transport(handler)
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content == audio


@pytest.mark.parametrize("exception", [httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError, httpx.RemoteProtocolError])
def test_timeout_and_offline_service_return_clean_503(exception):
    def handler(request):
        raise exception("private upstream detail", request=request)

    response = post_with_transport(handler)
    assert response.status_code == 503
    assert response.json() == {"detail": "Speech generation is not available yet."}


@pytest.mark.parametrize("status", [201, 302, 400, 422, 500, 503])
def test_non_200_return_clean_503(status):
    response = post_with_transport(lambda request: httpx.Response(status, text="private upstream error"))
    assert response.status_code == 503
    assert response.json() == {"detail": "Speech generation is not available yet."}


@pytest.mark.parametrize("body", [b"", b"<html>ngrok warning</html>", b'{"error":"failed"}'])
def test_invalid_audio_returns_clean_503(body):
    response = post_with_transport(lambda request: httpx.Response(200, content=body))
    assert response.status_code == 503
    assert response.json() == {"detail": "Speech generation is not available yet."}


def test_unsupported_language_does_not_contact_remote():
    def handler(request):
        pytest.fail("Unsupported language must not reach remote inference")

    assert post_with_transport(handler, {"text": "hello", "language": "ig"}).status_code == 422


def test_environment_selects_remote_without_local_model(monkeypatch):
    monkeypatch.setenv("TTS_INFERENCE_URL", "https://inference.example")
    assert TTSSettings.from_env().inference_url == "https://inference.example"
    engine = get_tts_engine()
    assert isinstance(engine, RemoteTTSEngine)
    assert engine.url == "https://inference.example/tts"
    assert get_tts_engine() is engine


def test_dotenv_does_not_override_explicit_process_setting(monkeypatch):
    monkeypatch.setenv("TTS_INFERENCE_URL", "https://override.example")
    create_app()
    assert TTSSettings.from_env().inference_url == "https://override.example"
