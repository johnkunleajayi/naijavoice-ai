from io import BytesIO

import numpy as np
import soundfile as sf


def trim_trailing_silence(samples: np.ndarray, sample_rate: int) -> np.ndarray:
    """Scan backwards in 0.1s RMS windows, retaining a 0.4s natural tail.

    Leading silence and internal pauses are untouched. Window boundaries give
    at most 0.1s boundary uncertainty. Entirely silent audio returns no samples.
    """
    audio = np.asarray(samples, dtype=np.float32)
    if sample_rate <= 0 or audio.ndim != 1 or not np.isfinite(audio).all():
        raise ValueError("Expected finite mono samples and positive sample rate")
    window = max(1, round(sample_rate * 0.1))
    tail = round(sample_rate * 0.4)
    end = len(audio)
    while end > 0:
        start = max(0, end - window)
        rms = np.sqrt(np.mean(np.square(audio[start:end], dtype=np.float64)))
        if rms > 0.01:
            return audio[:min(len(audio), end + tail)]
        end = start
    return audio[:0]


def encode_wav(samples: np.ndarray, sample_rate: int) -> bytes:
    output = BytesIO()
    sf.write(output, samples, sample_rate, format="WAV", subtype="PCM_16")
    return output.getvalue()
