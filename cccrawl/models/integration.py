from datetime import datetime, timezone
from enum import auto

from pydantic import AwareDatetime, computed_field, conint, constr

from cccrawl.models.base import CCBaseModel, CCBaseStrEnum, ModelId


class Platform(CCBaseStrEnum):
    codeforces = auto()
    cses = auto()


class Integration(CCBaseModel):
    platform: Platform
    last_fetch: AwareDatetime | None = None

    def update_last_fetched(self) -> None:
        self.last_fetch = datetime.now(tz=timezone.utc)
