"""Targeted character and sentence normalization for Yoruba speech."""

_YORUBA_TRANSLATION = str.maketrans({"Ẹ": "ẹ", "Ọ": "ọ"})


def normalize_yoruba(text: str) -> str:
    """Preserve internal spacing, tone marks, and user punctuation."""
    normalized = text.translate(_YORUBA_TRANSLATION).strip()
    if normalized and not normalized.endswith((".", "!", "?")):
        normalized += "."
    return normalized
