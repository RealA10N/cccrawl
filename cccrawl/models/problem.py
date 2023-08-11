from pydantic import HttpUrl, computed_field

from cccrawl.models.base import CCBaseModel, ModelId


class Problem(CCBaseModel):
    problem_url: HttpUrl

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> ModelId:
        return ModelId(self._hash_tokens(str(self.problem_url)))
