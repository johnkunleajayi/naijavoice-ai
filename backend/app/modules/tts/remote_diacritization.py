import json

import httpx

from app.modules.tts.engine import EngineUnavailableError


class RemoteYorubaDiacritizer:
    """Restore Yoruba marks through the shared remote inference service."""

    def __init__(self, base_url: str, *, transport: httpx.BaseTransport | None = None):
        self.url = base_url.rstrip("/") + "/diacritize"
        self.transport = transport

    def diacritize(self, text: str) -> str:
        payload = json.dumps({"text": text}, ensure_ascii=False).encode("utf-8")
        try:
            with httpx.Client(
                timeout=httpx.Timeout(60.0, connect=5.0, write=10.0, pool=5.0),
                transport=self.transport,
                follow_redirects=False,
            ) as client:
                response = client.post(
                    self.url,
                    content=payload,
                    headers={
                        "Content-Type": "application/json; charset=utf-8",
                        "Accept": "application/json",
                        "ngrok-skip-browser-warning": "true",
                    },
                )
        except (httpx.RequestError, httpx.InvalidURL) as exc:
            raise EngineUnavailableError("Remote diacritization unavailable") from exc
        if response.status_code != 200:
            raise EngineUnavailableError("Remote diacritization failed")
        try:
            result = json.loads(response.content.decode("utf-8"))
        except ValueError as exc:
            raise EngineUnavailableError("Invalid diacritization response") from exc
        if not isinstance(result, dict):
            raise EngineUnavailableError("Invalid diacritization response")
        restored = result.get("diacritized_text") or result.get("text")
        if not isinstance(restored, str) or not restored.strip():
            raise EngineUnavailableError("Invalid restored text")
        return restored
