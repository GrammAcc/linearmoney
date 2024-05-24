"""Functions and types for doing monetary calculations in linear algebra."""

from __future__ import annotations

__all__: list[str] = [
    "asset",
    "forex",
    "basis_vector",
    "space",
    "gamma",
    "dot",
    "evaluate",
    "convert",
    "store",
    "restore",
    "MoneyVector",
    "ForexVector",
    "CurrencySpace",
    "RatesDict",
]

import decimal
import copy
from typing import TYPE_CHECKING, TypeAlias, TypedDict, TypeVar
from collections.abc import Iterator

from linearmoney import cache, _utils
from linearmoney.mixins import ImmutableDeduplicationMixin, EqualityByHashMixin
from linearmoney.exceptions import SpaceError, IntegrityError

if TYPE_CHECKING:
    from typing import Self

DecimalVector: TypeAlias = tuple[decimal.Decimal, ...]

_ZERO = decimal.Decimal(0)
_ONE = decimal.Decimal(1)

# TypeVar needed for typechecking subclasses returned in place of base class.
V = TypeVar("V", bound="MoneyVector")


class CurrencySpace(ImmutableDeduplicationMixin, EqualityByHashMixin):
    """Represents the currency space of a `MoneyVector`."""

    __slots__ = ["_axes", "_currencies", "_hash"]

    def __init__(self, axes: tuple[str, ...]) -> None:
        """
        Args:
            axes:
                A tuple of ISO 4217 currency codes representing the euclidean axes of the
                vector space.
        """

        self._axes = axes
        self._currencies = set(axes)
        self._hash = hash((axes, repr(self._currencies)))

    def __repr__(self) -> str:
        return "".join(["CurrencySpace", str(self.axes)])

    @property
    def axes(self) -> tuple[str, ...]:
        """The tuple of ISO 4217 currency codes representing the axes of this
        currency space."""

        return self._axes

    @property
    def currencies(self) -> set[str]:
        """The axes of this currency space as a python `Set`.

        Useful for faster membership testing of currencies.

        Example:
            >>> import linearmoney as lm
            >>> fo = lm.vector.forex({"base": "EUR", "rates": {"USD": 0.4}})
            >>> sp = lm.vector.space(fo)
            >>> "USD" in sp.currencies  # Is USD part of the currency space?
            True
        """

        return self._currencies

    def __hash__(self) -> int:
        return self._hash


class MoneyVector(ImmutableDeduplicationMixin, EqualityByHashMixin):
    """Base class for all money vectors.

    `MoneyVector`s are iterables that behave like tuples of `decimal.Decimal`s.

    Implements the basic arithmetic operations for vector math.
    """

    __slots__ = ["_vector", "_v_repr", "_axes", "_hash"]

    def __init__(self, decimal_vector: DecimalVector, axes: tuple[str, ...]) -> None:
        """
        Args:
            decimal_vector:
                The actual componenents of the vector.
            axes:
                The ISO 4217 currency codes that correspond to the axes of the vector's
                currency space.
        Raises:
            `linearmoney.exceptions.SpaceError`:
                If `decimal_vector` and `axes` are not the same length.
        """

        if len(decimal_vector) != len(axes):
            raise SpaceError("Must have the same number of components as axes.")
        self._vector = decimal_vector
        self._v_repr = str(tuple([str(component) for component in decimal_vector]))
        self._axes = axes
        self._hash = hash((self._vector, self._axes))

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        # Preserve precision of Decimals
        return f"{self.__class__.__name__}{self._v_repr}"

    def __hash__(self) -> int:
        return self._hash

    def __getitem__(self, idx: int) -> decimal.Decimal:
        return self._vector[idx]

    def __iter__(self) -> Iterator:
        return self._vector.__iter__()

    def __len__(self) -> int:
        return len(self._vector)

    @cache.cached()
    def __add__(self, other: MoneyVector) -> Self:
        # Raises `SpaceError` if the two vectors are not part of the same currency
        # space.

        if not isinstance(other, MoneyVector):
            return NotImplemented

        if self.axes != other.axes:
            raise SpaceError("MoneyVectors must be in the same space.")

        new_vector = tuple([self[i] + other[i] for i in range(self.dim)])
        return self.__class__(new_vector, self.axes)

    @cache.cached()
    def __radd__(self, other: MoneyVector) -> Self:
        if other == 0:
            return self
        return self.__add__(other)

    @cache.cached()
    def __sub__(self, other: MoneyVector) -> Self:
        # Raises `SpaceError` if the two vectors are not part of the same currency
        # space.

        if not isinstance(other, MoneyVector):
            return NotImplemented

        if self.axes != other.axes:
            raise SpaceError("MoneyVectors must be in the same space.")

        new_vector = tuple([self[i] - other[i] for i in range(self.dim)])
        return self.__class__(new_vector, self.axes)

    @cache.cached()
    def __rsub__(self, other: V) -> V:
        if not isinstance(other, MoneyVector):
            return NotImplemented
        return other.__sub__(self)  # pragma: no cover

    @cache.cached()
    def __mul__(self, scalar: decimal.Decimal | int | float | str) -> Self:
        try:
            scalar = _utils.coerce_decimal(scalar)
        except NotImplementedError:
            return NotImplemented
        return self.__class__(tuple([scalar * i for i in self]), self.axes)

    @cache.cached()
    def __rmul__(self, scalar: decimal.Decimal | int | float | str) -> Self:
        return self.__mul__(scalar)

    @cache.cached()
    def __truediv__(self, scalar: decimal.Decimal | int | float | str) -> Self:
        try:
            scalar = _utils.coerce_decimal(scalar)
        except NotImplementedError:
            return NotImplemented
        return self * (decimal.Decimal(1) / scalar)

    @cache.cached()
    def __pos__(self) -> Self:
        return copy.deepcopy(self)

    @cache.cached()
    def __neg__(self) -> Self:
        return self.__class__(tuple([-i for i in self]), self.axes)

    @property
    @cache.cached()
    def dim(self) -> int:
        """The dimension of this `MoneyVector`."""

        return len(self)

    @property
    @cache.cached()
    def axes(self) -> tuple[str, ...]:
        """Tuple of the ISO 4217 alpha currency codes representing the axes of this
        `MoneyVector`."""

        return self._axes


class ForexVector(MoneyVector):
    """A [forex vector](/linearmoney/glossary.html#forex-vector) in the
    [linear money model](/linear_money_model.html)."""

    @cache.cached()
    def __neg__(self) -> Self:
        raise (IntegrityError("Forex vectors can not have negative-valued components."))


@cache.cached()
def basis_vector(currency_space: CurrencySpace, axis: str) -> MoneyVector:
    """Return the Euclidean basis vector corresponding to `axis` in `currency_space`.

    Raises:
        `linearmoney.exceptions.SpaceError`:
            If `axis` is not part of `currency_space`.
    """

    axis = axis.upper()

    if axis not in currency_space.currencies:
        raise SpaceError(
            f"Currency {axis} is not part of currency space {currency_space}"
        )
    _vector = tuple([_ONE if i == axis else _ZERO for i in currency_space.axes])
    return MoneyVector(_vector, currency_space.axes)


@cache.cached()
def dot(vec1: MoneyVector, vec2: MoneyVector) -> decimal.Decimal:
    """Calculate and return the dot product of vectors `vec1` and `vec2`.

    Raises:
        `linearmoney.exceptions.SpaceError`:
            If the two vectors are not part of the same currency space.
    """

    if vec1.axes != vec2.axes:
        raise SpaceError("MoneyVectors must be in the same space.")

    product = decimal.Decimal(
        str(sum([vec1[idx] * vec2[idx] for idx in range(vec1.dim)]))
    )
    return product


@cache.cached()
def space(vec: MoneyVector) -> CurrencySpace:
    """Create and return a new `CurrencySpace` representing the space that `vec`
    belongs to."""

    return CurrencySpace(vec.axes)


@cache.cached(size_multiplier=16)
def asset(
    amount: int | float | decimal.Decimal, iso_code: str, currency_space: CurrencySpace
) -> MoneyVector:
    """Create a new [*Asset Vector*](/linearmoney/glossary.html#asset-vector) in `currency_space`
    with `amount` of `iso_code` as it's only non-zero component.

    Raises:
        `linearmoney.exceptions.SpaceError`:
            If `iso_code` is not part of `currency_space`.
    """

    iso_code = iso_code.upper()

    if iso_code not in currency_space.currencies:
        raise SpaceError(f"{iso_code} is not part of {currency_space}")

    try:
        _amount = _utils.coerce_decimal(amount)
    except NotImplementedError:
        raise TypeError(f"Unsupported type for argument `amount`: {type(amount)}")

    _vector = tuple([_amount if i == iso_code else _ZERO for i in currency_space.axes])
    return MoneyVector(_vector, currency_space.axes)


_DecimalRates: TypeAlias = dict[str, decimal.Decimal]
_NumericRates: TypeAlias = dict[str, int | float | decimal.Decimal]


class RatesDict(TypedDict):
    """A dictionary representing forex rates ***from*** `base` ***to*** each of the
    keys in `rates`.

    The key names of this dict are chosen to match the most common structure returned
    by public HTTP APIs for forex data since that is how most applications
    will source their forex rates, so this allows passing the results of e.g.
    `json.load(api_response)` directly to any function that accepts this type.
    """

    base: str
    rates: _NumericRates


@cache.cached()
def _coerce_decimal_rates(numeric_rates: _NumericRates) -> _DecimalRates:
    """Coerce the values of `numeric_rates` to `decimal.Decimal` and force all keys
    to uppercase."""

    return {k.upper(): _utils.coerce_decimal(v) for k, v in numeric_rates.items()}


@cache.cached()
def _merge_rates(base_rates: _DecimalRates, overrides: _DecimalRates) -> _DecimalRates:
    """Override values in `base_rates` with corresponding values in `overrides`.
    Any keys in `overrides` not present in `base_rates` will be merged into `base_rates
    as well."""

    r = {k: v for k, v in base_rates.items()}
    r.update(overrides)
    return r


@cache.cached()
def _invert_rates(rates: _DecimalRates) -> _DecimalRates:
    """Invert the forex rates given by `rates`.

    Input forex rates are assumed to represent the rates from
    Quote Currency -> All Currencies. This function inverts them to represent the
    rates from All Currencies -> Quote Currency.

    E.g. (EUR -> EUR, EUR -> JPY, EUR -> USD) becomes
    (EUR -> EUR, JPY -> EUR, USD -> EUR).
    """

    return {k: (_ONE / v) for k, v in rates.items()}


@cache.cached()
def forex(
    forex_rates: RatesDict, **overrides: int | float | decimal.Decimal
) -> ForexVector:
    r"""Construct a new `ForexVector` suitable for use in the `gamma` function.

    Args:
        forex_rates:
            A mapping where each of the values in `forex_rates["rates"]` specifies
            the rate ***from*** `forex_rates["base"]` ***to*** the value's
            corresponding key.
            `forex_rates["base"]` and all keys in `forex_rates["rates"]` are treated as
            case-insensitive, and all numeric rate values are forced to
            `decimal.Decimal`, so `{"base": "eur", "rates": {"usd": 0.1}}` and
            `{"base": "EUR", "rates": {"USD": decimal.Decimal("0.1")}}` are treated as
            equivalent.
            If the `rates` key of `forex_rates` is an empty dictionary, then
            we create a forex vector with only one rate, which is `base -> base = 1`.
            This makes it clear that a forex vector is intended to force
            [single-currency](/user_guide/recipes.html#single-currency-application) calculations.
        \*\*overrides:
            Additional kwargs interpreted as ISO 4217 currency codes that should be
            manually overriden with the value provided or added to the set of
            exchange rates if the code is not already present in
            `forex_rates["rates"]`.
            Any rates passed as kwargs are interpreted in
            the same way as if they had been included in the `forex_rates["rates"]`
            nested mapping, so they should represent the exchange rates ***from***
            `forex_rates["base"]` ***to*** the currency represented by the name of
            the kwarg. All kwargs are case-insensitive, so passing `usd=0.1` will
            result in the rate
            `forex_rates["base"] -> "USD" = decimal.Decimal("0.1")`.
    Returns:
        The newly created `ForexVector`.

        Its [`axes`](#MoneyVector.axes) tuple will be the set of all
        currencies provided via `forex_rates["rates"]` and `overrides` along with
        the `forex_rates["base"]`.
    Raises:
        `linearmoney.exceptions.IntegrityError`:
            If the `forex_rates["rates"]` dictionary contains any values that are less
            than or equal to 0.
    """

    _rates: _DecimalRates = _coerce_decimal_rates(forex_rates["rates"])
    _iso_code: str = forex_rates["base"].upper()

    if overrides:
        _rates = _merge_rates(_rates, _coerce_decimal_rates(overrides))

    for r in _rates.values():
        if r <= 0:
            raise IntegrityError("All components of a ForexVector must be > 0.")

    # We copy here to prevent mutating rates returned from the cache
    _rates = {k: v for k, v in _rates.items()}
    _rates[_iso_code] = decimal.Decimal("1.0")

    _rates = _invert_rates(_rates)
    _sorted_rates = dict(sorted(_rates.items()))
    return ForexVector(tuple(_sorted_rates.values()), tuple(_sorted_rates))


@cache.cached()
def _round_forex(vec: ForexVector, quantizer: decimal.Decimal) -> ForexVector:
    """Return a new `ForexVector` with all components of `vec` rounded based on
    `quantizer`."""

    return ForexVector(tuple([r.quantize(quantizer) for r in vec]), vec.axes)


@cache.cached()
def gamma(r: ForexVector, iso_code: str, decimal_places: int = 17) -> ForexVector:
    """Return a new `ForexVector` representing the rates ***from*** all different
    currencies in the currency space of `r` ***to*** `iso_code`.

    Args:
        r:
            The forex vector to calculate the gamma vector from.
            Corresponds to the `r` of the [linear money model's](/linear_money_model.html)
            gamma function.
        iso_code:
            The ISO 4217 currency code that the resulting gamma vector will represent
            the rates ***to***.
        decimal_places:
            The number of decimal places the rates in the resulting gamma vector will
            use.
            This should be large enough to support the precise exchange rates between
            the most valuable and least valuable currencies in the currency space.
            This is NOT the decimal *precision*. It specifies the exact number of
            digits *after* the decimal separator, not the total digits of the entire
            number.
    Raises:
        `linearmoney.exceptions.SpaceError`:
            If `iso_code` is not part of the currency space of `r`.
    """

    _quantizer = decimal.Decimal("1.0") ** decimal_places

    iso_code = iso_code.upper()

    _space = space(r)
    if iso_code not in _space.currencies:
        raise SpaceError(f"{iso_code} is not an axis in currency space {_space}.")

    ek = basis_vector(_space, iso_code)
    conversion_factor = _ONE / dot(r, ek)
    new_rates_vector = r * conversion_factor
    return _round_forex(new_rates_vector, _quantizer)


_EVALUATION_QUANTIZER = decimal.Decimal("10") ** decimal.Decimal("-12")


@cache.cached()
def evaluate(
    asset_vec: MoneyVector, iso_code: str, forex_vec: ForexVector
) -> decimal.Decimal:
    """[Evaluate](/linearmoney/glossary.html#evaluation) `asset_vec` to `iso_code` using rates
    defined by `forex_vec`."""

    result = dot(asset_vec, gamma(forex_vec, iso_code))
    # Eliminate intermediate rounding errors.
    rounded_result = result.quantize(_EVALUATION_QUANTIZER)
    # Normalize to improve consistency and improve testability.
    normalized_result = rounded_result.normalize()
    return normalized_result


@cache.cached()
def convert(
    asset_vec: MoneyVector, iso_code: str, forex_vec: ForexVector
) -> MoneyVector:
    """[Convert](/linearmoney/glossary.html#conversion) `asset_vec` to `iso_code` using the rates
    defined by `forex_vec`.

    Returns a [*Rudimentary Asset*](/linearmoney/glossary.html#rudimentary-asset).
    """

    return evaluate(asset_vec, iso_code, forex_vec) * basis_vector(
        space(asset_vec), iso_code
    )


@cache.cached()
def store(vec: MoneyVector) -> str:
    """Serialize `vec` to a string that can be used to recreate the exact same
    vector."""

    component_list = [
        ";".join([k, str(v.normalize())]) for k, v in zip(vec.axes, vec, strict=True)
    ]
    return ":".join(component_list)


@cache.cached()
def restore(serial_str: str) -> MoneyVector:
    """Recreate a `MoneyVector` from a serialized string.

    Args:
        serial_str:
            A serialized string representation of a `MoneyVector`.
            Should be the same format as returned by the `store` function.
    Returns:
        `MoneyVector`

        The reconstructed vector.
        Should be exactly the same as the vector that was `store`d.
    Raises:
        ValueError:
            If the `serial_str` has an invalid format.
    """

    components = serial_str.split(":")
    new_decimal_vector_list = []
    new_axes_list = []
    for i in components:
        component = i.split(";")
        if len(component) != 2:
            raise ValueError(f"Invalid serial string format: {serial_str}")
        new_decimal_vector_list.append(decimal.Decimal(component[1]))
        new_axes_list.append(component[0])
    new_decimal_vector = tuple(new_decimal_vector_list)
    new_axes = tuple(new_axes_list)
    return MoneyVector(new_decimal_vector, new_axes)
