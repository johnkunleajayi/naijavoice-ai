import pytest

from app.modules.tts.dependencies import get_tts_engine


@pytest.fixture(autouse=True)
def isolate_tts_environment(monkeypatch):
    # Prevent developer/host configuration from triggering real model work in tests.
    for name in ("TTS_CHECKPOINT_PATH", "TTS_VOCAB_PATH", "TTS_REFERENCE_AUDIO_PATH", "TTS_DEVICE", "TTS_REMOTE_MODEL_ID", "TTS_DEFAULT_VOICE_AUDIO_PATH", "TTS_DEFAULT_VOICE_TRANSCRIPT_PATH"):
        monkeypatch.delenv(name, raising=False)
    # Override the configured .env URL to keep the entire suite offline.
    monkeypatch.setenv("TTS_INFERENCE_URL", "")
    monkeypatch.setenv("TRANSLATION_INFERENCE_URL", "")
    monkeypatch.setenv("DIACRITIZATION_INFERENCE_URL", "")
    get_tts_engine.cache_clear()
    yield
    get_tts_engine.cache_clear()
