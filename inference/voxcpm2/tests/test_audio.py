import numpy as np
import pytest

from voxcpm_service.audio import trim_trailing_silence


def test_backwards_trim_preserves_natural_tail_and_internal_silence():
    audio = np.concatenate([np.zeros(100), np.ones(400) * .1, np.zeros(200), np.ones(300) * .1, np.zeros(2000)])
    result = trim_trailing_silence(audio, 1000)
    assert len(result) == 1400
    np.testing.assert_allclose(result, audio[:1400], rtol=1e-7)


def test_short_existing_tail_is_not_padded_or_removed():
    audio = np.concatenate([np.ones(1000) * .1, np.zeros(200)])
    np.testing.assert_allclose(trim_trailing_silence(audio, 1000), audio, rtol=1e-7)


@pytest.mark.parametrize("audio", [np.zeros(2000), np.array([]), np.ones(2000) * .009])
def test_silent_or_below_threshold_audio_has_no_speech(audio):
    assert len(trim_trailing_silence(audio, 1000)) == 0


def test_low_but_above_threshold_speech_and_partial_window():
    audio = np.concatenate([np.ones(155) * .011, np.zeros(1000)])
    # Scanning backwards finds the exact end here despite a partial first window.
    assert len(trim_trailing_silence(audio, 1000)) == 555


@pytest.mark.parametrize("rate", [16000, 24000, 48000])
def test_window_and_tail_scale_with_sample_rate(rate):
    audio = np.concatenate([np.ones(rate) * .1, np.zeros(rate * 2)])
    assert len(trim_trailing_silence(audio, rate)) == rate + round(rate * .4)


@pytest.mark.parametrize("audio,rate", [(np.ones(3), 0), (np.zeros((2, 2)), 1000), (np.array([np.nan]), 1000)])
def test_invalid_waveforms_are_rejected(audio, rate):
    with pytest.raises(ValueError):
        trim_trailing_silence(audio, rate)
