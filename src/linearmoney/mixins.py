from __future__ import annotations

__all__: list[str] = [
    "ImmutableDeduplicationMixin",
    "EqualityByHashMixin",
]


from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, ClassVar
from collections.abc import Hashable, Sequence

if TYPE_CHECKING:
    from typing import Self


class ImmutableDeduplicationMixin:
    """A mixin class that provides common dunder method implementations for
    logically immutable objects.

    Provides recursive implementations of `__getstate__` and
    `__setstate__` based on the `__slots__` declared on the class and all of its
    ancestors in order to fully support pickling without having
    to implement the methods in every class and provides implementations of `__copy__`
    and `__deepcopy__` that simply return self since copying makes no difference for
    immutable objects.
    """

    __slots__: ClassVar[Sequence[str]] = []

    def __getstate__(self) -> dict:
        state = {}
        for i in self.__class__.mro():
            sl = getattr(i, "__slots__", None)
            if sl is not None:
                for j in sl:
                    obj = getattr(self, j, None)
                    state[j] = obj
        return state

    def __setstate__(self, state: dict) -> None:
        for k, v in state.items():
            setattr(self, k, v)

    def __copy__(self) -> Self:
        # Just return self since we're immutable.
        return self

    def __deepcopy__(self, memo: dict = {}) -> Self:
        # Just return self since we're immutable.
        return self


class EqualityByHashMixin(metaclass=ABCMeta):
    """Mixin class that adds equality comparison support for user-defined hashable
    classes.

    Adding this mixin to a class will add a basic implementation of
    `__eq__` and `__ne__` which will compare objects for equality by hash
    instead of `id`. Only user defined classes that override
    `object.__hash__` should inherit from this mixin.

    This mixin does not add any of the ordered comparison operators
    (<, >, <=, >=), only equality comparison is added.
    """

    __slots__: ClassVar[Sequence[str]] = []

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Hashable):
            return hash(self) == hash(other)
        else:
            return NotImplemented  # pragma: no cover

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Hashable):
            return hash(self) != hash(other)
        else:
            return NotImplemented  # pragma: no cover

    @abstractmethod
    def __hash__(self) -> int:
        raise NotImplementedError
