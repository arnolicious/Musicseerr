"""Singleton decorator and automatic cleanup registry for DI providers."""

from __future__ import annotations

from functools import lru_cache, wraps
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable)

_singleton_registry: list[Callable] = []


def singleton(fn: F) -> F:
    """Wrap *fn* with ``@lru_cache(maxsize=1)`` and register it for automatic cleanup."""
    cached = lru_cache(maxsize=1)(fn)
    _singleton_registry.append(cached)

    @wraps(fn)
    def wrapper(*args, **kwargs):
        return cached(*args, **kwargs)

    # Expose cache_clear so callers can invalidate individual singletons
    wrapper.cache_clear = cached.cache_clear  # type: ignore[attr-defined]
    wrapper.cache_info = cached.cache_info  # type: ignore[attr-defined]
    wrapper._cached = cached  # type: ignore[attr-defined]
    _singleton_registry[-1] = wrapper  # replace with the wrapper so clear_all hits wrapper
    return wrapper  # type: ignore[return-value]


def clear_all_singletons() -> None:
    """Call ``cache_clear()`` on every registered singleton provider."""
    for fn in _singleton_registry:
        cache_clear = getattr(fn, "cache_clear", None)
        if callable(cache_clear):
            cache_clear()
