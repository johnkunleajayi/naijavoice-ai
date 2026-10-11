from io import BytesIO


def encode_wav(samples, sample_rate: int) -> bytes:
    """Encode the F5-TTS waveform in memory without temporary output files."""
    import soundfile

    output = BytesIO()
    soundfile.write(output, samples, sample_rate, format="WAV", subtype="PCM_16")
    return output.getvalue()
