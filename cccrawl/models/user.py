from typing import NewType

from pydantic import EmailStr, Field, RootModel, computed_field
from typing_extensions import TypeAlias

from cccrawl.crawlers.codeforces import CodeforcesIntegration
from cccrawl.crawlers.cses import CsesIntegration
from cccrawl.models.any_integration import AnyIntegration
from cccrawl.models.base import CCBaseModel, ModelUid

Name = NewType("Name", str)


class UserConfig(CCBaseModel):
    name: Name
    email: EmailStr
    integrations: list[AnyIntegration]

    @computed_field  # type: ignore[misc]
    @property
    def uid(self) -> ModelUid:
        return ModelUid(self._hash_tokens(self.email))
