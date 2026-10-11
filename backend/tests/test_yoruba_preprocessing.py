from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.tts.dependencies import get_tts_engine, get_yoruba_diacritizer
from app.modules.tts.diacritization import PassthroughYorubaDiacritizer, has_yoruba_diacritics
from app.modules.tts.preprocessing import YorubaPreprocessor


@pytest.mark.parametrize("text", ["ẹ", "Ọ", "Ṣ", "á", "ò", "ń", "ā", "e\u0323", "o\u0301", "Mo fẹ́ kọ́ èdè Yorùbá."])
def test_detects_precomposed_and_combining_marks(text):
    assert has_yoruba_diacritics(text)


@pytest.mark.parametrize("text", ["", "Mo fe ko ede Yoruba daadaa", "ABC 123?!", " "])
def test_detects_unmarked_input(text):
    assert not has_yoruba_diacritics(text)


def test_unmarked_text_passes_through_adapter_then_gets_period():
    text = "Mo fe ko ede Yoruba daadaa"
    adapter = Mock(wraps=PassthroughYorubaDiacritizer())
    assert YorubaPreprocessor(adapter).preprocess("  " + text + "  ") == text + "."
    adapter.diacritize.assert_called_once_with(text)


def test_future_diacritizer_output_is_normalized():
    adapter = Mock()
    adapter.diacritize.return_value = "  Ẹ fẹ́ kọ́ èdè Yorùbá  "
    assert YorubaPreprocessor(adapter).preprocess("E fe ko ede Yoruba") == "ẹ fẹ́ kọ́ èdè Yorùbá."
    adapter.diacritize.assert_called_once_with("E fe ko ede Yoruba")


@pytest.mark.parametrize("text", ["Mo fẹ́ kọ́ èdè Yorùbá dáadáa.", "Báwo ni?", "Ẹ káàbọ̀!", "e\u0323\u0301."])
def test_marked_input_bypasses_diacritizer_and_preserves_marks(text):
    adapter = Mock()
    expected = text.replace("Ẹ", "ẹ")
    assert YorubaPreprocessor(adapter).preprocess(text) == expected
    adapter.diacritize.assert_not_called()


def test_blank_text_does_not_call_diacritizer():
    adapter = Mock()
    assert YorubaPreprocessor(adapter).preprocess("   ") == ""
    adapter.diacritize.assert_not_called()


@pytest.mark.parametrize("text,expected", [
    ("  Mo fe ko ede Yoruba daadaa  ", "Mo fe ko ede Yoruba daadaa."),
    ("Mo fe!", "Mo fe!"),
    ("Mo fe?", "Mo fe?"),
    ("Mo fẹ́ kọ́ èdè Yorùbá dáadáa.", "Mo fẹ́ kọ́ èdè Yorùbá dáadáa."),
])
def test_endpoint_sends_preprocessed_text_to_engine(text, expected):
    engine = Mock()
    engine.synthesize.return_value = b"test audio"
    adapter = Mock(wraps=PassthroughYorubaDiacritizer())
    app = create_app()
    app.dependency_overrides[get_tts_engine] = lambda: engine
    app.dependency_overrides[get_yoruba_diacritizer] = lambda: adapter
    with TestClient(app) as client:
        response = client.post("/api/tts", json={"text": text, "language": "yo"})
    assert response.status_code == 200
    engine.synthesize.assert_called_once_with(text=expected, language="yo")
    assert adapter.diacritize.call_count == (0 if has_yoruba_diacritics(text) else 1)
