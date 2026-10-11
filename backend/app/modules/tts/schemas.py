from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    language: Literal["yo"]

    @field_validator("text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Text must contain non-whitespace characters")
        return value
