from pathlib import Path
from unittest.mock import patch

from app.modules.tts.config import TTSSettings
from app.modules.tts.dependencies import get_tts_engine
from app.modules.tts.remote import RemoteTTSEngine

BACKEND = Path(__file__).resolve().parents[1]


def test_voxcpm2_model_and_existing_voice_defaults():
    settings = TTSSettings.from_env()
    assert settings.remote_model_id == "LyngualLabs/YorubaEnglish-CodeSwitching-TTS"
    assert settings.default_voice_audio_path == BACKEND / "assets/voices/naijavoice_default_voice.wav"
    assert settings.default_voice_transcript_path == BACKEND / "assets/voices/naijavoice_default_voice.txt"
    assert settings.default_voice_audio_path.is_file()
    transcript = settings.default_voice_transcript_path.read_text(encoding="utf-8").strip()
    assert transcript == "Ẹ káàbọ̀ sí NaijaVoice AI. Jẹ́ kí ohùn wa sọ ìtàn wa."


def test_defaults_are_independent_of_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert TTSSettings.from_env() == TTSSettings()


def test_voice_paths_and_model_can_be_overridden(monkeypatch, tmp_path):
    monkeypatch.setenv("TTS_REMOTE_MODEL_ID", " custom/model ")
    monkeypatch.setenv("TTS_DEFAULT_VOICE_AUDIO_PATH", str(tmp_path / "voice.wav"))
    monkeypatch.setenv("TTS_DEFAULT_VOICE_TRANSCRIPT_PATH", "assets/voices/custom.txt")
    settings = TTSSettings.from_env()
    assert settings.remote_model_id == "custom/model"
    assert settings.default_voice_audio_path == tmp_path / "voice.wav"
    assert settings.default_voice_transcript_path == BACKEND / "assets/voices/custom.txt"


def test_empty_values_use_defaults(monkeypatch):
    for name in ("TTS_REMOTE_MODEL_ID", "TTS_DEFAULT_VOICE_AUDIO_PATH", "TTS_DEFAULT_VOICE_TRANSCRIPT_PATH"):
        monkeypatch.setenv(name, "  ")
    assert TTSSettings.from_env() == TTSSettings()


def test_remote_selection_does_not_load_f5_or_read_voice_assets(monkeypatch):
    monkeypatch.setenv("TTS_INFERENCE_URL", "https://inference.example")
    with patch("app.modules.tts.dependencies.F5TTSYorubaEngine") as f5, patch.object(Path, "read_text", side_effect=AssertionError("No voice reads at selection")):
        engine = get_tts_engine()
    assert isinstance(engine, RemoteTTSEngine)
    assert engine.url == "https://inference.example/tts"
    f5.assert_not_called()
