import hashlib
from typing import NewType

from pydantic import EmailStr, computed_field

from cccrawl.models.base import CCBaseModel, ModelUid
from cccrawl.models.integration import Integration

Name = NewType("Name", str)
CodeforcesHandle = NewType("CodeforcesHandle", str)
CsesUserNumber = NewType("CsesUserNumber", int)


class UserConfig(CCBaseModel):
    name: Name
    email: EmailStr
    integrations: list[Integration]

    @computed_field
    @property
    def uid(self) -> ModelUid:
        return ModelUid(self._hash_tokens(self.email))
