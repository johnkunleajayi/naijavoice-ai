import json

import httpx
import pytest

from app.modules.translation.dependencies import get_translation_service
from app.modules.tts.dependencies import get_tts_engine, get_yoruba_diacritizer


@pytest.mark.parametrize("endpoint", ["tts", "diacritize", "translate"])
def test_configured_ngrok_adapters_send_browser_warning_bypass(monkeypatch, endpoint):
    base_url = "https://trustless-episode-blank.ngrok-free.dev"
    monkeypatch.setenv("TTS_INFERENCE_URL", base_url)
    requests = []
    audio = b"RIFF" + b"1234" + b"WAVE" + b"test audio"

    def handle_request(transport, request):
        requests.append(request)
        assert str(request.url) == f"{base_url}/{endpoint}"
        assert request.method == "POST"
        assert request.headers["ngrok-skip-browser-warning"] == "true"
        assert json.loads(request.content.decode("utf-8")) == {"text": "ẹ káàárọ̀"}
        if endpoint == "tts":
            return httpx.Response(200, content=audio)
        return httpx.Response(200, json={"text": "ẹ káàárọ̀"})

    # Exercise real dependency configuration and HTTP request construction,
    # replacing only the network transport. No request reaches ngrok.
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", handle_request)
    if endpoint == "tts":
        assert get_tts_engine().synthesize("ẹ káàárọ̀", "yo") == audio
    elif endpoint == "diacritize":
        assert get_yoruba_diacritizer().diacritize("ẹ káàárọ̀") == "ẹ káàárọ̀"
    else:
        assert get_translation_service().translate("ẹ káàárọ̀") == "ẹ káàárọ̀"
    assert len(requests) == 1
