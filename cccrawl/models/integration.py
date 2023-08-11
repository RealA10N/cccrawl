from enum import auto

from pydantic import AwareDatetime

from cccrawl.models.base import CCBaseModel, CCBaseStrEnum
from cccrawl.utils import current_datetime


class Platform(CCBaseStrEnum):
    codeforces = auto()
    cses = auto()


class Integration(CCBaseModel):
    platform: Platform
    last_fetch: AwareDatetime | None = None

    def update_last_fetched(self) -> None:
        self.last_fetch = current_datetime()
