from datetime import datetime, timezone
from pydantic import AwareDatetime


def current_datetime() -> AwareDatetime:
    """Returns an instance representing the current date and time, with
    timezone metadata included."""
    return datetime.now(tz=timezone.utc)
