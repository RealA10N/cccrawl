from typing import Literal

from pydantic import computed_field, conint

from cccrawl.models.base import ModelId
from cccrawl.models.integration import Integration, Platform


class CsesIntegration(Integration):
    platform: Literal[Platform.cses]
    user_number: conint(strict=True, gt=0, le=10_000_000)  # type: ignore[valid-type]

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> ModelId:
        return ModelId(self._hash_tokens(self.platform.value, self.user_number))
