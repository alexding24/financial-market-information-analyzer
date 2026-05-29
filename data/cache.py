from __future__ import annotations

from functools import wraps
from threading import RLock
from time import monotonic
from typing import Any, Callable, TypeVar


F = TypeVar("F", bound=Callable[..., Any])


def _make_hashable(value: Any) -> Any:
    try:
        hash(value)
        return value
    except TypeError:
        if isinstance(value, dict):
            return tuple(sorted((_make_hashable(key), _make_hashable(item)) for key, item in value.items()))
        if isinstance(value, (list, set, tuple)):
            return tuple(_make_hashable(item) for item in value)
        return repr(value)


def ttl_cache(seconds: int) -> Callable[[F], F]:
    cache: dict[tuple[Any, ...], tuple[float, Any]] = {}
    lock = RLock()

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = _make_hashable(args) + _make_hashable(tuple(sorted(kwargs.items())))
            now = monotonic()
            with lock:
                cached = cache.get(key)
                if cached and now - cached[0] < seconds:
                    return cached[1]

            value = func(*args, **kwargs)
            with lock:
                cache[key] = (now, value)
            return value

        return wrapper  # type: ignore[return-value]

    return decorator
