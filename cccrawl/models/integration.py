from enum import auto
from typing import Literal, NewType, TypeAlias

from pydantic import computed_field, conint, constr

from cccrawl.models.base import CCBaseModel, CCBaseStrEnum, ModelUid


class Platform(CCBaseStrEnum):
    codeforces = auto()
    cses = auto()


class Integration(CCBaseModel):
    platform: Platform
