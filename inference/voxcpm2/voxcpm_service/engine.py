from threading import Lock

from voxcpm_service.audio import encode_wav, trim_trailing_silence
from voxcpm_service.config import MODEL_ID, Settings


class InferenceUnavailableError(Exception):
    pass


class VoxCPM2Engine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._model = None
        self._lock = Lock()

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def _load_model(self):
        # Heavy GPU imports/downloads happen only on the first POST /tts.
        from voxcpm import VoxCPM

        return VoxCPM.from_pretrained(
            MODEL_ID, load_denoiser=False, optimize=False, device="cuda"
        )

    def synthesize(self, text: str) -> bytes:
        with self._lock:
            try:
                if not self.settings.reference_audio.is_file():
                    raise ValueError("Reference audio is missing")
                transcript = self.settings.reference_transcript.read_text(encoding="utf-8").strip()
                if not transcript:
                    raise ValueError("Reference transcript is empty")
                if self._model is None:
                    self._model = self._load_model()
                waveform = self._model.generate(
                    text=text,
                    prompt_wav_path=str(self.settings.reference_audio),
                    prompt_text=transcript,
                    cfg_value=2.0,
                    inference_timesteps=22,
                    retry_badcase=False,
                )
                sample_rate = self._model.tts_model.sample_rate
                trimmed = trim_trailing_silence(waveform, sample_rate)
                if not len(trimmed):
                    raise ValueError("No audible speech was generated")
                return encode_wav(trimmed, sample_rate)
            except Exception as exc:
                raise InferenceUnavailableError("Speech generation unavailable") from exc
