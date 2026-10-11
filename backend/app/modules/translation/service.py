from typing import Protocol


class TranslationUnavailableError(Exception):
    """Translation cannot be completed by the configured provider."""


class TranslationEngine(Protocol):
    def translate(self, text: str) -> str:
        """Translate English into marked Yoruba."""
        ...


class TranslationService:
    def __init__(self, engine: TranslationEngine) -> None:
        self.engine = engine

    def translate(self, text: str) -> str:
        # Translation output is already marked: no TTS preprocessing here.
        return self.engine.translate(text)
