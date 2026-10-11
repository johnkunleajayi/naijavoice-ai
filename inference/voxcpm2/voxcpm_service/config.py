import os
from dataclasses import dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
VOICE_ROOT = REPOSITORY_ROOT / "backend" / "assets" / "voices"
MODEL_ID = "LyngualLabs/YorubaEnglish-CodeSwitching-TTS"


@dataclass(frozen=True)
class Settings:
    reference_audio: Path = VOICE_ROOT / "naijavoice_default_voice.wav"
    reference_transcript: Path = VOICE_ROOT / "naijavoice_default_voice.txt"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            reference_audio=Path(os.getenv("VOXCPM_REFERENCE_AUDIO_PATH") or cls.reference_audio).expanduser().resolve(),
            reference_transcript=Path(os.getenv("VOXCPM_REFERENCE_TRANSCRIPT_PATH") or cls.reference_transcript).expanduser().resolve(),
        )
