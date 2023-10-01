from typing import Annotated, Literal

from pydantic import Field, StringConstraints, computed_field

from cccrawl.models.base import ModelId
from cccrawl.models.integration import Integration, Platform


class CsesIntegration(Integration):
    platform: Literal[Platform.cses] = Platform.cses
    user_number: Annotated[int, Field(strict=True, ge=0, le=10_000_000)]
    handle: Annotated[
        str,
        StringConstraints(
            min_length=1,
            max_length=16,
            strip_whitespace=True,
        ),
    ]

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> ModelId:
        return ModelId(self._hash_tokens(self.platform.value, self.user_number))
