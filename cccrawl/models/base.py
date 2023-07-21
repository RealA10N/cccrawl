from pydantic import BaseModel
from enum import StrEnum


class CCBaseModel(BaseModel):
    """A base model for all models used by CodeCoach and the crawler."""


class CCBaseStrEnum(StrEnum):
    """A base string based enum that is used by all enums in CodeCoach and the
    crawler."""
