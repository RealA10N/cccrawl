import hashlib
from typing import NewType

from pydantic import EmailStr, computed_field

from cccrawl.models.base import CCBaseModel, ModelUid

Name = NewType("Name", str)
CodeforcesHandle = NewType("CodeforcesHandle", str)
CsesUserNumber = NewType("CsesUserNumber", int)


class UserConfig(CCBaseModel):
    name: Name
    email: EmailStr
    codeforces: CodeforcesHandle | None
    cses: CsesUserNumber | None

    @computed_field
    @property
    def uid(self) -> ModelUid:
        return ModelUid(self._hash_tokens(self.email))
