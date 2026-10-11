import json
from typing import Literal

import httpx

from app.modules.tts.engine import EngineUnavailableError


class RemoteTTSEngine:
    """Forward already-normalized Yoruba text to the inference host."""

    def __init__(self, base_url: str, *, transport: httpx.BaseTransport | None = None):
        self.url = base_url.rstrip("/") + "/tts"
        self.transport = transport

    def synthesize(self, text: str, language: Literal["yo"]) -> bytes:
        if language != "yo":
            raise EngineUnavailableError("Only Yoruba is supported")
        payload = json.dumps({"text": text}, ensure_ascii=False).encode("utf-8")
        try:
            with httpx.Client(
                timeout=httpx.Timeout(120.0, connect=5.0, write=10.0, pool=5.0),
                transport=self.transport,
                follow_redirects=False,
            ) as client:
                response = client.post(
                    self.url,
                    content=payload,
                    headers={
                        "Content-Type": "application/json; charset=utf-8",
                        "Accept": "audio/wav",
                        "ngrok-skip-browser-warning": "true",
                    },
                )
        except (httpx.RequestError, httpx.InvalidURL) as exc:
            raise EngineUnavailableError("Remote speech service unavailable") from exc
        if response.status_code != 200:
            raise EngineUnavailableError("Remote speech service failed")
        audio = response.content
        # Never present an ngrok HTML page or upstream JSON error as WAV audio.
        if len(audio) < 12 or audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
            raise EngineUnavailableError("Remote speech service returned invalid audio")
        return audio
