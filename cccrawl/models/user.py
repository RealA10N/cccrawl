import hashlib
from typing import NewType

from pydantic import EmailStr

from cccrawl.models.base import CCBaseModel

Name = NewType('Name', str)
UserUid = NewType('UserUid', str)
CodeforcesHandle = NewType('CodeforcesHandle', str)
CsesUserNumber = NewType('CsesUserNumber', int)


class UserConfig(CCBaseModel):
    name: Name
    email: EmailStr
    codeforces: CodeforcesHandle
    cses: CsesUserNumber

    @property
    def id(self) -> UserUid:
        return hashlib.sha256(self.name.encode()).hexdigest()
