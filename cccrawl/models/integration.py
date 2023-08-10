from enum import auto

from pydantic import computed_field, conint, constr

from cccrawl.models.base import CCBaseModel, CCBaseStrEnum, ModelId


class Platform(CCBaseStrEnum):
    codeforces = auto()
    cses = auto()


class Integration(CCBaseModel):
    platform: Platform
