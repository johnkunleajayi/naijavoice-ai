import json

import httpx

from app.modules.translation.service import TranslationUnavailableError


class RemoteTranslationEngine:
    def __init__(self, base_url: str, *, transport: httpx.BaseTransport | None = None):
        self.base_url = base_url.strip().rstrip("/")
        self.transport = transport

    def translate(self, text: str) -> str:
        if not self.base_url:
            raise TranslationUnavailableError("Inference URL is not configured")
        payload = json.dumps({"text": text}, ensure_ascii=False).encode("utf-8")
        try:
            with httpx.Client(
                timeout=httpx.Timeout(60.0, connect=5.0, write=10.0, pool=5.0),
                transport=self.transport,
                follow_redirects=False,
            ) as client:
                response = client.post(
                    self.base_url + "/translate",
                    content=payload,
                    headers={
                        "Content-Type": "application/json; charset=utf-8",
                        "Accept": "application/json",
                        "ngrok-skip-browser-warning": "true",
                    },
                )
        except (httpx.RequestError, httpx.InvalidURL) as exc:
            raise TranslationUnavailableError("Remote translation unavailable") from exc
        if response.status_code != 200:
            raise TranslationUnavailableError("Remote translation failed")
        try:
            result = json.loads(response.content.decode("utf-8"))
        except ValueError as exc:
            raise TranslationUnavailableError("Invalid translation response") from exc
        translated = (
            result.get("translated_text") or result.get("text")
            if isinstance(result, dict)
            else None
        )
        if not isinstance(translated, str) or not translated.strip():
            raise TranslationUnavailableError("Invalid translated text")
        return translated
