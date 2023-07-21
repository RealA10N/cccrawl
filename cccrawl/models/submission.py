from enum import auto

from typing import NewType
from cccrawl.models.base import CCBaseModel, CCBaseStrEnum
from pydantic import HttpUrl, AwareDatetime

ProblemUid = NewType("ProblemUid", str)


class SubmissionVerdict(CCBaseEnum):
    """An enum representing possible submission verdicts.
    Currently we only support a boolean verdict (accepted or not accepted),
    since there are some judges (like CSES) where it is hard (and even)
    impossible to retrieve a more specific verdict."""

    accepted = auto()
    rejected = auto()


class Submission(CCBaseModel):
    """A model that describes a single submission."""

    # A unique string that represents the problem.
    # Usually the URL of the problem, or part of it.
    # This should not change if the problem statement or title changes,
    # since this equality of problem UIDs is used to distinguish between
    # problems.
    problem_uid: ProblemUid

    # The submission verdict.
    verdict: SubmissionVerdict

    # The first time the scraper scraped the solution.
    # Should not be changed between scrapes (constant value).
    first_seen_at: AwareDatetime

    # The time in which the solution was submitted at. None if the judge does
    # not provide such information.
    submitted_at: AwareDatetime | None

    # A URL pointing to a webpage of the judge, which contains the solution,
    # source code, verdict, etc. (if exists)
    submission_url: HttpUrl | None

    # A URL pointing to a raw text file with the submission source code.
    raw_code_url: HttpUrl | None
