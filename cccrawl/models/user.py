import hashlib
from typing import NewType

from pydantic import EmailStr, validator

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

    uid: UserUid = None

    @validator("uid", always=True, pre=True)
    def uid_validator(cls, v, values) -> UserUid:
        expected = hashlib.sha256(values["email"].encode()).hexdigest()
        if v:
            assert v == expected
        return expected
