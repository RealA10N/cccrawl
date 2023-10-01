from typing import Annotated, Literal

from pydantic import StringConstraints, computed_field

from cccrawl.models.base import ModelId
from cccrawl.models.integration import Integration, Platform


class CodeforcesIntegration(Integration):
    platform: Literal[Platform.codeforces] = Platform.codeforces
    handle: Annotated[
        str, StringConstraints(to_lower=True, min_length=3, max_length=30)
    ]

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> ModelId:
        return ModelId(self._hash_tokens(self.platform.value, self.handle))
