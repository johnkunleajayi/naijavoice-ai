import io
import sys
import types
import wave
from unittest.mock import Mock

import numpy as np
import pytest
from fastapi.testclient import TestClient

from voxcpm_service.config import MODEL_ID, Settings, VOICE_ROOT
from voxcpm_service.engine import VoxCPM2Engine
from voxcpm_service.main import create_app


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    reference = tmp_path / "voice.wav"
    reference.write_bytes(b"fixture: model is mocked")
    transcript = tmp_path / "voice.txt"
    transcript.write_text("Ẹ káàbọ̀ sí NaijaVoice AI.", encoding="utf-8")
    model = Mock()
    model.tts_model.sample_rate = 1000
    model.generate.return_value = np.concatenate([np.ones(1000) * .1, np.zeros(2000)])
    factory = Mock(return_value=model)
    module = types.ModuleType("voxcpm")
    module.VoxCPM = types.SimpleNamespace(from_pretrained=factory)
    monkeypatch.setitem(sys.modules, "voxcpm", module)
    engine = VoxCPM2Engine(Settings(reference, transcript))
    return engine, factory, model, reference, transcript


def test_default_assets_resolve_to_existing_repository_files(monkeypatch):
    monkeypatch.delenv("VOXCPM_REFERENCE_AUDIO_PATH", raising=False)
    monkeypatch.delenv("VOXCPM_REFERENCE_TRANSCRIPT_PATH", raising=False)
    settings = Settings.from_env()
    assert settings.reference_audio == VOICE_ROOT / "naijavoice_default_voice.wav"
    assert settings.reference_audio.is_file()
    assert "Ẹ káàbọ̀" in settings.reference_transcript.read_text(encoding="utf-8")


def test_health_is_lazy_and_generation_returns_trimmed_wav(runtime):
    engine, factory, model, reference, _ = runtime
    with TestClient(create_app(engine)) as client:
        assert client.get("/health").json() == {"status": "ok", "model_loaded": False}
        factory.assert_not_called()
        for _ in range(2):
            response = client.post("/tts", json={"text": "Ẹ káàbọ̀. Welcome!"})
            assert response.status_code == 200
            assert response.headers["content-type"] == "audio/wav"
            with wave.open(io.BytesIO(response.content)) as audio:
                assert audio.getframerate() == 1000
                assert audio.getnframes() == 1400
                assert audio.getnchannels() == 1
                assert audio.getsampwidth() == 2
        assert client.get("/health").json()["model_loaded"] is True
    factory.assert_called_once_with(MODEL_ID, load_denoiser=False, optimize=False, device="cuda")
    model.generate.assert_called_with(
        text="Ẹ káàbọ̀. Welcome!", prompt_wav_path=str(reference),
        prompt_text="Ẹ káàbọ̀ sí NaijaVoice AI.", cfg_value=2.0,
        inference_timesteps=22, retry_badcase=False,
    )


@pytest.mark.parametrize("payload", [{}, {"text": ""}, {"text": " \n\t"}, {"text": None}, {"text": 12}, {"text": "x" * 5001}])
def test_invalid_requests_never_load_model(runtime, payload):
    engine, factory, _, _, _ = runtime
    with TestClient(create_app(engine)) as client:
        assert client.post("/tts", json=payload).status_code == 422
    factory.assert_not_called()


@pytest.mark.parametrize("failure", ["load", "generate", "silent", "missing_audio", "missing_transcript", "empty_transcript"])
def test_failures_return_sanitized_503(runtime, failure):
    engine, factory, model, reference, transcript = runtime
    if failure == "load": factory.side_effect = RuntimeError("private model error")
    if failure == "generate": model.generate.side_effect = RuntimeError("private GPU error")
    if failure == "silent": model.generate.return_value = np.zeros(1000)
    if failure == "missing_audio": reference.unlink()
    if failure == "missing_transcript": transcript.unlink()
    if failure == "empty_transcript": transcript.write_text("   ", encoding="utf-8")
    with TestClient(create_app(engine)) as client:
        response = client.post("/tts", json={"text": "ẹ káàárọ̀"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Speech generation is unavailable."}
    if failure in {"missing_audio", "missing_transcript", "empty_transcript"}:
        factory.assert_not_called()
