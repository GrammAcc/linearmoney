"""This module provides access to the custom least recently used caching system used
by functions in the linearmoney package."""

from __future__ import annotations

__all__ = [
    "cached",
    "enable",
    "is_enabled",
    "head",
    "tail",
    "invalidate",
    "size",
    "max_size",
    "get_base_size",
    "set_base_size",
]

import logging

import decimal
import threading

import functools
from collections import OrderedDict
from collections.abc import Hashable, Callable, Mapping
from typing import (
    TypeVar,
    ParamSpec,
    SupportsInt,
    Any,
)

from linearmoney.exceptions import CacheError

logger = logging.getLogger(__name__)

_thread_local_data = threading.local()


class _LRUFuncCache(OrderedDict):
    """OrderedDict representing the lru cache of a specific function."""

    __slots__ = [
        "_funcname",
        "_size_multiplier",
    ]

    def __init__(
        self,
        from_store: Mapping = {},
        *,
        funcname: str,
        size_multiplier: int | float = 1,
    ) -> None:
        super().__init__(from_store)
        self._funcname = funcname
        self._size_multiplier = size_multiplier

    @property
    def max_size(self) -> int:
        """**Read-only**: The maximum number of cache
        entries for this `LRUStore`.

        Calculated: `base_size` * `size_multiplier` = `max_size`
        """

        return int(get_base_size() * self.size_multiplier)

    @property
    def size_multiplier(self) -> int | float:
        """**Read-only**: Contributes to dynamic `max_size`."""

        return self._size_multiplier

    @property
    def size(self) -> int:
        """Read-only: the current number of values cached on this instance."""

        return len(self)

    @property
    def head(self) -> Any:
        """Read-only: the cached value at the current *head* (least recently used)
        position."""

        return self[next(iter(self))]

    @property
    def tail(self) -> Any:
        """Read-only: the cached value at the current *tail* (most recently used)
        position."""

        return self[next(iter(reversed(self)))]

    def is_cached(self, cache_key: tuple) -> bool:
        return cache_key in self

    def write(self, cache_key: tuple, value: Any) -> None:
        """Cache a new value to this store.

        Args:
            cache_key
                The tuple key used to lookup the value within this funccache.
            value
                The value to be stored in this funccache.
        """

        self[cache_key] = value
        self.move_to_end(cache_key)
        if self._overfull():
            logger.warning(
                f"{self._funcname}: \
cache full on write(key={cache_key}, value={value})."
            )
            self._remove_head()

    def _overfull(self) -> bool:
        return len(self) > self.max_size

    def _remove_head(self) -> None:
        del self[next(iter(self))]

    def read(self, cache_key: tuple) -> Any:
        """Fetch a cached value from this store.

        Args:
            cache_key
                The tuple key used to lookup the value within this funccache.

        Returns:
            Any

            The value stored by `cache_key` in this store.
        """

        read_value = self[cache_key]
        self.move_to_end(cache_key)
        return read_value


def _get_cachedict() -> dict[str, _LRUFuncCache]:
    """Return the `cachedict` for the calling thread."""

    global _thread_local_data
    ca = getattr(_thread_local_data, "cachedict", None)
    if ca is None:
        _thread_local_data.cachedict = {}
    return _thread_local_data.cachedict


def _get_funccache(cached_func: Callable) -> _LRUFuncCache:
    """Return the cache for the `cached_func`.

    Raises:
        `linearmoney.exceptions.CacheError`:
            If there is no cache for `cached_func` in the current thread's `cachedict`.
    """

    _cachedict = _get_cachedict()
    funcname = cached_func.__qualname__
    try:
        return _cachedict[funcname]
    except KeyError:
        raise CacheError(f"Individual cache for: {funcname} not found.")


def invalidate(cached_func: Callable | None = None) -> None:
    """Invalidate the cache.

    Args:
        cached_func:
            If None (default), invalidate the entire cache for the calling thread.
            If not `None`, invalidate only the cache for the specified function in the
            calling thread.
    Raises:
        `linearmoney.exceptions.CacheError`:
            If the function passed as `cached_func` isn't cached.
            Individual caches are created dynamically, so this can happen if
            `cached_func` has not been called yet, but this is very unlikely in most
            applications.
    """

    if cached_func is None:
        for funccache in _get_cachedict().values():
            funccache.clear()
    else:
        _get_funccache(cached_func).clear()


_is_enabled = True


def enable(enable: bool) -> None:
    """Enable/disable package-wide caching."""

    if threading.current_thread() == threading.main_thread():
        global _is_enabled
        _is_enabled = enable
    else:
        global _thread_local_data
        _thread_local_data.is_enabled = enable


def is_enabled() -> bool:
    if threading.current_thread() == threading.main_thread():
        return _is_enabled
    else:
        global _thread_local_data
        ca = getattr(_thread_local_data, "is_enabled", None)
        if ca is None:
            _thread_local_data.is_enabled = _is_enabled
        return _thread_local_data.is_enabled


_base_size = 256


def get_base_size() -> int:
    """The current `base_size` for the cache.

    This value is used to calculate the dynamic `max_size` of each individual
    function cache. E.g. a function with 2.0 as its `size_multiplier` in the `cached`
    decorator will have `floor(2.0 * get_base_size())` maximum cache entries.
    """

    if threading.current_thread() == threading.main_thread():
        return _base_size
    else:
        global _thread_local_data
        ca = getattr(_thread_local_data, "base_size", None)
        if ca is None:
            _thread_local_data.base_size = _base_size
        return _thread_local_data.base_size


def set_base_size(new_base_size: int) -> None:
    """Set the current `base_size` for the cache.

    Raises:
        TypeError:
            If `new_base_size` doesn't support int.
    """

    if not isinstance(new_base_size, SupportsInt):
        raise TypeError(
            f"set_base_size(): Expected `SupportsInt`, \
got {type(new_base_size)}"
        )
    if threading.current_thread() == threading.main_thread():
        global _base_size
        _base_size = int(new_base_size)
    else:
        global _thread_local_data
        _thread_local_data.base_size = int(new_base_size)


def max_size(cached_func: Callable) -> int:
    """Return the maximum number of cache entries for the cache of the `cached_func`.

    Raises:
        `linearmoney.exceptions.CacheError`:
            If `cached_func` isn't cached.
            Individual caches are created dynamically, so this can happen if
            `cached_func` has not been called yet, but this is very unlikely in most
            applications.
    """

    return _get_funccache(cached_func).max_size


def size(cached_func: Callable | None = None) -> int:
    """The current size of the requested cache.

    Args:
        cached_func:
            If `None` (default) return the total combined size of all function caches,
            else return the total number of cached values for the cache of
            `cached_func`.
    Raises:
        `linearmoney.exceptions.CacheError`:
            If `cached_func` is not `None` and the function is not cached.
            Individual caches are created dynamically, so this can happen if
            `cached_func` has not been called yet, but this is very unlikely in most
            applications.
    """

    if cached_func is None:
        accumulator = 0
        for funccache in _get_cachedict().values():
            accumulator += funccache.size
        return accumulator
    else:
        return _get_funccache(cached_func).size


def head(cached_func: Callable) -> Any:
    """The cached value at the *head* (least recently used) position of the cache
    for `cached_func`.

    This is the value that will be removed from the cache if the `max_size` for
    `cached_func` is reached.

    Raises:
        `linearmoney.exceptions.CacheError`:
            If the passed function is not cached.
            Individual caches are created dynamically, so this can happen if
            `cached_func` has not been called yet, but this is very unlikely in most
            applications.
    """

    return _get_funccache(cached_func).head


def tail(cached_func: Callable) -> Any:
    """The cached value at the *tail* (most recently used) position of the cache
    for `cached_func`.

    Raises:
        `linearmoney.exceptions.CacheError`:
            If the passed function is not cached.
            Individual caches are created dynamically, so this can happen if
            `cached_func` has not been called yet, but this is very unlikely in most
            applications.
    """

    return _get_funccache(cached_func).tail


# Needed for type checking cache decorators.
T = TypeVar("T")
P = ParamSpec("P")


def _hit(
    func: Callable[P, T],
    *args,
    size_multiplier: int | float,
    **kwargs,
) -> T:
    """Hit the cache.

    If a call to func with equivalent arguments has already been made, return the
    cached value, else call `func`, cache the value, and return it.

    If `func` has not been called yet at all, create a new _LRUFuncCache for `func`
    and cache the value of the current call.

    The argument parsing portion of this function includes a check for numeric types
    like `decimal.Decimal` that makes sure that precision is taken into account when
    hashing arguments, so that for example, a rounding function that takes a decimal
    quantizer as an argument does not give the same result for decimals with different
    numbers of trailing zeros but the same actual value.
    """

    _funccache: _LRUFuncCache
    try:
        _funccache = _get_funccache(func)
    except CacheError:
        _funccache = _LRUFuncCache(
            funcname=func.__qualname__, size_multiplier=size_multiplier
        )
        _get_cachedict()[func.__qualname__] = _funccache
    key_accumulator: list[Hashable] = []
    if args:
        for i in args:
            if isinstance(i, Hashable):
                if isinstance(i, decimal.Decimal):
                    # Ensure Decimals of different precision are treated separately.
                    key_accumulator.append(str(i))
                else:
                    # Other supported numeric types need to be distinguished from
                    # unsupported numeric types with the same value.
                    # `id` is included to avoid natural hash collisions between numbers
                    # of the same type but different values. E.g. -1 and -2
                    key_accumulator.append((type(i), i, id(i)))
            else:
                key_accumulator.append(repr(i))
    if kwargs:
        for k, v in kwargs.items():
            if isinstance(v, Hashable):
                if isinstance(v, decimal.Decimal):
                    # Ensure Decimals of different precision are treated separately.
                    key_accumulator.append((k, str(v)))
                else:
                    # Other supported numeric types need to be distinguished from
                    # unsupported numeric types with the same value.
                    key_accumulator.append((k, type(v), v))
            else:
                key_accumulator.append((k, repr(v)))
    cache_key = tuple(key_accumulator)
    if not _funccache.is_cached(cache_key):
        value = func(*args, **kwargs)
        _funccache.write(cache_key, value)
        return value
    else:
        return _funccache.read(cache_key)


def cached(
    size_multiplier: int | float = 1,
) -> Callable[[Callable[P, T]], Callable[P, T]]:  # pragma: no cover
    """Used just like the `functools.lru_cache` decorator, but it allows unhashable
    types and has some special handling for numeric types, and in particular
    `decimal.Decimal` that takes precision into account, so that e.g. a rounding
    function that expects a decimal as an argument to be used in a
    `decimal.Decimal.quantize()` call will not treat two `decimal.Decimal`s with
    different trailing zeros as the same argument even if they have the same value."""

    def _outer_wrapper(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def _inner_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if is_enabled():
                return _hit(
                    func,
                    size_multiplier=size_multiplier,
                    *args,
                    **kwargs,
                )
            else:
                return func(*args, **kwargs)

        return _inner_wrapper

    return _outer_wrapper
