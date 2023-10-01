from typing import Literal

from pydantic import computed_field, constr

from cccrawl.models.base import ModelId
from cccrawl.models.integration import Integration, Platform


class CodeforcesIntegration(Integration):
    platform: Literal[Platform.codeforces] = Platform.codeforces
    handle: str = constr(to_lower=True, min_length=3, max_length=30)  # type: ignore[assignment]

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> ModelId:
        return ModelId(self._hash_tokens(self.platform.value, self.handle))
