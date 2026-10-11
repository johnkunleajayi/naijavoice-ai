import builtins
import io
import sys
import types
import wave
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.tts.config import TTSSettings
from app.modules.tts.dependencies import get_tts_engine
from app.modules.tts.engine import EngineUnavailableError
from app.modules.tts.f5_yoruba import F5TTSYorubaEngine, REFERENCE_TRANSCRIPT


@pytest.fixture
def settings(tmp_path):
    paths = []
    for filename in ("model_150000.pt", "vocab.txt", "reference.wav"):
        path = tmp_path / filename
        path.write_bytes(b"test placeholder, never loaded")
        paths.append(str(path))
    return TTSSettings(*paths)


@pytest.fixture
def runtime(monkeypatch):
    utils = types.ModuleType("f5_tts.model.utils")
    utils.convert_char_to_pinyin = Mock(side_effect=AssertionError("Must bypass pinyin"))
    model = Mock()
    model.infer.return_value = ([0.0, 0.0], 24000, None)
    constructor = Mock(return_value=model)
    api = types.ModuleType("f5_tts.api")

    def get_api_attribute(name):
        if name != "F5TTS":
            raise AttributeError(name)
        text = ["ẹ kú àárọ̀", "ọrẹ́"]
        assert utils.convert_char_to_pinyin(text) is text
        assert utils.convert_char_to_pinyin(text, polyphone=False) is text
        return constructor

    api.__getattr__ = get_api_attribute
    for name in ("f5_tts", "f5_tts.model"):
        package = types.ModuleType(name)
        package.__path__ = []
        monkeypatch.setitem(sys.modules, name, package)
    monkeypatch.setitem(sys.modules, "f5_tts.model.utils", utils)
    monkeypatch.setitem(sys.modules, "f5_tts.api", api)
    sf = types.ModuleType("soundfile")

    def write(output, samples, sample_rate, **kwargs):
        assert kwargs == {"format": "WAV", "subtype": "PCM_16"}
        with wave.open(output, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(sample_rate)
            audio.writeframes(b"\x00\x00" * len(samples))

    sf.write = Mock(side_effect=write)
    monkeypatch.setitem(sys.modules, "soundfile", sf)
    return constructor, model, sf


def configure_env(monkeypatch, settings):
    monkeypatch.setenv("TTS_CHECKPOINT_PATH", settings.checkpoint_path)
    monkeypatch.setenv("TTS_VOCAB_PATH", settings.vocab_path)
    monkeypatch.setenv("TTS_REFERENCE_AUDIO_PATH", settings.reference_audio_path)
    monkeypatch.setenv("TTS_DEVICE", settings.device)


def test_configuration_defaults_and_overrides(monkeypatch, settings):
    assert TTSSettings.from_env() == TTSSettings()
    configure_env(monkeypatch, settings)
    monkeypatch.setenv("TTS_DEVICE", "cpu")
    assert TTSSettings.from_env() == TTSSettings(
        settings.checkpoint_path, settings.vocab_path, settings.reference_audio_path, "cpu"
    )


def test_startup_and_adapter_creation_do_not_import_f5(monkeypatch, settings):
    configure_env(monkeypatch, settings)
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        assert not name.startswith(("f5_tts", "torch", "soundfile"))
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    with TestClient(create_app()) as client:
        assert client.get("/api/health").status_code == 200
        engine = get_tts_engine()
        assert isinstance(engine, F5TTSYorubaEngine)
        assert engine._model is None
        assert get_tts_engine() is engine


@pytest.mark.parametrize("device", ["cuda", "cpu"])
def test_model_settings_patch_order_and_wav(settings, runtime, device):
    constructor, model, sf = runtime
    settings = TTSSettings(settings.checkpoint_path, settings.vocab_path, settings.reference_audio_path, device)
    engine = F5TTSYorubaEngine(settings)
    constructor.assert_not_called()
    for _ in range(2):
        audio = engine.synthesize("ẹ káàárọ̀", "yo")
        with wave.open(io.BytesIO(audio), "rb") as wav:
            assert wav.getframerate() == 24000
            assert wav.getnframes() == 2
    constructor.assert_called_once_with(
        model="F5TTS_v1_Base", ckpt_file=settings.checkpoint_path,
        vocab_file=settings.vocab_path, device=device,
    )
    model.infer.assert_called_with(
        ref_file=settings.reference_audio_path,
        ref_text="ẹ kú àárọ̀, báwo ni àwọn ọmọ yín ṣe wà?",
        gen_text="ẹ káàárọ̀", speed=1.0, nfe_step=16,
    )
    assert model.infer.call_count == sf.write.call_count == 2
    assert REFERENCE_TRANSCRIPT == "ẹ kú àárọ̀, báwo ni àwọn ọmọ yín ṣe wà?"


@pytest.mark.parametrize("field", ["checkpoint_path", "vocab_path", "reference_audio_path"])
@pytest.mark.parametrize("value", ["", "does-not-exist"])
def test_unconfigured_or_missing_files_do_not_load(settings, runtime, field, value):
    constructor, _, _ = runtime
    config = dict(vars(settings))
    config[field] = value
    with pytest.raises(EngineUnavailableError):
        F5TTSYorubaEngine(TTSSettings(**config)).synthesize("ẹ", "yo")
    constructor.assert_not_called()


def test_configured_endpoint_uses_adapter_and_normalization(monkeypatch, settings, runtime):
    configure_env(monkeypatch, settings)
    _, model, _ = runtime
    with TestClient(create_app()) as client:
        response = client.post("/api/tts", json={"text": "Ẹ Ọ", "language": "yo"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content.startswith(b"RIFF")
    assert model.infer.call_args.kwargs["gen_text"] == "ẹ ọ."


@pytest.mark.parametrize("stage", ["load", "infer", "encode", "empty"])
def test_runtime_failures_keep_clean_503(monkeypatch, settings, runtime, stage):
    configure_env(monkeypatch, settings)
    constructor, model, sf = runtime
    if stage == "empty":
        model.infer.return_value = ([], 24000, None)
    else:
        target = {"load": constructor, "infer": model.infer, "encode": sf.write}[stage]
        target.side_effect = RuntimeError("private filesystem or GPU detail")
    with TestClient(create_app()) as client:
        response = client.post("/api/tts", json={"text": "ẹ", "language": "yo"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Speech generation is not available yet."}


def test_optional_dependency_missing_keeps_clean_503(monkeypatch, settings):
    configure_env(monkeypatch, settings)
    original_import = builtins.__import__

    def missing_import(name, *args, **kwargs):
        if name.startswith("f5_tts"):
            raise ModuleNotFoundError("f5_tts not installed")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing_import)
    with TestClient(create_app()) as client:
        response = client.post("/api/tts", json={"text": "ẹ", "language": "yo"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Speech generation is not available yet."}
