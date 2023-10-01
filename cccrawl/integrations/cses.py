from typing import Literal

from pydantic import computed_field, conint, constr

from cccrawl.models.base import ModelId
from cccrawl.models.integration import Integration, Platform


class CsesIntegration(Integration):
    platform: Literal[Platform.cses] = Platform.cses
    handle: str = constr(min_length=1, max_length=16, strip_whitespace=True)  # type: ignore[assignment]
    user_number: int = conint(strict=True, gt=0, le=10_000_000)  # type: ignore[assignment]

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> ModelId:
        return ModelId(self._hash_tokens(self.platform.value, self.user_number))
