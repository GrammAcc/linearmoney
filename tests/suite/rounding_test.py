import decimal

import pytest
from pytest_parametrize_cases import parametrize_cases, Case

import linearmoney as lm


@parametrize_cases(
    Case("usd", value="10.123456", currency_code="usd", expected="10.12"),
    Case("jpy", value="1000.123456", currency_code="jpy", expected="1000"),
    Case("cad", value="10.123456", currency_code="cad", expected="10.12"),
)
def test_roundas_basic_usage(
    value, currency_code, expected, fixt_space, fixt_forex_usd
):
    """The `roundas` function uses the `denomination` and `places` of the
    specified currency's data to determine how the value will be rounded."""

    sut = lm.vector.asset(value, currency_code, fixt_space)
    val = lm.vector.evaluate(sut, currency_code, fixt_forex_usd)
    curr = lm.data.currency(currency_code)
    assert str(lm.scalar.roundas(val, curr)) == expected


def test_roundas_cash(fixt_space, fixt_forex_usd):
    """If the `cash` keyword argument is True, the value should be rounded
    based on the currency's `cash_denomination` and `cash_places`
    data as opposed to the normal `denomination` and `places` data."""

    sut = lm.vector.asset("10.183456", "cad", fixt_space)
    val = lm.vector.evaluate(sut, "cad", fixt_forex_usd)
    curr = lm.data.currency("cad")
    assert str(lm.scalar.roundas(val, curr)) == "10.18"
    assert str(lm.scalar.roundas(val, curr, cash=True)) == "10.20"


def test_roundas_whole_dollars(fixt_space, fixt_forex_usd):
    """When rounding an integer value, the result should still have the correct number
    of decimal places based on the currency."""

    sut = lm.vector.asset(10, "USD", fixt_space)
    val = lm.vector.evaluate(sut, "USD", fixt_forex_usd)
    curr = lm.data.currency("USD", denomination=10, places=5)
    assert str(lm.scalar.roundas(val, curr)) == "10.00000"


def test_roundas_negative_places(fixt_space, fixt_forex_usd):
    """When rounding to a currency with a negative value for `places`, we round as if
    `places` were 0."""

    for decimal_places in range(1, 10):
        sut = lm.vector.asset("10.000000", "USD", fixt_space)
        val = lm.vector.evaluate(sut, "USD", fixt_forex_usd)
        curr = lm.data.currency("USD", denomination=10, places=-decimal_places)
        assert str(lm.scalar.roundas(val, curr)) == "10"


@pytest.fixture(scope="class", params=["usd", "cad", "jpy"])
def fixt_currency_codes(request):
    """Parametrized fixture providing currency codes with different
    currency data.

    At least one of these codes will have a denomination of 0 and places
    of 2, at least one will have a places of 0, and at least one will have
    a cash denomination of > 1, so that they provide a spread of different
    formats for tests that should return the same results regardless.
    """

    return request.param


@parametrize_cases(
    Case("zero_places", places=0, expected="1111"),
    Case("one_place", places=1, expected="1111.1"),
    Case("two_places", places=2, expected="1111.12"),
    Case("three_places", places=3, expected="1111.123"),
    Case("four_places", places=4, expected="1111.1235"),
    Case("five_places", places=5, expected="1111.12346"),
    Case("six_places", places=6, expected="1111.123456"),
    Case("seven_places", places=7, expected="1111.1234560"),
)
def test_roundto(fixt_currency_codes, places, expected, fixt_space, fixt_forex_usd):
    """The `roundto` function should round the value to the specified number of
    places as if the denomination was 0 or 1, and the currency data is
    ignored."""

    sut = lm.vector.asset("1111.123456", fixt_currency_codes, fixt_space)
    val = lm.vector.evaluate(sut, fixt_currency_codes, fixt_forex_usd)
    assert str(lm.scalar.roundto(val, places)) == expected


def test_roundto_negative_places(fixt_space, fixt_forex_usd):
    """If `places` is negative, it should be treated as if it were
    0."""

    sut = lm.vector.asset("10.6", "usd", fixt_space)
    val = lm.vector.evaluate(sut, "usd", fixt_forex_usd)
    for places in range(9):
        assert str(lm.scalar.roundto(val, -(places + 1))) == "11"


def test_integer_value_roundto(fixt_space, fixt_forex_usd):
    """Ensure rounding an integer value to a specific number of places
    results in the correct number of zeros after the decimal point."""

    sut = lm.vector.asset("10", "usd", fixt_space)
    val = lm.vector.evaluate(sut, "usd", fixt_forex_usd)
    assert str(lm.scalar.roundto(val, 4)) == "10.0000"


@parametrize_cases(
    Case(
        "10.4_places_1_denomination_15",
        value="10.4",
        places=1,
        denomination=15,
        expected="10.45",
    ),
    Case(
        "10.35_places_1_denomination_15",
        value="10.35",
        places=1,
        denomination=15,
        expected="10.30",
    ),
    Case(
        "10.5_places_2_denomination_150",
        value="10.5",
        places=2,
        denomination=150,
        expected="10.450",
    ),
    Case(
        "10.55_places_2_denomination_150",
        value="10.55",
        places=2,
        denomination=150,
        expected="10.600",
    ),
)
def test_denomination_digits_more_than_places(
    value, places, denomination, expected, fixt_space, fixt_forex_usd
):
    """Check an edge case where the `denomination` has more digits than the
    `places` we are rounding to.

    This should round to the number of digits in `denomination`.
    """

    usd_override = lm.data.currency("usd", denomination=denomination, places=places)
    sut = lm.vector.asset(value, "usd", fixt_space)
    val = lm.vector.evaluate(sut, "usd", fixt_forex_usd)
    assert str(lm.scalar.roundas(val, usd_override)) == expected


@parametrize_cases(
    Case(
        "denomination_digits_equal_places",
        value="10.10",
        fractions={"denomination": 20, "places": 2},
        expected="10.00",
    ),
    Case(
        "zero_places",
        value="10.00",
        fractions={"denomination": 20, "places": 0},
        expected="0",
    ),
)
def test_midpoint_rounding(value, fractions, expected, fixt_space, fixt_forex_usd):
    """Ensure that rounding from the midpoint gives the correct results
    based on the ROUND_HALF_EVEN rounding mode set for the test suite."""

    usd_override = lm.data.currency("usd", **fractions)
    sut = lm.vector.asset(value, "usd", fixt_space)
    val = lm.vector.evaluate(sut, "usd", fixt_forex_usd)
    assert str(lm.scalar.roundas(val, usd_override)) == expected


@parametrize_cases(
    Case(
        "denomination_2_places_2_round_down",
        value="10.03",
        fractions={"denomination": 2, "places": 2},
        expected="10.04",
    ),
    Case(
        "denomination_2_places_2_round_up",
        value="10.03",
        fractions={"denomination": 2, "places": 2},
        expected="10.04",
    ),
    Case(
        "denomination_20_places_3_round_down",
        value="10.030",
        fractions={"denomination": 20, "places": 3},
        expected="10.040",
    ),
    Case(
        "denomination_20_places_3_round_up",
        value="10.030",
        fractions={"denomination": 20, "places": 3},
        expected="10.040",
    ),
)
def test_denomination_digits_less_than_to_places_with_leading_zeros(
    value, fractions, expected, fixt_space, fixt_forex_usd
):
    """This is a regression test added for a bug that was causing the
    leading zeros in the fractional portion of a rounded value to be
    dropped when the denomination digits were less than the number of
    places, and the fractional portion of the value before rounding had
    a leading zero. E.g. 10.03 with denomination=2 and places=2 would
    round up to 10.40 instead of 10.04, and 10.030 with denomination=20,
    and places=3 would round up to 10.400 instead of 10.040."""

    usd_override = lm.data.currency("usd", **fractions)
    sut = lm.vector.asset(value, "usd", fixt_space)
    val = lm.vector.evaluate(sut, "usd", fixt_forex_usd)
    assert str(lm.scalar.roundas(val, usd_override)) == expected


@parametrize_cases(
    Case(
        "places_2_denomination_0",
        fractions={"denomination": 0, "places": 2},
        expected="100.00",
    ),
    Case(
        "places_2_denomination_5",
        fractions={"denomination": 5, "places": 2},
        expected="100.00",
    ),
    Case(
        "places_2_denomination_15",
        fractions={"denomination": 15, "places": 2},
        expected="100.05",
    ),
    Case(
        "places__0_denomination_0",
        fractions={"denomination": 0, "places": 0},
        expected="100",
    ),
    Case(
        "places_0_denomination_5",
        fractions={"denomination": 5, "places": 0},
        expected="100",
    ),
    Case(
        "places_0_denomination_15",
        fractions={"denomination": 15, "places": 0},
        expected="105",
    ),
)
def test_carryover(fractions, expected, fixt_space, fixt_forex_usd):
    """Ensure the rounding algorithm properly carries over values from the
    fractional part of the value to the integral part when rounding up."""

    usd_override = lm.data.currency("usd", **fractions)
    sut = lm.vector.asset("99.9999999", "usd", fixt_space)
    val = lm.vector.evaluate(sut, "usd", fixt_forex_usd)
    assert str(lm.scalar.roundas(val, usd_override)) == expected


@parametrize_cases(
    Case(
        "usd",
        val=decimal.Decimal("10.55"),
        currency=lm.data.currency("usd"),
        expected=1055,
    ),
    Case(
        "jpy",
        val=decimal.Decimal("1000.4"),
        currency=lm.data.currency("jpy"),
        expected=1000,
    ),
    Case(
        "cad",
        val=decimal.Decimal("10.18"),
        currency=lm.data.currency("cad"),
        expected=1018,
    ),
)
def test_atomic(val, currency, expected):
    """The `atomic` function should return the decimal's value as an
    integer in the supplied currency's smallest denomination."""

    sut = lm.scalar.atomic(val, currency)
    assert sut == expected


@parametrize_cases(
    Case(
        "usd",
        val=decimal.Decimal("10.55"),
        currency=lm.data.currency("usd"),
        expected=1055,
    ),
    Case(
        "jpy",
        val=decimal.Decimal("1000.4"),
        currency=lm.data.currency("jpy"),
        expected=1000,
    ),
    Case(
        "cad",
        val=decimal.Decimal("10.18"),
        currency=lm.data.currency("cad"),
        expected=1020,
    ),
)
def test_atomic_cash(val, currency, expected):
    """Use the smallest ***cash*** denomination when `cash` is True."""

    sut = lm.scalar.atomic(val, currency, cash=True)
    assert sut == expected
