from typing import NewType

from pydantic import EmailStr, Field, RootModel, computed_field
from typing_extensions import TypeAlias

from cccrawl.models.any_integration import AnyIntegration
from cccrawl.models.base import CCBaseModel, ModelId

Name = NewType("Name", str)


class UserConfig(CCBaseModel):
    name: Name
    email: EmailStr
    integrations: list[AnyIntegration]

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> ModelId:
        return ModelId(self._hash_tokens(self.email))
