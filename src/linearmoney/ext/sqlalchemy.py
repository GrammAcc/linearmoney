"""SQLAlchemy ORM integrations for linearmoney."""

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
    (VARCHAR) underneath, so in-db aggregate functions like SUM and MAX/MIN cannot
    be used and these operations need to be performed in Python if they are needed.

    Examples:
        >>> from sqlalchemy.orm import (
        >>>     Mapped,
        >>>     mapped_column,
        >>>     DeclarativeBase,
        >>> )
        >>>
        >>> from linearmoney.ext.sqlalchemy import VectorMoney
        >>>
        >>> class LMExample(DeclarativeBase):
        >>>
        >>>     __tablename__ = "lm_example"
        >>>
        >>>     id: Mapped[int] = mapped_column(primary_key=True)
        >>>     money_column: Mapped[VectorMoney] = mapped_column(VectorMoney)
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: lm.vector.MoneyVector, dialect: Dialect):
        return lm.vector.store(value)

    def process_result_value(self, value: String, dialect: Dialect):
        return lm.vector.restore(value)


class AtomicMoney(TypeDecorator):
    """SQLAlchemy column type that automatically serializes and
    deserializes a `linearmoney.vector.MoneyVector` as an atomic value in the smallest
    denomination of `currency` to and from an integer column for storage in the db.

    This type is intended to be used with single-currency applications. It
    evaluates the stored asset vector in a single-currency space defined by
    the `currency` argument provided on column declaration.

    This means that attempting to store a money vector from a different currency space
    will result in a `linearmoney.Exceptions.SpaceError`.

    The advantage of this column type is that it allows the use of in-db aggregate
    functions like SUM and MAX/MIN. The disadvantage is that it can only be used
    with single-currency applications or with a manual conversion step before
    passing any values into sqlalchemy's column operations. For this reason,
    multi-currency applications should generally choose `VectorMoney` instead.

    Examples:
        >>> from sqlalchemy.orm import (
        >>>     Mapped,
        >>>     mapped_column,
        >>>     DeclarativeBase,
        >>> )
        >>>
        >>> import lienarmoney as lm
        >>> from linearmoney.ext.sqlalchemy import AtomicMoney
        >>>
        >>> CURRENCY = lm.data.currency("USD")
        >>> class LMExample(DeclarativeBase):
        >>>
        >>>     __tablename__ = "lm_example"
        >>>
        >>>     id: Mapped[int] = mapped_column(primary_key=True)
        >>>     money_column: Mapped[AtomicMoney] = mapped_column(AtomicMoney(CURRENCY))
    """

    impl = Integer
    cache_ok = True

    currency: lm.data.CurrencyData
    forex: lm.vector.ForexVector
    space: lm.vector.CurrencySpace

    def __init__(self, currency: lm.data.CurrencyData, *args, **kwargs) -> None:
        super().__init__()
        self.currency = currency
        self.forex = lm.vector.forex({"base": currency.iso_code, "rates": {}})
        self.space = lm.vector.space(self.forex)

    def process_bind_param(self, value: lm.vector.MoneyVector, dialect: Dialect):
        return lm.scalar.atomic(
            lm.vector.evaluate(value, self.currency.iso_code, self.forex),
            self.currency,
        )

    def process_result_value(self, value: Integer, dialect: Dialect):
        exponent = decimal.Decimal(10) ** decimal.Decimal(self.currency.data["places"])
        decimal_value = decimal.Decimal(value) / exponent
        return lm.vector.asset(decimal_value, self.currency.iso_code, self.space)
