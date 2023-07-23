import hashlib
from enum import auto
from typing import NewType, TypeVar

from pydantic import AwareDatetime, Field, HttpUrl, computed_field

from cccrawl.models.base import CCBaseModel, CCBaseStrEnum
from cccrawl.models.integration import IntegrationId
from cccrawl.models.user import UserUid
from cccrawl.utils import current_datetime

SubmissionUid = NewType("SubmissionUid", str)


class SubmissionVerdict(CCBaseStrEnum):
    """An enum representing possible submission verdicts.
    Currently we only support a boolean verdict (accepted or not accepted),
    since there are some judges (like CSES) where it is hard (and even)
    impossible to retrieve a more specific verdict."""

    accepted = auto()
    rejected = auto()


class CrawledSubmission(CCBaseModel):
    """A model that describes a single submission, where all information can
    and should be provided in a single scrape."""

    problem_url: HttpUrl
    verdict: SubmissionVerdict

    # The time in which the solution was submitted at. None if the judge does
    # not provide such information.
    submitted_at: AwareDatetime | None = None

    # A URL pointing to a webpage of the judge, which contains the solution,
    # source code, verdict, etc. (if exists)
    submission_url: HttpUrl | None = None

    # A URL pointing to a raw text file with the submission source code.
    raw_code_url: HttpUrl | None = None

    @computed_field()
    @property
    def uid(self) -> SubmissionUid:
        hash = hashlib.sha256()
        for token in (self.problem_url, self.verdict):
            hash.update(str(token).encode())
        return SubmissionUid(hash.hexdigest())


SubmissionT = TypeVar("SubmissionT", bound="Submission")


class Submission(CrawledSubmission):
    """A model that describes a single submission fully. This model expends the
    'crawled' submission model with information about the submission that
    require some context and can not be obtained in a single scrape."""

    # The first time the scraper scraped the solution.
    # Should not be changed between scrapes (constant value).
    first_seen_at: AwareDatetime

    @classmethod
    def from_crawled(
        cls: type[SubmissionT],
        crawled_submission: CrawledSubmission,
    ) -> SubmissionT:
        return cls(
            **crawled_submission.model_dump(),
            first_seen_at=current_datetime(),
        )


class UserSubmissions(CCBaseModel):
    """A model containing all submissions of a given user."""

    id: UserUid
    submissions: list[Submission] = Field(default_factory=list)
    last_update: AwareDatetime = Field(default_factory=current_datetime)
