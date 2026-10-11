from app.modules.tts.diacritization import YorubaDiacritizer, has_yoruba_diacritics
from app.modules.tts.normalization import normalize_yoruba


class YorubaPreprocessor:
    def __init__(self, diacritizer: YorubaDiacritizer) -> None:
        self.diacritizer = diacritizer

    def preprocess(self, text: str) -> str:
        # Detect before adding punctuation; preserve marked text verbatim apart
        # from the explicit uppercase, surrounding whitespace, and ending rules.
        text = text.strip()
        if text and not has_yoruba_diacritics(text):
            text = self.diacritizer.diacritize(text)
        return normalize_yoruba(text)
