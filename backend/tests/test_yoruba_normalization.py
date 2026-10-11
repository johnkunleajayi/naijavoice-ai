import pytest

from app.modules.tts.normalization import normalize_yoruba


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Ẹ", "ẹ."),
        ("Ọ", "ọ."),
        ("Ẹ káàárọ̀, Ọrẹ́!", "ẹ káàárọ̀, ọrẹ́!"),
        ("Ẹ́ Ọ̀ ẸỌ", "ẹ́ ọ̀ ẹọ."),
        ("ẹ káàárọ̀", "ẹ káàárọ̀."),
        ("ABC E O Ṣ À! 123\n", "ABC E O Ṣ À! 123."),
        ("  Ẹ\nỌ  ", "ẹ\nọ."),
        ("", ""),
        (" \n\t ", ""),
        ("Mo fe ko ede Yoruba daadaa", "Mo fe ko ede Yoruba daadaa."),
        ("Mo fẹ́ kọ́ èdè Yorùbá dáadáa.", "Mo fẹ́ kọ́ èdè Yorùbá dáadáa."),
        ("  Báwo ni?  ", "Báwo ni?"),
        ("Ẹ káàbọ̀!", "ẹ káàbọ̀!"),
        ("Báwo ni?!", "Báwo ni?!"),
        ("Mo fe...", "Mo fe..."),
        ("Mo fe,", "Mo fe,."),
    ],
)
def test_targeted_normalization(text, expected):
    assert normalize_yoruba(text) == expected
    assert normalize_yoruba(normalize_yoruba(text)) == expected
