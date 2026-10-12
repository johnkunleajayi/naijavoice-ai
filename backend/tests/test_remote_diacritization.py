import json
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.tts.dependencies import get_tts_engine, get_yoruba_diacritizer
from app.modules.tts.diacritization import PassthroughYorubaDiacritizer
from app.modules.tts.remote import RemoteTTSEngine
from app.modules.tts.remote_diacritization import RemoteYorubaDiacritizer

RESTORED = "Mo fẹ́ kọ èdè Yorùbà dáadáa"


def endpoint(handler, text="Mo fe ko ede Yoruba daadaa"):
    app = create_app()
    engine = Mock()
    engine.synthesize.return_value = b"test WAV"
    adapter = RemoteYorubaDiacritizer("https://inference.example/", transport=httpx.MockTransport(handler))
    app.dependency_overrides[get_yoruba_diacritizer] = lambda: adapter
    app.dependency_overrides[get_tts_engine] = lambda: engine
    with TestClient(app) as client:
        response = client.post("/api/tts", json={"text": text, "language": "yo"})
    return response, engine


def test_unmarked_text_restored_then_normalized_and_sent_to_tts():
    calls = []

    def handler(request):
        calls.append(request)
        assert request.url.path == "/diacritize"
        assert request.method == "POST"
        assert json.loads(request.content.decode("utf-8")) == {"text": "Mo fe ko ede Yoruba daadaa"}
        assert request.headers["content-type"] == "application/json; charset=utf-8"
        assert request.headers["accept"] == "application/json"
        assert request.headers["ngrok-skip-browser-warning"] == "true"
        assert request.extensions["timeout"]["read"] == 60.0
        return httpx.Response(200, content=json.dumps({"text": RESTORED}, ensure_ascii=False).encode("utf-8"))

    response, engine = endpoint(handler, "  Mo fe ko ede Yoruba daadaa  ")
    assert response.status_code == 200
    assert len(calls) == 1
    engine.synthesize.assert_called_once_with(text=RESTORED + ".", language="yo")


def test_remote_adapter_sends_non_ascii_utf8_correctly():
    def handler(request):
        assert "ẹ".encode("utf-8") in request.content
        assert json.loads(request.content) == {"text": "ẹ"}
        return httpx.Response(200, json={"text": "ẹ́"})

    adapter = RemoteYorubaDiacritizer("https://inference.example", transport=httpx.MockTransport(handler))
    assert adapter.diacritize("ẹ") == "ẹ́"


@pytest.mark.parametrize("text", ["Mo fẹ́ kọ èdè Yorùbà dáadáa.", "Ẹ káàárọ̀!", "e\u0323\u0301?"])
def test_marked_input_never_calls_remote_diacritizer(text):
    def handler(request):
        pytest.fail("Marked input must bypass /diacritize")

    response, engine = endpoint(handler, text)
    assert response.status_code == 200
    engine.synthesize.assert_called_once_with(text=text.replace("Ẹ", "ẹ"), language="yo")


@pytest.mark.parametrize("exception", [httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError])
def test_network_failures_return_clean_503_without_tts(exception):
    def handler(request):
        raise exception("private upstream detail", request=request)

    response, engine = endpoint(handler)
    assert response.status_code == 503
    assert response.json() == {"detail": "Speech generation is not available yet."}
    engine.synthesize.assert_not_called()


@pytest.mark.parametrize("status", [201, 302, 422, 500, 503])
def test_non_200_returns_clean_503_without_tts(status):
    response, engine = endpoint(lambda request: httpx.Response(status, text="private error"))
    assert response.status_code == 503
    assert response.json() == {"detail": "Speech generation is not available yet."}
    engine.synthesize.assert_not_called()


@pytest.mark.parametrize("body", [b"not json", b"\xff", b"[]", b"null", b"{}", b'{"text":null}', b'{"text":12}', b'{"text":""}', b'{"text":"   "}'])
def test_invalid_response_returns_clean_503_without_tts(body):
    response, engine = endpoint(lambda request: httpx.Response(200, content=body))
    assert response.status_code == 503
    assert response.json() == {"detail": "Speech generation is not available yet."}
    engine.synthesize.assert_not_called()


def test_independent_base_url_configuration(monkeypatch):
    monkeypatch.setenv("TTS_INFERENCE_URL", "https://tts.example/")
    monkeypatch.setenv("TRANSLATION_INFERENCE_URL", "https://translation.example/")
    monkeypatch.setenv("DIACRITIZATION_INFERENCE_URL", "https://marks.example/")
    assert get_yoruba_diacritizer().url == "https://marks.example/diacritize"
    assert get_tts_engine().url == "https://tts.example/tts"


@pytest.mark.parametrize("url", ["", "   "])
def test_missing_diacritization_url_never_falls_back_to_tts(monkeypatch, url):
    monkeypatch.setenv("TTS_INFERENCE_URL", "https://tts.example/")
    monkeypatch.setenv("DIACRITIZATION_INFERENCE_URL", url)
    adapter = get_yoruba_diacritizer()
    assert isinstance(adapter, PassthroughYorubaDiacritizer)
    assert adapter.diacritize("Mo fe ko") == "Mo fe ko"
    assert get_tts_engine().url == "https://tts.example/tts"


def test_normalizes_restored_uppercase_whitespace_and_keeps_punctuation():
    response, engine = endpoint(lambda request: httpx.Response(200, json={"text": "  Ẹ Ọ!  "}))
    assert response.status_code == 200
    engine.synthesize.assert_called_once_with(text="ẹ ọ!", language="yo")


def test_two_remote_calls_are_ordered_and_return_wav():
    calls = []
    audio = b"RIFF" + b"1234" + b"WAVE" + b"test audio"

    def handler(request):
        calls.append(request.url.path)
        if request.url.path == "/diacritize":
            return httpx.Response(200, json={"text": RESTORED})
        assert request.url.path == "/tts"
        assert json.loads(request.content) == {"text": RESTORED + "."}
        return httpx.Response(200, content=audio)

    transport = httpx.MockTransport(handler)
    app = create_app()
    app.dependency_overrides[get_yoruba_diacritizer] = lambda: RemoteYorubaDiacritizer("https://inference.example", transport=transport)
    app.dependency_overrides[get_tts_engine] = lambda: RemoteTTSEngine("https://inference.example", transport=transport)
    with TestClient(app) as client:
        response = client.post("/api/tts", json={"text": "Mo fe ko ede Yoruba daadaa", "language": "yo"})
    assert calls == ["/diacritize", "/tts"]
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content == audio
