"""Functions for rounding monetary values. All functions in this module operate on
[`decimal.Decimal`](https://docs.python.org/3/library/decimal.html#decimal-objects)
instances and not money vectors."""

# Rounding algorithm:
#
#     Step 1: Round the decimal value to `places`.
#     Step 2: Left shift the coefficient of the decimal value by `places` to get an integer.
#     Step 3: Divide the integral value by `denomination`.
#     Step 4: Round the quotient to an integer.
#     Step 5: Multiply the value by `denomination`.
#     Step 6: Divide the value by 10 ** `places`, or alternatively, set the exponent of
#         the Decimal object to `-places`.
#
#     Steps 1-5 are taken care of by the `atomic` function since they result in a correctly
#     rounded integral value.

from __future__ import annotations

__all__ = [
    "as_currency",
    "to_places",
    "to_nearest",
    "atomic",
]

import decimal

from linearmoney import cache
from linearmoney.data import CurrencyData

_INTEGRAL_QUANTIZER = decimal.Decimal("1")


def _extract_fractions_data(currency: CurrencyData, cash: bool) -> tuple[int, int]:
    """Return the denomination and places values for the specified currency as a
    2-element tuple."""

    if cash:
        denomination, places = (
            currency.data["cash_denomination"],
            currency.data["cash_places"],
        )
    else:
        denomination, places = currency.data["denomination"], currency.data["places"]
    if places < 0:
        places = 0
    return denomination, places


@cache.cached()
def as_currency(
    amount: decimal.Decimal, currency: CurrencyData, cash: bool = False
) -> decimal.Decimal:
    """Round `amount` based on the denominational data defined by `currency`.

    If `cash` is True, round based on the *cash* denominations defined by `currency`.

    This function rounds the currency based on its smallest denomination. This means
    that certain combinations of values and denominations may give results that appear
    incorrect at first glance. For example, a value of 10.40 with a custom currency
    using denomination=15 and places=2 would give the rounded value 10.35. This seems
    wrong at first since 35 cents is not divisible by 15, but 1035 is divisible by 15, so
    the value is constructable from the smallest denomination available. If the value
    was rounded to the nearest value where the fractional portion was constructible from
    the smallest denomination, this would result in 10.45. 45 is divisible by 15, but
    1045 is not, so the overall amount is not atomically constructable from the smallest
    denomination of the currency. If the application requires rounding whole and fractional
    currency components separately e.g. a point-of-sale system that calculates change, the
    application will have to implement that behavior itself.
    Something along these lines:

    ```python
    import decimal

    places = 2
    denomination = 15

    value = decimal.Decimal("10.40").as_tuple()
    integral_digits = value.digits[:-places]
    fractional_digits = value.digits[-places:]

    one = decimal.Decimal("1")
    fractional_component = decimal.Decimal((value.sign, fractional_digits, 0))
    rounded_fractional = (fractional_component / 15).quantize(one) * 15
    rounded_fractional_digits = rounded_fractional.as_tuple().digits
    rounded_digits = integral_digits + rounded_fractional_digits
    final_value = decimal.Decimal((value.sign, rounded_digits, -places))
    ```

    Example:

        >>> import linearmoney as lm
        >>> fv = lm.vector.forex({"base": "cad", "rates": {"usd": 1}})
        >>> av = lm.vector.asset(10.067777, "cad", lm.vector.space(fv))
        >>> val = lm.vector.evaluate(av, "cad", fv)
        >>> curr = lm.data.currency("cad")
        >>> lm.round.as_currency(val, curr)
        Decimal('10.07')
        >>> lm.round.as_currency(val, curr, cash=True)
        Decimal('10.05')
    """

    denomination, places = _extract_fractions_data(currency, cash=cash)

    if denomination == 0 or denomination == 1:
        return to_places(amount, places)
    else:
        _tup = atomic(amount, currency, cash).as_tuple()
        rounded_value = decimal.Decimal((_tup.sign, _tup.digits, -places))
        return rounded_value


@cache.cached()
def to_places(amount: decimal.Decimal, places: int) -> decimal.Decimal:
    """Round `amount` to a fixed number of decimal `places`.

    A negative value for `places` is treated the same as 0.

    Example:

        >>> import linearmoney as lm
        >>> fv = lm.vector.forex({"base": "cad", "rates": {"usd": 1}})
        >>> av = lm.vector.asset(10.067777, "cad", lm.vector.space(fv))
        >>> val = lm.vector.evaluate(av, "cad", fv)
        >>> lm.round.to_places(val, 3)
        Decimal('10.068')
        >>> lm.round.to_places(val, 2)
        Decimal('10.07')
        >>> lm.round.to_places(val, 1)
        Decimal('10.1')
        >>> lm.round.to_places(val, 0)
        Decimal('10')
        >>> lm.round.to_places(val, -5)
        Decimal('10')
    """

    return amount.quantize(decimal.Decimal("10") ** -places)


@cache.cached()
def to_nearest(amount: decimal.Decimal, value: int) -> decimal.Decimal:
    """Round `amount` to the nearest multiple of `value`.

    This function is useful for financial statements and similar contexts where monetary
    values are displayed in thousands, millions, billions, etc and not as the exact dollar amount.

    Raises:
        ValueError:
            If `value` is not a positive integer (greater than 0).

    Example:

        >>> import linearmoney as lm
        >>> fv = lm.vector.forex({"base": "usd", "rates": {}})
        >>> av = lm.vector.asset("123456789.123456789", "usd", lm.vector.space(fv))
        >>> val = lm.vector.evaluate(av, "usd", fv)
        >>> lm.round.to_nearest(val, 1_000)
        Decimal('123457000')
        >>> lm.round.to_nearest(val, 10_000)
        Decimal('123460000')
        >>> lm.round.to_nearest(val, 1)
        Decimal('123456789')
    """

    if value <= 0:
        raise ValueError("`value` must be positive.")
    return (amount / value).quantize(_INTEGRAL_QUANTIZER) * value


@cache.cached()
def atomic(
    amount: decimal.Decimal, currency: CurrencyData, cash: bool = False
) -> decimal.Decimal:
    """Return the integral value of `amount` in its smallest denomination as defined by
    the `currency` data.

    If `cash` is True, return the value in the smallest *cash* denomination defined by
    `currency`.

    Example:

        >>> import linearmoney as lm
        >>> fv = lm.vector.forex({"base": "cad", "rates": {"usd": 1}})
        >>> av = lm.vector.asset(10.07, "cad", lm.vector.space(fv))
        >>> val = lm.vector.evaluate(av, "cad", fv)
        >>> curr = lm.data.currency("cad")
        >>> lm.round.atomic(val, curr)
        Decimal('1007')
        >>> lm.round.atomic(val, curr, cash=True)
        Decimal('1005')
    """

    denomination, places = _extract_fractions_data(currency, cash=cash)

    _quantized_value = amount.quantize(decimal.Decimal("10") ** -places)
    _integral_value = _quantized_value.shift(places)
    if denomination == 0 or denomination == 1:
        return _integral_value.quantize(_INTEGRAL_QUANTIZER)
    else:
        return to_nearest(_integral_value, denomination)
