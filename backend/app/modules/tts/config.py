import os
from dataclasses import dataclass
from pathlib import Path

from app.modules.tts.engine import EngineUnavailableError


@dataclass(frozen=True)
class TTSSettings:
    checkpoint_path: str = ""
    vocab_path: str = ""
    reference_audio_path: str = ""
    device: str = "cuda"
    inference_url: str = ""

    @classmethod
    def from_env(cls) -> "TTSSettings":
        return cls(
            checkpoint_path=os.getenv("TTS_CHECKPOINT_PATH", "").strip(),
            vocab_path=os.getenv("TTS_VOCAB_PATH", "").strip(),
            reference_audio_path=os.getenv("TTS_REFERENCE_AUDIO_PATH", "").strip(),
            inference_url=os.getenv("TTS_INFERENCE_URL", "").strip(),
            device=os.getenv("TTS_DEVICE", "cuda").strip() or "cuda",
        )

    def validate_files(self) -> None:
        for value in (self.checkpoint_path, self.vocab_path, self.reference_audio_path):
            if not value or not Path(value).is_file():
                raise EngineUnavailableError("TTS requires configured local files")
