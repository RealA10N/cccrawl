from abc import ABC
from enum import auto
from typing import TypeVar

from pydantic import AwareDatetime, HttpUrl

from cccrawl.models.any_integration import AnyIntegration
from cccrawl.models.base import CCBaseModel, CCBaseStrEnum
from cccrawl.models.problem import Problem
from cccrawl.utils import current_datetime


class SubmissionVerdict(CCBaseStrEnum):
    """An enum representing possible submission verdicts.
    Currently we only support a boolean verdict (accepted or not accepted),
    since there are some judges (like CSES) where it is hard (and even)
    impossible to retrieve a more specific verdict."""

    accepted = auto()
    rejected = auto()


class CrawledSubmission(ABC, CCBaseModel):
    """A model that describes a single submission, where all information can
    and should be provided in a single scrape."""

    integration: AnyIntegration
    problem: Problem
    verdict: SubmissionVerdict


SubmissionT = TypeVar("SubmissionT", bound="Submission")


class Submission(CrawledSubmission):
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
