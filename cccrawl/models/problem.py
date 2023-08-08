import hashlib
from typing import NewType

from pydantic import HttpUrl, computed_field

from cccrawl.models.base import CCBaseModel, ModelUid


class Problem(CCBaseModel):
    problem_url: HttpUrl

    @computed_field()
    @property
    def uid(self) -> ModelUid:
        return ModelUid(self._hash_tokens(str(self.problem_url)))
