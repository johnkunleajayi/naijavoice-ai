from typing import Literal, Protocol


class EngineUnavailableError(Exception):
    """The speech engine is not configured or cannot serve requests."""


class TTSEngine(Protocol):
    def synthesize(self, text: str, language: Literal["yo"]) -> bytes:
        """Return complete WAV audio bytes or raise EngineUnavailableError."""
        ...


class UnconfiguredTTSEngine:
    def synthesize(self, text: str, language: Literal["yo"]) -> bytes:
        raise EngineUnavailableError("No speech engine is configured")
