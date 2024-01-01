"""Helper functions used internally by the linearmoney package."""

from __future__ import annotations


__all__: list[str] = [
    "coerce_decimal",
    "get_supported_numeric",
    "is_supported_numeric",
    "perf",
]

import decimal
import time
import logging
from functools import singledispatch
from typing import Callable, TypeVar, ParamSpec

perf_logger = logging.getLogger("performance")
file_handler = logging.FileHandler(
    "performance.log",
    mode="w",
    encoding="utf-8",
    delay=True,
)
perf_logger.setLevel(logging.DEBUG)
file_handler.setLevel(logging.DEBUG)
perf_logger.addHandler(file_handler)

T = TypeVar("T")
P = ParamSpec("P")
iterations = [10, 100, 1_000, 10_000, 100_000, 1_000_000]


def perf(func: Callable[P, T], *args, **kwargs) -> None:
    for i in iterations:
        start = time.perf_counter_ns()
        for j in range(i):
            func(*args, **kwargs)
        end = time.perf_counter_ns()
        elapsed = end - start
        perf_logger.debug(
            "".join(
                [
                    func.__qualname__,
                    ": Iterations - ",
                    str(i),
                    ", Runtime - ",
                    str(elapsed),
                ]
            )
        )


@singledispatch
def coerce_decimal(number) -> decimal.Decimal:
    """Generic function to convert registered types to `decimal.Decimal` instances.

    New types can be registered with `coerce_decimal.register` at runtime, but this will
    likely break static type checking, so it is not recommended.
    See the documentation for
    [`functools.singledispatch`](https://docs.python.org/3/library/functools.html#functools.singledispatch)
    for details on usage.

    Default registered types are: `int`, `float`, `decimal.Decimal`, and
    `str`.

    Notes:
        - `str` is registered to allow valid string inputs to the `decimal.Decimal`
        constructor to be more easily checked as valid numeric input, but strings that
        are invalid as input to the `decimal.Decimal` constructor will still raise a
        `NotImplementedError` unless the user registers a new function for
        the `str` type to implement the conversion.
    """

    raise NotImplementedError


@coerce_decimal.register
def _force_int_to_decimal(
    number: int,
) -> decimal.Decimal:
    return decimal.Decimal(number)


@coerce_decimal.register
def _force_float_to_decimal(number: float) -> decimal.Decimal:
    return decimal.Decimal(str(number))


@coerce_decimal.register
def _force_decimal_to_decimal(number: decimal.Decimal) -> decimal.Decimal:
    return number


@coerce_decimal.register
def _force_numeric_string_to_decimal(number: str) -> decimal.Decimal:
    try:
        return decimal.Decimal(number)
    except decimal.InvalidOperation:
        raise NotImplementedError


def get_supported_numeric() -> tuple[type, ...]:
    """A tuple of all types that can be safely converted to `decimal.Decimal` by the
    linearmoney package at runtime.

    Corresponds to the types registered to the `coerce_decimal` generic
    function.
    """

    supported_classes = dict(coerce_decimal.registry)
    del supported_classes[object]
    return tuple(supported_classes)


def is_supported_numeric(value: object) -> bool:
    """Determines if a variable is of a type that can be safely converted to Decimal
    at runtime through the `coerce_decimal` generic function."""

    return type(value) in get_supported_numeric()
