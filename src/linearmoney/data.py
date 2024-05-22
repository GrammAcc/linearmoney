from __future__ import annotations

__all__ = [
    "locale",
    "system_locale",
    "currency",
    "FormatType",
    "DataMap",
    "LocaleMap",
    "LocaleData",
    "CurrencyMap",
    "CurrencyData",
]

import copy
import enum
from collections.abc import MutableMapping, Mapping
from typing import TypedDict, Any, cast
from dataclasses import dataclass
import locale as posix_locale

from linearmoney import cache, resources
from linearmoney.mixins import ImmutableDeduplicationMixin, EqualityByHashMixin
from linearmoney.exceptions import UnknownDataError


# This class needs to have a docstring, or the doctest examples in
# the parent class `enum.Enum` will fail due to bare `Enum` not
# being available in the test namespace.
class FormatType(enum.Enum):
    """Enum representing the allowed locale formats.

    Primarily used to select l10n data with the `locale` function.
    """

    STANDARD = "standard"
    ACCOUNTING = "accounting"

    def __str__(self) -> str:
        return self.value


class DataMap(EqualityByHashMixin, ImmutableDeduplicationMixin, Mapping):
    """A read-only mapping."""

    __slots__ = ["_data", "_data_repr", "_hash"]

    def __init__(self, *args, **kwargs) -> None:
        self._data = dict(*args, **kwargs)
        self._data_repr = repr(self._data)
        self._hash = hash(self._data_repr)

    def __repr__(self) -> str:  # pragma: no cover
        _repr = getattr(self, "_data_repr", None)
        if _repr is None:
            return f"{self.__class__.__name__}({self._data})"
        else:
            return f"{self.__class__.__name__}({self._data_repr})"

    def __hash__(self) -> int:  # pragma: no cover
        return self._hash

    def __getitem__(self, key: str) -> Any:
        value = self._data[key]
        if isinstance(value, MutableMapping):
            # Ensure DataMap is read-only at all levels of nesting.
            return DataMap(value.items())
        return value

    def __iter__(self):  # pragma: no cover
        return self._data.__iter__()

    def __len__(self):  # pragma: no cover
        return self._data.__len__()


class LocaleMap(TypedDict):
    """Represents the structure of localization data for individual locales.

    TODO:
        Mark this as readonly once [PEP 705](https://peps.python.org/pep-0705/)
        is implemented.
        We currently have to cast a `DataMap` to `LocaleMap` whenever we construct this
        dict since we can't mark a `TypedDict` as read-only yet.
    """

    currency_symbols: MutableMapping[str, str]
    decimal_separator: str
    grouping_separator: str
    local_currency_code: str
    negative_grouping: tuple[int, ...]
    negative_sign: str
    negative_sign_position: int
    negative_symbol_before: bool
    negative_symbol_space: int
    positive_grouping: tuple[int, ...]
    positive_sign: str
    positive_sign_position: int
    positive_symbol_before: bool
    positive_symbol_space: int


@dataclass(eq=False, frozen=True)
class LocaleData(EqualityByHashMixin):
    """A [Datasource](/linearmoney/glossary.html#datasource) that provides formatting
    data for currency localization."""

    language: str
    region: str
    nformat: FormatType
    data: LocaleMap

    @property
    def id(self) -> tuple[str, str, FormatType]:
        """Identifies the locale, but not necessarily the unique data of the locale.

        Represents the positional arguments used to create this instance.
        See [Datasources](/linearmoney/glossary.html#datasource) in the glossary
        for more details.
        """

        return (self.language, self.region, self.nformat)

    @property
    def tag(self) -> str:
        """The [`Locale Tag`](/linearmoney/glossary.html#locale-tag) for this locale."""

        return "_".join([self.language, self.region])

    def __hash__(self) -> int:
        return hash((self.id, self.data))


_REQUIRED_LOCALE_KEYS = {
    "currency_symbols",
    "decimal_separator",
    "grouping_separator",
    "local_currency_code",
    "negative_grouping",
    "negative_sign",
    "negative_sign_position",
    "negative_symbol_before",
    "negative_symbol_space",
    "positive_grouping",
    "positive_sign",
    "positive_sign_position",
    "positive_symbol_before",
    "positive_symbol_space",
}


@cache.cached()
def _merge_locale_overrides(locales: LocaleMap, **overrides) -> LocaleMap:
    """Merge any values given by keyword arguments into the resulting locale data,
    overriding the values for the corresponding keys in `locales`."""

    new_locales = copy.deepcopy(locales)

    for i in overrides:
        if i in _REQUIRED_LOCALE_KEYS:
            if i == "currency_symbols":
                # Ensure currency codes used as keys are all upper case.
                symbols = {
                    k.upper(): v for k, v in overrides["currency_symbols"].items()
                }
                for k, v in symbols.items():
                    new_locales["currency_symbols"][k] = v
            else:
                new_locales[i] = overrides[i]  # type: ignore[literal-required]
    return new_locales


_fallback_locales = resources.get_package_resource("locales")


@cache.cached(size_multiplier=2)
def locale(
    language: str,
    region: str,
    nformat: FormatType = FormatType.STANDARD,
    **overrides,
) -> LocaleData:
    r"""Create a new `LocaleData` datasource for locale given by `language`, and
    `region`.

    Args:
        language:
            The language portion of the [locale tag](/linearmoney/glossary.html#locale-tag)
        region:
            The region (territory) portion of the
            [locale tag](/linearmoney/glossary.html#locale-tag)
        nformat:
            The number format to use. Should be a member of the `FormatType` enum.
            The difference in format is generally only in negative numbers. E.g. -10 in
            'standard' vs. (10) in 'accounting'.
            If you aren't sure which format you need, you probably want 'FormatType.STANDARD`.
        **overrides:
            Formatting options to override the default formatting rules for the
            requested locale.
            The name of each kwarg is interpreted as a key in the `LocaleMap`
            returned as the `LocaleData.data` field, and its
            value will replace the value of that key in the output `DataMap`.
            E.g. `locale("en", "US", grouping_separator=';')` will return a `LocaleData`
            with formatting data for the 'en_US' locale, but using a semi-colon
            for grouping, so localizing '$1,000.00' using this data would result in
            '$1;000.00'.

            Values of a mapping type only override the keys provided, not the entire
            mapping. For example, if the formatting data for the requested locale
            contains `currency_symbols: {"EUR": "€", "USD": "$"}` by default, then
            providing `currency_symbols={"USD": "MySymbol"}` in the `locale` call will
            result in a `currency_symbols` value of `{"EUR": "€", "USD": "MySymbol"}`,
            not `{"USD": "MySymbol"}`.
    Returns:
        The newly parsed `LocaleData`.
    Raises:
        `linearmoney.exceptions.UnknownDataError`:
            If the cldr-json data that linearmoney utilizes does not have formatting
            data for the [locale tag](/linearmoney/glossary.html#locale-tag) built from the
            `language` and `region` arguments.
        ValueError:
            If the `nformat` is not one of the supported string constants.
            This should also be caught by static type checkers since the argument is
            typed with a Literal type.
    """

    if not language.islower():
        language = language.lower()

    if not region.isupper():
        region = region.upper()

    locales: LocaleMap

    format_key = str(nformat)

    if format_key in _fallback_locales:
        locale_string = "_".join([language, region])
        try:
            locales = _fallback_locales[format_key][locale_string]
        except KeyError as e:
            raise UnknownDataError(
                f"invalid value for `language` {language} or `region` {region}. \
Locale data not available under number format {nformat}"
            ) from e

    else:
        raise ValueError(
            f"invalid value for `nformat`. Expected either 'FormatType.Standard' or \
'FormatType.Accounting' got {nformat}"
        )

    if overrides:
        # We cast to satisfy mypy since we can't use read-only TypedDict yet.
        # Remove this cast once pep 705 is implemented.
        return LocaleData(
            language,
            region,
            nformat,
            data=cast(
                LocaleMap, DataMap(_merge_locale_overrides(locales, **overrides))
            ),
        )
    else:
        # We cast to satisfy mypy since we can't use read-only TypedDict yet.
        # Remove this cast once pep 705 is implemented.
        return LocaleData(
            language, region, nformat, data=cast(LocaleMap, DataMap(locales))
        )


# Set up system locale.
if None in posix_locale.getlocale(posix_locale.LC_MONETARY):
    # Set the locale of the python session to the running system locale.
    posix_locale.setlocale(posix_locale.LC_ALL, "")


def system_locale() -> LocaleData:
    """The `LocaleData` of the current POSIX locale of the running
    Python process.

    This is useful for local applications such as commandline scripts
    and desktop apps since those applications usually don't need to support
    multiple locales, but the developer doesn't always know the locale of the
    end user's environment.

    Prior to version 0.1.2, there was a bug in this function that would cause
    a crash when the system locale was set to the default C/POSIX locale.
    Version 0.1.2 and later fix this by interpreting the default C/POSIX locale
    as `en_US`. See
    [#14](https://github.com/GrammAcc/linearmoney/issues/14).
    """

    system_locale_string: str | None = posix_locale.getlocale()[0]
    assert (
        system_locale_string is not None
    ), "We init the system locale above, so it should not be None."
    if system_locale_string.upper() == "C" or system_locale_string.upper() == "POSIX":
        system_locale_string = "en_US"
    language, region = system_locale_string.split("_")

    return locale(language, region)


class CurrencyMap(TypedDict):
    """Represents the structure of denominational/rounding data for currencies.

    TODO:
        Mark this as readonly once [PEP 705](https://peps.python.org/pep-0705/)
        is implemented.
        We currently have to cast a `DataMap` to `CurrencyMap` whenever we construct this
        dict since we can't mark a `TypedDict` as read-only yet.
    """

    places: int
    cash_places: int
    denomination: int
    cash_denomination: int


@dataclass(eq=False, frozen=True)
class CurrencyData(EqualityByHashMixin):
    """A [Datasource](/linearmoney/glossary.html#datasource) that provides denominational
    data for currency rounding."""

    iso_code: str
    data: CurrencyMap

    @property
    def id(self) -> tuple[str]:
        """Identifies the currency, but not necessarily the unique data of the currency.

        Represents the positional arguments used to create this instance.
        See [Datasources](/linearmoney/glossary.html#datasource) in the glossary
        for more details.
        """

        return (self.iso_code,)

    def __hash__(self) -> int:
        return hash((self.id, self.data))


_REQUIRED_CURRENCY_KEYS = {
    "places",
    "cash_places",
    "denomination",
    "cash_denomination",
}


@cache.cached()
def _merge_currency_overrides(currencies: CurrencyMap, **overrides) -> CurrencyMap:
    """Merge any values given by keyword arguments into the resulting currencies data
    overriding the values for the corresponding keys in `currencies`."""

    new_currencies = copy.deepcopy(currencies)

    for i in _REQUIRED_CURRENCY_KEYS:
        if i in overrides:
            new_currencies[i] = overrides[i]  # type: ignore[literal-required]

    return new_currencies


_fallback_currencies = resources.get_package_resource("currencies")
_supported_iso_codes = set(resources.get_package_resource("supported_iso_codes"))


@cache.cached()
def currency(iso_code: str, **overrides) -> CurrencyData:
    r"""Create a new `CurrencyData` datasource based on `iso_code` and `**overrides`

    Args:
        iso_code:
            The ISO 4217 alpha code of the currency to parse denominational data for.
        **overrides:
            Denominational options to override the default rounding rules for the
            requested currency.
            The name of each kwarg is interpreted as a key in the `CurrencyMap`
            returned as the `CurrencyData.data` field, and
            its value will replace the value of that key in the output `DataMap`.
            E.g. `currency("USD", denomination=5)` will return a `CurrencyData`
            with denominational data for the 'USD' currency, but rounding to the
            nearest $0.05, so rounding $10.068 using this data would result in
            $10.05, not $10.07.
    Returns:
        The newly parsed `CurrencyData`.
    Raises:
        `linearmoney.exceptions.UnknownDataError`:
            If the cldr-json data does not have denominational data for `iso_code`
            and not all of the fields of `CurrencyMap` are provided as **overrides.
    """

    if not iso_code.isupper():
        iso_code = iso_code.upper()

    if iso_code not in _supported_iso_codes:
        if (
            "denomination" not in overrides
            or "places" not in overrides
            or "cash_denomination" not in overrides
            or "cash_places" not in overrides
        ):
            raise UnknownDataError(
                f"Rounding data for currency {iso_code} not found.\
You must provide all rounding data for unknown currency."
            )

    currencies: CurrencyMap
    if iso_code in _fallback_currencies:
        currencies = _fallback_currencies[iso_code]
    else:
        currencies = _fallback_currencies["DEFAULT"]

    if overrides:
        # We cast to satisfy mypy since we can't use read-only TypedDict yet.
        # Remove this cast once pep 705 is implemented.
        return CurrencyData(
            iso_code,
            data=cast(
                CurrencyMap, DataMap(_merge_currency_overrides(currencies, **overrides))
            ),
        )
    else:
        # We cast to satisfy mypy since we can't use read-only TypedDict yet.
        # Remove this cast once pep 705 is implemented.
        return CurrencyData(iso_code, data=cast(CurrencyMap, DataMap(currencies)))
