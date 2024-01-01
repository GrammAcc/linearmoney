import decimal

import pytest
from pytest_parametrize_cases import parametrize_cases, Case
from pytest_lazy_fixtures import lf

import linearmoney as lm
from linearmoney.exceptions import SpaceError

from tests.conftest import helpers

evaluations = [
    Case("to_cad", to_currency="cad", expected=12.5),
    Case("to_cny", to_currency="cny", expected=1250),
    Case("to_eur", to_currency="eur", expected=4),
    Case("to_gbp", to_currency="gbp", expected=8),
    Case("to_jpy", to_currency="jpy", expected=1000),
    Case("to_inr", to_currency="inr", expected=800),
    Case("to_usd", to_currency="usd", expected=10),
]


# Evaluation #
@parametrize_cases(*evaluations)
def test_evaluate(fixt_assets, to_currency, expected, fixt_forex_usd):
    """Ensure that evaluating asset vectors works as expected."""

    assert lm.vector.evaluate(fixt_assets, to_currency, fixt_forex_usd) == expected


def test_regression_evaluate_normalized(fixt_assets, fixt_forex_usd):
    """Ensure that the decimal returned by the `evaluate` function is
    normalized to a standard form to avoid string parsing issues in
    internal functions."""

    assert str(lm.vector.evaluate(fixt_assets, "usd", fixt_forex_usd)) == "1E+1"


@parametrize_cases(*evaluations)
def test_convert_to_result_is_rudimentary(
    fixt_assets, to_currency, expected, fixt_forex_usd
):
    """The result of a conversion should always be rudimentary
    regardless of whether the vector was a rudimentary or composite
    asset before conversion."""

    sut = lm.vector.convert(fixt_assets, to_currency, fixt_forex_usd)
    count = 0
    for val in sut:
        if val != 0:
            count += 1
    assert count == 1


@parametrize_cases(
    Case(
        "asset_and_asset",
        vec1=lf("fixt_asset_usd"),
        vec2=lf("fixt_asset_composite"),
        expected=50,
    ),
    Case(
        "asset_and_forex",
        vec1=lf("fixt_asset_usd"),
        vec2=lf("fixt_forex_usd"),
        expected=10,
    ),
)
def test_dot(vec1, vec2, expected):
    """Ensure the dot product function gives correct results."""

    assert lm.vector.dot(vec1, vec2) == expected


def test_dot_product_space_error():
    """The dot product function should raise an appropriate error if the two
    vectors are not part of the same currency space."""

    f1 = lm.vector.forex({"base": "usd", "rates": {"jpy": 100}})
    f2 = lm.vector.forex({"base": "usd", "rates": {"eur": 100}})
    vec1 = lm.vector.asset(10, "usd", lm.vector.space(f1))
    vec2 = lm.vector.asset(10, "usd", lm.vector.space(f2))
    with pytest.raises(SpaceError):
        lm.vector.dot(vec1, vec2)


@parametrize_cases(
    Case("CAD", axis="CAD", expected=helpers.decimal_tuple(1, 0, 0, 0, 0, 0, 0)),
    Case("CNY", axis="CNY", expected=helpers.decimal_tuple(0, 1, 0, 0, 0, 0, 0)),
    Case("EUR", axis="EUR", expected=helpers.decimal_tuple(0, 0, 1, 0, 0, 0, 0)),
    Case("GBP", axis="GBP", expected=helpers.decimal_tuple(0, 0, 0, 1, 0, 0, 0)),
    Case("INR", axis="INR", expected=helpers.decimal_tuple(0, 0, 0, 0, 1, 0, 0)),
    Case("JPY", axis="JPY", expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 1, 0)),
    Case("USD", axis="USD", expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 0, 1)),
)
def test_basis_vector(axis, expected, fixt_space):
    """The `basis_vector` function should return a `MoneyVector` representing the
    basis vector of the provided axis in the provided currency space."""

    assert helpers.vector_to_tuple(lm.vector.basis_vector(fixt_space, axis)) == expected


def test_basis_vector_space_error(fixt_space):
    """The `basis_vector` function should raise a `SpaceError` if the provided axis is
    not part of the provided currency space."""

    with pytest.raises(SpaceError):
        lm.vector.basis_vector(fixt_space, "SOME_INVALID_ISO_CODE")


def test_gamma():
    """Ensure the gamma function gives correct results."""

    # (2.5, 0.01, 1.0)
    forex_usd = lm.vector.forex({"base": "usd", "rates": {"jpy": 100, "eur": 0.4}})

    # Default decimal places for gamma function is 17.
    quantizer = decimal.Decimal("1.0") ** 17

    assert helpers.vector_to_tuple(lm.vector.gamma(forex_usd, "usd")) == (
        decimal.Decimal("2.5").quantize(quantizer),
        decimal.Decimal("0.01").quantize(quantizer),
        decimal.Decimal("1.0").quantize(quantizer),
    )
    assert helpers.vector_to_tuple(lm.vector.gamma(forex_usd, "jpy")) == (
        decimal.Decimal("250").quantize(quantizer),
        decimal.Decimal("1.0").quantize(quantizer),
        decimal.Decimal("100").quantize(quantizer),
    )
    assert helpers.vector_to_tuple(lm.vector.gamma(forex_usd, "eur")) == (
        decimal.Decimal("1.0").quantize(quantizer),
        decimal.Decimal("0.004").quantize(quantizer),
        decimal.Decimal("0.4").quantize(quantizer),
    )


def test_gamma_space_error():
    """The gamma function should raise an apppropriate error when the
    `iso_code` provided is not part of the currency space of the
    `forex_vector`."""

    # (EUR, JPY, USD)
    forex_usd = lm.vector.forex({"base": "usd", "rates": {"jpy": 100, "eur": 0.4}})

    with pytest.raises(SpaceError):
        lm.vector.gamma(forex_usd, "CNY")


def test_gamma_decimal_places(fixt_forex_usd, fixt_iso_codes):
    """The gamma function should round the decimal components of the result
    vector to the provided `decimal_places`."""

    with decimal.localcontext() as ctx:
        ctx.prec = 54
        zero_gamma = lm.vector.gamma(fixt_forex_usd, fixt_iso_codes, 0)
        for i in zero_gamma:
            # Zero decimal places should result in an integer.
            assert "." not in str(i)
        for i in range(1, 48):
            new_gamma = lm.vector.gamma(fixt_forex_usd, fixt_iso_codes, i)
            for j in new_gamma:
                integral, fractional = tuple(str(j).split("."))
                # Number of decimal places should match for all components.
                assert len(fractional) == i
