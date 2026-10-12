import os
from dataclasses import dataclass
from pathlib import Path

from app.modules.tts.engine import EngineUnavailableError

_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_VOICE_ROOT = _BACKEND_ROOT / "assets" / "voices"
DEFAULT_REMOTE_MODEL_ID = "LyngualLabs/YorubaEnglish-CodeSwitching-TTS"


def _asset_path(variable: str, default: Path) -> Path:
    value = os.getenv(variable, "").strip()
    path = Path(value).expanduser() if value else default
    return (path if path.is_absolute() else _BACKEND_ROOT / path).resolve()


@dataclass(frozen=True)
class TTSSettings:
    checkpoint_path: str = ""
    vocab_path: str = ""
    reference_audio_path: str = ""
    device: str = "cuda"
    inference_url: str = ""
    diacritization_inference_url: str = ""
    # Deployment metadata: the remote host selects/loads the VoxCPM2 model.
    remote_model_id: str = DEFAULT_REMOTE_MODEL_ID
    default_voice_audio_path: Path = _VOICE_ROOT / "naijavoice_default_voice.wav"
    default_voice_transcript_path: Path = _VOICE_ROOT / "naijavoice_default_voice.txt"

    @classmethod
    def from_env(cls) -> "TTSSettings":
        return cls(
            remote_model_id=os.getenv("TTS_REMOTE_MODEL_ID", "").strip() or DEFAULT_REMOTE_MODEL_ID,
            default_voice_audio_path=_asset_path(
                "TTS_DEFAULT_VOICE_AUDIO_PATH", _VOICE_ROOT / "naijavoice_default_voice.wav"
            ),
            default_voice_transcript_path=_asset_path(
                "TTS_DEFAULT_VOICE_TRANSCRIPT_PATH", _VOICE_ROOT / "naijavoice_default_voice.txt"
            ),
            checkpoint_path=os.getenv("TTS_CHECKPOINT_PATH", "").strip(),
            vocab_path=os.getenv("TTS_VOCAB_PATH", "").strip(),
            reference_audio_path=os.getenv("TTS_REFERENCE_AUDIO_PATH", "").strip(),
            inference_url=os.getenv("TTS_INFERENCE_URL", "").strip(),
            diacritization_inference_url=os.getenv("DIACRITIZATION_INFERENCE_URL", "").strip(),
            device=os.getenv("TTS_DEVICE", "cuda").strip() or "cuda",
        )

    def validate_files(self) -> None:
        for value in (self.checkpoint_path, self.vocab_path, self.reference_audio_path):
            if not value or not Path(value).is_file():
                raise EngineUnavailableError("TTS requires configured local files")
