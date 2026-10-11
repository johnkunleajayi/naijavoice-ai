import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.translation.dependencies import get_translation_service
from app.modules.translation.remote import RemoteTranslationEngine
from app.modules.translation.service import TranslationService

ENGLISH = "I want to write in Yoruba very well."
YORUBA = "Mo fẹ́ kọ̀wé lédè Yorùbá dáadáa."
UNAVAILABLE = {"detail": "Translation is not available right now. Please try again later."}


def post_translation(handler, payload=None):
    app = create_app()
    engine = RemoteTranslationEngine("https://inference.example/", transport=httpx.MockTransport(handler))
    app.dependency_overrides[get_translation_service] = lambda: TranslationService(engine)
    with TestClient(app) as client:
        return client.post("/api/translate", json={"text": ENGLISH} if payload is None else payload)


def test_translation_utf8_and_marked_output_is_unchanged():
    calls = []

    def handler(request):
        calls.append(request.url.path)
        assert request.url.path == "/translate"
        assert request.method == "POST"
        assert json.loads(request.content.decode("utf-8")) == {"text": ENGLISH}
        assert request.headers["content-type"] == "application/json; charset=utf-8"
        assert request.headers["accept"] == "application/json"
        assert request.headers["ngrok-skip-browser-warning"] == "true"
        assert request.extensions["timeout"]["connect"] == 5.0
        assert request.extensions["timeout"]["read"] == 60.0
        return httpx.Response(200, content=json.dumps({"text": YORUBA}, ensure_ascii=False).encode("utf-8"))

    response = post_translation(handler)
    assert response.status_code == 200
    assert response.json() == {"text": YORUBA}
    assert YORUBA.encode("utf-8") in response.content
    assert calls == ["/translate"]


def test_unicode_input_is_sent_as_utf8_and_output_is_not_normalized():
    text = "Translate ‘hello’ for Adé."
    translated = "  Ẹ Ọ!  "

    def handler(request):
        assert text.encode("utf-8") in request.content
        return httpx.Response(200, json={"text": translated})

    response = post_translation(handler, {"text": text})
    assert response.json() == {"text": translated}


@pytest.mark.parametrize("error", [httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError, httpx.RemoteProtocolError])
def test_network_errors_return_sanitized_503(error):
    def handler(request):
        raise error("private upstream info", request=request)

    response = post_translation(handler)
    assert response.status_code == 503
    assert response.json() == UNAVAILABLE


@pytest.mark.parametrize("status", [201, 302, 400, 422, 500, 503])
def test_non_200_returns_sanitized_503(status):
    response = post_translation(lambda request: httpx.Response(status, text="private upstream info"))
    assert response.status_code == 503
    assert response.json() == UNAVAILABLE


@pytest.mark.parametrize("body", [b"not json", b"\xff", b"null", b"[]", b"{}", b'{"text":null}', b'{"text":42}', b'{"text":[]}', b'{"text":""}', b'{"text":"   "}'])
def test_invalid_response_returns_sanitized_503(body):
    response = post_translation(lambda request: httpx.Response(200, content=body))
    assert response.status_code == 503
    assert response.json() == UNAVAILABLE


@pytest.mark.parametrize("payload", [{}, {"text": ""}, {"text": " \n\t"}, {"text": None}, {"text": 42}, {"text": "x" * 5001}])
def test_invalid_input_is_rejected_without_remote_call(payload):
    def handler(request):
        pytest.fail("Invalid input must not be forwarded")

    assert post_translation(handler, payload).status_code == 422


def test_reuses_configured_inference_url(monkeypatch):
    monkeypatch.setenv("TTS_INFERENCE_URL", "https://shared.example/")
    service = get_translation_service()
    assert isinstance(service.engine, RemoteTranslationEngine)
    assert service.engine.base_url == "https://shared.example"


def test_missing_inference_url_returns_503():
    with TestClient(create_app()) as client:
        response = client.post("/api/translate", json={"text": ENGLISH})
    assert response.status_code == 503
    assert response.json() == UNAVAILABLE
