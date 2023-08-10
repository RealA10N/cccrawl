import hashlib
from abc import abstractmethod
from enum import StrEnum
from typing import NewType, Protocol, runtime_checkable

from pydantic import BaseModel

ModelId = NewType("ModelUid", str)


@runtime_checkable
class HasUid(Protocol):
    @property
    def uid(self) -> ModelId:
        ...


class CCBaseModel(BaseModel):
    """A base model for all models used by CodeCoach and the crawler."""

    @property
    @abstractmethod
    def id(self) -> ModelId:
        """A predictable uid (typically a hash) that represents the object."""

    def _hash_tokens(self, *tokens: str | int | HasUid) -> str:
        """Returns a predictible and consistant hash that is a direct output
        of the provided string tokens. To be used with the abstract uid
        property: every model implementation should define the tokens it depends
        on."""
        hash = hashlib.sha256()
        for token in tokens:
            token_str = token.uid if isinstance(token, HasUid) else str(token)
            hash.update(token_str.encode(encoding="utf8"))
        return hash.hexdigest()


class CCBaseStrEnum(StrEnum):
    """A base string based enum that is used by all enums in CodeCoach and the
    crawler."""
