import asyncio
from collections.abc import Awaitable
from datetime import datetime, timedelta
from functools import wraps
from queue import Queue
from typing import Callable, ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")


async def wait_until(when: datetime) -> None:
    now = datetime.now()
    sleep_for = (when - now).total_seconds()
    if sleep_for > 0:
        await asyncio.sleep(sleep_for)


def ratelimit(
    calls: int, every: timedelta | float
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """A ratelimit decorator to wrap async functions.
    Ensures that the wrapped function is called at most 'calls' times in any
    'every' interval of time. If it is called more then that, the call will
    sleep (using async.sleep) until it is safe to make the call, and then the
    execution will resume."""

    every = timedelta(seconds=every) if not isinstance(every, timedelta) else every

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        recent_calls = Queue[datetime](maxsize=calls + 1)

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            recent_calls.put(datetime.now())
            if recent_calls.qsize() > calls:
                top = recent_calls.get()
                await wait_until(top + every)
            return await func(*args, **kwargs)

        return wrapper

    return decorator
