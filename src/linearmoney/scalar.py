from __future__ import annotations

__all__ = [
    "l10n",
]

import decimal

from linearmoney import cache
from linearmoney.data import CurrencyData, LocaleData

# TODO: Move l10n functionality to dedicated module.


@cache.cached()
def _format_grouping(rounded_value: decimal.Decimal, locale: LocaleData) -> str:
    """Format `rounded_value` based on the grouping and separator data of `locale`."""

    _sign = "positive" if rounded_value >= 0 else "negative"

    # TODO: Refactor this function for readability.
    str_value = str(rounded_value).strip("-").strip("+")
    decimal_separator = ""
    grouping_separator = locale.data["grouping_separator"]
    grouping = locale.data["_".join([_sign, "grouping"])]  # type: ignore[literal-required]
    decimal_split = str_value.split(".")
    decimal_part = ""
    if len(decimal_split) > 1:
        decimal_separator = locale.data["decimal_separator"]
        decimal_part = decimal_split[1]
    integer_part_string = decimal_split[0]
    formatted_number = ""
    if len(integer_part_string) <= grouping[0] or grouping == [-1]:
        formatted_number = f"{decimal_separator}".join(
            [integer_part_string, decimal_part]
        )
    else:
        integer_part = list(integer_part_string)
        integer_part.reverse()
        integer_split: list = []
        count = 0
        for i in reversed(grouping):
            if len(integer_part[count:]) < i:
                break
            integer_split.append(integer_part[count : count + i])
            count += i
        last_index = grouping[0]
        tmp_list = [
            integer_part[i : i + last_index]
            for i in range(count, len(integer_part), last_index)
        ]
        integer_split += tmp_list

        integer_split = ["".join(integer_split[i]) for i in range(len(integer_split))]

        reversed_integer_part = f"{grouping_separator}".join(integer_split)
        integer_part = list(reversed_integer_part)
        integer_part.reverse()
        formatted_integer_part = "".join(integer_part)
        formatted_number = f"{decimal_separator}".join(
            [formatted_integer_part, decimal_part]
        )
    return formatted_number


@cache.cached()
def l10n(
    amount: decimal.Decimal,
    currency: CurrencyData,
    locale: LocaleData,
    *,
    international: bool = False,
) -> str:
    """Localize `amount` to a currency-formatted string based on the `locale` and
    `currency` data.

    Args:
        amount:
            The decimal value to format. This will usually be a rounded decimal value
            resulting from a call to `linearmoney.round.as_currency` or
            `linearmoney.round.to_places`, but it doesn't have to be.
        currency:
            The `linearmoney.data.CurrencyData`
            of the currency that the `amount` represents.
        locale:
            The `linearmoney.data.LocaleData` to use for formatting the result.
        international:
            Keyword-only argument. If False (default), then use the currency symbol for
            the target currency in the result and respect the `symbol_space` value of
            the `locale` data. If True, then use the international format with the
            ISO 4217 alpha currency code in place of the symbol and a space between
            the value and the symbol regardless of the value of the `symbol_space`
            data for the `locale`.

    Example:

        >>> import linearmoney as lm
        >>> fv = lm.vector.forex({"base": "cad", "rates": {"eur": 2}})  # 1 CAD -> 2 EUR
        >>> av = lm.vector.asset(10.067777, "cad", lm.vector.space(fv))
        >>> en_US = lm.data.locale("en", "us")  # English-United States
        >>> cad = lm.data.currency("cad")
        >>> val = lm.vector.evaluate(av, "cad", fv)
        >>> rounded_val = lm.round.as_currency(val, cad)
        >>> lm.scalar.l10n(rounded_val, cad, en_US)
        'CA$10.07'
        >>> cash_rounded_val = lm.round.as_currency(val, cad, cash=True)
        >>> lm.scalar.l10n(cash_rounded_val, cad, en_US)
        'CA$10.05'
        >>> lm.scalar.l10n(rounded_val, cad, en_US, international=True)
        'CAD 10.07'
        >>> fr_FR = lm.data.locale("fr", "fr")  # French-France
        >>> eur = lm.data.currency("eur")
        >>> val = lm.vector.evaluate(av, "eur", fv)
        >>> rounded_val = lm.round.as_currency(val, eur)
        >>> lm.scalar.l10n(rounded_val, eur, fr_FR)
        '20,14 €'
        >>> cash_rounded_val = lm.round.as_currency(val, eur, cash=True)
        >>> lm.scalar.l10n(cash_rounded_val, eur, fr_FR)
        '20,14 €'
        >>> lm.scalar.l10n(rounded_val, eur, fr_FR, international=True)
        '20,14 EUR'
    """

    # TODO: Refactor this function for readability.

    iso_code = currency.iso_code

    _sign = "positive" if amount >= 0 else "negative"

    lc_data = locale.data

    sign = lc_data["_".join([_sign, "sign"])]  # type: ignore[literal-required]
    symbol_before = lc_data["_".join([_sign, "symbol_before"])]  # type: ignore[literal-required]
    symbol_space = lc_data["_".join([_sign, "symbol_space"])]  # type: ignore[literal-required]
    sign_position = lc_data["_".join([_sign, "sign_position"])]  # type: ignore[literal-required]

    if not international:
        _currency_symbol = lc_data["currency_symbols"][iso_code]
        if _currency_symbol is None:
            international = True
        else:
            currency_symbol = _currency_symbol
    if international:
        currency_symbol = iso_code
        symbol_space = 1
        if sign_position == 1 and symbol_before:
            sign_position = 4
            symbol_space = 2

    join_list = []
    if sign_position == 3:
        if symbol_space == 2:
            currency_symbol = " ".join([sign, currency_symbol])
        else:
            currency_symbol = "".join([sign, currency_symbol])
    elif sign_position == 4:
        if symbol_space == 2:
            currency_symbol = " ".join([currency_symbol, sign])
        else:
            currency_symbol = "".join([currency_symbol, sign])

    if symbol_space == 1:
        join_list = [
            currency_symbol,
            " ",
            _format_grouping(amount, locale),
        ]
    else:
        join_list = [
            currency_symbol,
            _format_grouping(amount, locale),
        ]

    if not symbol_before:
        join_list.reverse()

    match sign_position:
        case 0:
            join_list.insert(0, "(")
            join_list.append(")")
        case 1:
            if symbol_space == 2 and not symbol_before:
                join_list.insert(0, "".join([sign, " "]))
            else:
                join_list.insert(0, sign)
        case 2:
            if symbol_space == 2 and symbol_before:
                join_list.append("".join([" ", sign]))
            else:
                join_list.append(sign)
    return "".join(join_list)
