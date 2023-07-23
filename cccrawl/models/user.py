import hashlib
from typing import NewType

from pydantic import EmailStr, computed_field

from cccrawl.models.base import CCBaseModel

Name = NewType("Name", str)
UserUid = NewType("UserUid", str)
CodeforcesHandle = NewType("CodeforcesHandle", str)
CsesUserNumber = NewType("CsesUserNumber", int)


class UserConfig(CCBaseModel):
    name: Name
    email: EmailStr
    codeforces: CodeforcesHandle | None
    cses: CsesUserNumber | None

    @computed_field
    @property
    def uid(self) -> UserUid:
        return UserUid(hashlib.sha256(self.email.encode()).hexdigest())
