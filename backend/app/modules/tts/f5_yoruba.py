from threading import Lock
from typing import Literal

from app.modules.tts.audio import encode_wav
from app.modules.tts.config import TTSSettings
from app.modules.tts.engine import EngineUnavailableError

REFERENCE_TRANSCRIPT = "ẹ kú àárọ̀, báwo ni àwọn ọmọ yín ṣe wà?"


class F5TTSYorubaEngine:
    """Lazy adapter for local naijaml/f5-tts-yoruba checkpoint and vocabulary."""

    def __init__(self, settings: TTSSettings) -> None:
        self.settings = settings
        self._model = None
        self._lock = Lock()

    def _load_model(self):
        self.settings.validate_files()
        # Must precede importing f5_tts.api: inference binds this function at import.
        import f5_tts.model.utils as f5_utils

        f5_utils.convert_char_to_pinyin = lambda texts, polyphone=True: texts
        from f5_tts.api import F5TTS

        return F5TTS(
            model="F5TTS_v1_Base",
            ckpt_file=self.settings.checkpoint_path,
            vocab_file=self.settings.vocab_path,
            device=self.settings.device,
        )

    def synthesize(self, text: str, language: Literal["yo"]) -> bytes:
        if language != "yo":
            raise EngineUnavailableError("Only Yoruba is supported")
        # F5-TTS keeps mutable state; serialize loading and inference per process.
        with self._lock:
            try:
                if self._model is None:
                    self._model = self._load_model()
                samples, sample_rate, _ = self._model.infer(
                    ref_file=self.settings.reference_audio_path,
                    ref_text=REFERENCE_TRANSCRIPT,
                    gen_text=text,
                    speed=1.0,
                    nfe_step=16,
                )
                if samples is None or len(samples) == 0:
                    raise EngineUnavailableError("Speech engine returned no audio")
                return encode_wav(samples, sample_rate)
            except EngineUnavailableError:
                raise
            except Exception as exc:
                # Missing optional packages, device/load errors, and inference failures
                # use the API's existing clean unavailable response.
                raise EngineUnavailableError("Speech engine unavailable") from exc
