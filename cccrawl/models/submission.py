from abc import ABC
from enum import auto
from typing import Generic, TypeVar

from pydantic import AwareDatetime, HttpUrl

from cccrawl.models.base import CCBaseModel, CCBaseStrEnum
from cccrawl.models.integration import Integration
from cccrawl.models.problem import Problem
from cccrawl.utils import current_datetime

SubmissionT = TypeVar("SubmissionT", bound="Submission")
IntegrationT = TypeVar("IntegrationT", bound=Integration)


class SubmissionVerdict(CCBaseStrEnum):
    """An enum representing possible submission verdicts.
    Currently we only support a boolean verdict (accepted or not accepted),
    since there are some judges (like CSES) where it is hard (and even)
    impossible to retrieve a more specific verdict."""

    accepted = auto()
    rejected = auto()


class CrawledSubmission(ABC, CCBaseModel, Generic[IntegrationT]):
    """A model that describes a single submission, where all information can
    and should be provided in a single scrape."""

    integration: IntegrationT
    problem: Problem
    verdict: SubmissionVerdict


class Submission(CrawledSubmission[IntegrationT], Generic[IntegrationT]):
    """A model that describes a single submission fully. This model expends the
    'crawled' submission model with information about the submission that
    require some context and can not be obtained in a single scrape."""

    # The first time the scraper scraped the solution.
    # Should not be changed between scrapes (constant value).
    first_seen_at: AwareDatetime

    # The time in which the solution was submitted at. None if the judge does
    # not provide such information.
    submitted_at: AwareDatetime | None = None

    # A URL pointing to a webpage of the judge, which contains the solution,
    # source code, verdict, etc. (if exists)
    submission_url: HttpUrl | None = None

    # A URL pointing to a raw text file with the submission source code.
    raw_code_url: HttpUrl | None = None

    @classmethod
    def from_crawled(
        cls: type[SubmissionT],
        crawled_submission: CrawledSubmission,
        **additional_kwargs,
    ) -> SubmissionT:
        return cls(
            **crawled_submission.model_dump(),
            first_seen_at=current_datetime(),
            **additional_kwargs,
        )
