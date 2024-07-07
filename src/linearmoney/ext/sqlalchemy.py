"""SQLAlchemy ORM integrations for linearmoney.

Install with `pip install "linearmoney[sqlalchemy]"`.
"""

__all__ = [
    "VectorMoney",
    "AtomicMoney",
]

import decimal

from sqlalchemy.types import TypeDecorator, String, Integer
from sqlalchemy import Dialect

import linearmoney as lm


class VectorMoney(TypeDecorator):
    """SQLAlchemy column type that automatically serializes and
    deserializes a `linearmoney.vector.MoneyVector` to and from a String column
    for storage in the db.

    This type preserves all vector information including the currency space, so
    it should be used whenever non-destructive storage is desired.

    The disadvantage of this column type is that it uses a sqlalchemy String column
    (VARCHAR) underneath, so in-db aggregate functions like SUM and MAX cannot
    be used and these operations need to be performed in Python if they are needed.

    Another consequence of this is that comparisons in where clauses don't work as
    expected. For example,
    `select(VectorModel).where(VectorModel.money_column > money_vector)` will compare
    the serialized string of `money_vector` against the string stored in the db for the
    greater than operator, so it will not give a correct result based on the actual
    monetary values of the vectors.

    Examples:
        >>> from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
        >>>
        >>> from linearmoney.ext.sqlalchemy import VectorMoney
        >>>
        >>> class BaseModel(DeclarativeBase): ...
        >>>
        >>> class LMExample(BaseModel):
        ...
        ...     __tablename__ = "lm_example"
        ...
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     money_column: Mapped[VectorMoney] = mapped_column(VectorMoney)
    """

    impl = String

    # We add an empty docstring to `cache_ok`, so that pdoc doesn't
    # include the parent class' docstring.
    cache_ok = True
    """"""

    # SQLAlchemy types `value` argument as Any | None, which makes sense for an overload.
    # We ignore the override error because violating Liskov doesn't make any difference
    # when the argument isn't typed.
    def process_bind_param(
        self, value: lm.vector.MoneyVector, dialect: Dialect  # type: ignore[override]
    ):
        """Serialize the `MoneyVector` to a `str` compatible with the sqlalchemy `String`
        column type."""

        if value is not None:
            return lm.vector.store(value)
        return value

    # SQLAlchemy types `value` argument as Any | None, which makes sense for an overload.
    # We ignore the override error because violating Liskov doesn't make any difference
    # when the argument isn't typed.
    def process_result_value(self, value: str, dialect: Dialect):  # type: ignore[override]
        """Deserialize the `str` stored in the db to a `MoneyVector` equivalent to the vector
        that was originally stored."""

        if value is not None:
            return lm.vector.restore(value)
        return value


class AtomicMoney(TypeDecorator):
    """SQLAlchemy column type that automatically serializes and
    deserializes a `linearmoney.vector.MoneyVector` as an atomic value in the smallest
    denomination of `currency` to and from an integer column for storage in the db.

    This type is intended to be used with single-currency applications. It
    evaluates the stored asset vector in a single-currency space defined by
    the `currency` argument provided on column declaration.

    This means that attempting to store a money vector from a different currency space
    will result in a `linearmoney.exceptions.SpaceError`.

    The reason for using a single-currency space in the internal calculations instead
    of checking the space of the passed in vector is to ensure that
    the value read from the database is the same value that was written to it.

    For example, if we store a vector of (0 EUR, 10 USD,) in an AtomicMoney column
    for USD, then it will store the integer 1000 in the database. We will get the
    same value stored if we store a vector of (10 USD,). The difference is that
    we lose the information about the currency space when storing the value as an
    integer, so when we read the values from the db, both with deserialize to (10 USD,).
    By enforcing a single-currency space on write, we ensure that the values read
    from the database are actually the values that were written to the database, and
    we ensure that the integrity of math on those values will not be compromised
    through any subsequent writes/reads to/from the database.

    The main advantage of this column type is that it allows the use of in-db aggregate
    functions like SUM and MAX as well as ordered comparisons. The disadvantage is
    that it can only be used with single-currency applications or with a manual
    conversion step before passing any values into sqlalchemy's column operations.
    For this reason, multi-currency applications should generally choose `VectorMoney`
    instead.

    Examples:
        >>> from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
        >>>
        >>> import linearmoney as lm
        >>> from linearmoney.ext.sqlalchemy import AtomicMoney
        >>>
        >>> class BaseModel(DeclarativeBase): ...
        >>>
        >>> CURRENCY = lm.data.currency("USD")
        >>>
        >>> class LMExample(BaseModel):
        ...
        ...     __tablename__ = "lm_example"
        ...
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     money_column: Mapped[AtomicMoney] = mapped_column(AtomicMoney(CURRENCY))
    """

    impl = Integer
    # We add an empty docstring to `cache_ok`, so that pdoc doesn't
    # include the parent class' docstring.
    cache_ok = True
    """"""

    _currency: lm.data.CurrencyData

    _forex: lm.vector.ForexVector
    _space: lm.vector.CurrencySpace

    def __init__(self, currency: lm.data.CurrencyData, *args, **kwargs) -> None:
        """"""
        super().__init__()
        self._currency = currency
        self._forex = lm.vector.forex({"base": currency.iso_code, "rates": {}})
        self._space = lm.vector.space(self.forex)

    @property
    def currency(self) -> lm.data.CurrencyData:
        """The `CurrencyData` provided in the column constructor.

        Defines the single-currency `forex` and `space` for converting
        the `MoneyVector` into an integer on serialization."""

        return self._currency

    @property
    def forex(self) -> lm.vector.ForexVector:
        """The `ForexVector` representing the single-currency
        rates used to convert the `MoneyVector` to and from an integer."""

        return self._forex

    @property
    def space(self) -> lm.vector.CurrencySpace:
        """The single-currency `CurrencySpace` used to convert the
        `MoneyVector` to and from an integer."""

        return self._space

    # SQLAlchemy types `value` argument as Any | None, which makes sense for an overload.
    # We ignore the override error because violating Liskov doesn't make any difference
    # when the argument isn't typed.
    def process_bind_param(
        self, value: lm.vector.MoneyVector, dialect: Dialect  # type: ignore[override]
    ):
        """Serialize the `MoneyVector` to an `int` for storage in the sqlalchemy `Integer`
        column type."""

        if value is not None:
            return lm.scalar.atomic(
                lm.vector.evaluate(value, self.currency.iso_code, self.forex),
                self.currency,
            )
        return value

    # SQLAlchemy types `value` argument as Any | None, which makes sense for an overload.
    # We ignore the override error because violating Liskov doesn't make any difference
    # when the argument isn't typed.
    def process_result_value(self, value: int, dialect: Dialect):  # type: ignore[override]
        """Deserialize the `int` stored in the db to a `MoneyVector` equivalent to the vector
        that was originally stored."""

        if value is not None:
            exponent = decimal.Decimal(10) ** decimal.Decimal(
                self.currency.data["places"]
            )
            decimal_value = decimal.Decimal(value) / exponent
            return lm.vector.asset(decimal_value, self.currency.iso_code, self.space)
        return value
