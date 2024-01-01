"""Exception classes raised by the linearmoney library."""

from __future__ import annotations

__all__ = [
    "SpaceError",
    "IntegrityError",
    "UnknownDataError",
    "CacheError",
]


class SpaceError(Exception):
    """An operation between vectors in two different spaces
    was attempted."""

    def __init__(self, msg: str) -> None:
        return super().__init__(msg)


class IntegrityError(Exception):
    """An operation that would result in breaking the
    mathematical invariants of the linear money model was attempted."""

    def __init__(self, msg: str) -> None:
        return super().__init__(msg)


class UnknownDataError(Exception):
    """An operation using unavailable data was attempted.

    For example, localizing to a locale that we don't have formatting data for,
    or rounding to a currency that we don't have denominational data for.
    """

    def __init__(self, msg: str) -> None:
        return super().__init__(msg)


class CacheError(Exception):
    """A caching operation failed."""

    def __init__(self, msg: str) -> None:
        super().__init__(msg)
