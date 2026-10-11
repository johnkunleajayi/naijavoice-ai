import unicodedata
from typing import Protocol

# Grave/acute tones, optional explicit mid tone, and Yoruba underdots.
_YORUBA_MARKS = frozenset({"\u0300", "\u0301", "\u0304", "\u0323"})


def has_yoruba_diacritics(text: str) -> bool:
    """Detect marks, not linguistic correctness or completeness of marking."""
    return any(char in _YORUBA_MARKS for char in unicodedata.normalize("NFD", text))


class YorubaDiacritizer(Protocol):
    def diacritize(self, text: str) -> str:
        """Return contextually marked Yoruba without changing its meaning."""
        ...


class PassthroughYorubaDiacritizer:
    def diacritize(self, text: str) -> str:
        # Intentionally no dictionary or word substitution; a real model comes later.
        return text
