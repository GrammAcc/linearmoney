import decimal

import pytest
from pytest_lazy_fixtures import lf
from pytest_parametrize_cases import Case, parametrize_cases

import linearmoney as lm
from linearmoney.exceptions import IntegrityError, SpaceError
from tests.conftest import helpers

_numeric_input_types = [
    2,
    2.0,
    decimal.Decimal("2"),
    "2.0",
]


def _input_type_names(param):
    return param.__class__.__name__


@pytest.fixture(scope="class", params=_numeric_input_types, ids=_input_type_names)
def fixt_numeric_input(request):
    return request.param


@pytest.fixture(scope="class")
def fixt_decimal_input():
    return decimal.Decimal("2")


@parametrize_cases(
    Case(
        "rudimentary_asset_plus_rudimentary_asset",
        lhs=lf("fixt_asset_usd"),
        rhs=lf("fixt_asset_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 0, 20),
    ),
    Case(
        "rudimentary_asset_plus_composite_asset",
        lhs=lf("fixt_asset_usd"),
        rhs=lf("fixt_asset_composite"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 500, 15),
    ),
    Case(
        "composite_asset_plus_rudimentary_asset",
        lhs=lf("fixt_asset_composite"),
        rhs=lf("fixt_asset_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 500, 15),
    ),
    Case(
        "rudimentary_asset_plus_forex",
        lhs=lf("fixt_asset_usd"),
        rhs=lf("fixt_forex_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0.8, 0.008, 2.5, 1.25, 0.0125, 0.01, 11),
    ),
    Case(
        "forex_plus_rudimentary_asset",
        lhs=lf("fixt_forex_usd"),
        rhs=lf("fixt_asset_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0.8, 0.008, 2.5, 1.25, 0.0125, 0.01, 11),
    ),
    Case(
        "composite_asset_plus_forex",
        lhs=lf("fixt_asset_composite"),
        rhs=lf("fixt_forex_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0.8, 0.008, 2.5, 1.25, 0.0125, 500.01, 6),
    ),
    Case(
        "forex_plus_composite_asset",
        lhs=lf("fixt_forex_usd"),
        rhs=lf("fixt_asset_composite"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0.8, 0.008, 2.5, 1.25, 0.0125, 500.01, 6),
    ),
    Case(
        "rudimentary_asset_plus_basis",
        lhs=lf("fixt_asset_usd"),
        rhs=lf("fixt_basis_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 0, 11),
    ),
    Case(
        "basis_plus_rudimentary_asset",
        lhs=lf("fixt_basis_usd"),
        rhs=lf("fixt_asset_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 0, 11),
    ),
    Case(
        "composite_asset_plus_basis",
        lhs=lf("fixt_asset_composite"),
        rhs=lf("fixt_basis_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 500, 6),
    ),
    Case(
        "basis_plus_composite_asset",
        lhs=lf("fixt_basis_usd"),
        rhs=lf("fixt_asset_composite"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 500, 6),
    ),
)
def test_add(lhs, rhs, expected):
    """Ensure that addition with vectors works as expected."""

    _sum = lhs + rhs
    assert helpers.vector_to_tuple(_sum) == expected


@parametrize_cases(
    Case(
        "rudimentary_asset_minus_rudimentary_asset",
        lhs=lf("fixt_asset_usd"),
        rhs=lf("fixt_asset_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 0, 0),
    ),
    Case(
        "rudimentary_asset_minus_rudimentary_asset_different_currencies",
        lhs=lf("fixt_asset_usd"),
        rhs=lf("fixt_asset_jpy"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, -1000, 10),
    ),
    Case(
        "rudimentary_asset_minus_composite_asset",
        lhs=lf("fixt_asset_usd"),
        rhs=lf("fixt_asset_composite"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, -500, 5),
    ),
    Case(
        "composite_asset_minus_rudimentary_asset",
        lhs=lf("fixt_asset_composite"),
        rhs=lf("fixt_asset_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 500, -5),
    ),
    Case(
        "rudimentary_asset_minus_forex",
        lhs=lf("fixt_asset_usd"),
        rhs=lf("fixt_forex_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(-0.8, -0.008, -2.5, -1.25, -0.0125, -0.01, 9),
    ),
    Case(
        "forex_minus_rudimentary_asset",
        lhs=lf("fixt_forex_usd"),
        rhs=lf("fixt_asset_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0.8, 0.008, 2.5, 1.25, 0.0125, 0.01, -9),
    ),
    Case(
        "composite_asset_minus_forex",
        lhs=lf("fixt_asset_composite"),
        rhs=lf("fixt_forex_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(-0.8, -0.008, -2.5, -1.25, -0.0125, 499.99, 4),
    ),
    Case(
        "forex_minus_composite_asset",
        lhs=lf("fixt_forex_usd"),
        rhs=lf("fixt_asset_composite"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0.8, 0.008, 2.5, 1.25, 0.0125, -499.99, -4),
    ),
    Case(
        "rudimentary_asset_minus_basis",
        lhs=lf("fixt_asset_usd"),
        rhs=lf("fixt_basis_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 0, 9),
    ),
    Case(
        "basis_minus_rudimentary_asset",
        lhs=lf("fixt_basis_usd"),
        rhs=lf("fixt_asset_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 0, -9),
    ),
    Case(
        "composite_asset_minus_basis",
        lhs=lf("fixt_asset_composite"),
        rhs=lf("fixt_basis_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 500, 4),
    ),
    Case(
        "basis_minus_composite_asset",
        lhs=lf("fixt_basis_usd"),
        rhs=lf("fixt_asset_composite"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, -500, -4),
    ),
)
def test_sub(lhs, rhs, expected):
    """Ensure that subtraction with vectors works as expected."""

    _diff = lhs - rhs
    assert helpers.vector_to_tuple(_diff) == expected


def test_add_sub_invalid_input(fixt_vectors, fixt_decimal_input):
    """Ensure that addition and subtraction with a scalar raises the correct error."""

    with pytest.raises(TypeError):
        fixt_vectors + fixt_decimal_input
    with pytest.raises(TypeError):
        fixt_decimal_input + fixt_vectors

    with pytest.raises(TypeError):
        fixt_vectors - fixt_decimal_input
    with pytest.raises(TypeError):
        fixt_decimal_input - fixt_vectors


def test_add_sub_different_spaces(fixt_vectors):
    """Ensure that addition/subtraction of two money vectors from different currency
    spaces raises the correct error."""

    new_forex = lm.vector.forex({"base": "USD", "rates": {"GIL": 100}})
    new_space = lm.vector.space(new_forex)
    new_asset = lm.vector.asset(10, "USD", new_space)
    new_basis = lm.vector.basis_vector(new_space, "USD")
    new_vectors = [new_forex, new_asset, new_basis]

    for new_vector in new_vectors:
        with pytest.raises(SpaceError):
            fixt_vectors + new_vector

        with pytest.raises(SpaceError):
            new_vector + fixt_vectors

        with pytest.raises(SpaceError):
            fixt_vectors - new_vector

        with pytest.raises(SpaceError):
            new_vector - fixt_vectors


@parametrize_cases(
    Case(
        "rudimentary_asset",
        vec=lf("fixt_asset_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 0, 20),
    ),
    Case(
        "composite_asset",
        vec=lf("fixt_asset_composite"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 1000, 10),
    ),
    Case(
        "forex",
        vec=lf("fixt_forex_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(1.6, 0.016, 5, 2.5, 0.025, 0.02, 2),
    ),
    Case(
        "basis",
        vec=lf("fixt_basis_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 0, 2),
    ),
)
def test_mul(fixt_numeric_input, vec, expected):
    """Ensure that multiplication with vectors works as expected."""

    _lh_prod = vec * fixt_numeric_input
    assert helpers.vector_to_tuple(_lh_prod) == expected

    _rh_prod = fixt_numeric_input * vec
    assert helpers.vector_to_tuple(_rh_prod) == expected


@parametrize_cases(
    Case(
        "rudimentary_asset",
        lhs=lf("fixt_asset_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 0, 5),
    ),
    Case(
        "composite_asset",
        lhs=lf("fixt_asset_composite"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 250, 2.5),
    ),
    Case(
        "forex",
        lhs=lf("fixt_forex_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0.4, 0.004, 1.25, 0.625, 0.00625, 0.005, 0.5),
    ),
    Case(
        "basis",
        lhs=lf("fixt_basis_usd"),
        # CAD, CNY, EUR, GBP, INR, JPY, USD
        expected=helpers.decimal_tuple(0, 0, 0, 0, 0, 0, 0.5),
    ),
)
def test_div(fixt_numeric_input, lhs, expected):
    """Ensure that division with vectors works as expected."""

    _quot = lhs / fixt_numeric_input
    assert helpers.vector_to_tuple(_quot) == expected


def test_mul_div_invalid_input(fixt_vectors):
    """Ensure that multiplication and division do not accept other vectors."""

    with pytest.raises(TypeError):
        fixt_vectors * fixt_vectors
    with pytest.raises(TypeError):
        fixt_vectors / fixt_vectors


def test_cannot_divide_scalar_by_vector(fixt_vectors, fixt_decimal_input):
    """Ensure that dividing a scalar by a vector raises the correct error."""

    with pytest.raises(TypeError):
        fixt_decimal_input / fixt_vectors


def test_vector_unary_positive_operator(fixt_vectors):
    """Ensure that the `__pos__` operator gives a correct result for all
    vectors."""

    assert +fixt_vectors == fixt_vectors


def test_asset_vector_unary_negative_operator(fixt_three_space):
    """Ensure that the `__neg__` operator gives a correct result for asset
    vectors."""

    usd = lm.vector.asset(10, "usd", fixt_three_space)
    jpy = lm.vector.asset(500, "jpy", fixt_three_space)
    eur = lm.vector.asset(-25, "eur", fixt_three_space)
    composite = usd + jpy + eur

    negative = -composite

    assert helpers.vector_to_tuple(negative) == helpers.decimal_tuple(25, -500, -10)


def test_basis_vector_unary_negative_operator(fixt_basis_usd):
    """Ensure that the `__neg__` operator gives a correct result for basis
    vectors."""

    negative = -fixt_basis_usd
    assert helpers.vector_to_tuple(negative) == helpers.decimal_tuple(
        0, 0, 0, 0, 0, 0, -1
    )


def test_forex_vector_unary_negative_operator(fixt_forex_usd):
    """Forex vectors cannot have negative-valued components, so the `__neg__`
    operator should raise an appropriate error for forex vectors."""

    with pytest.raises(IntegrityError):
        -fixt_forex_usd


def test_sum_assets(fixt_forex_usd, fixt_three_space):
    """Ensure vectors can be summed with the builtin `sum` function."""

    vectors = [lm.vector.asset(i, "usd", fixt_three_space) for i in range(4)]
    with helpers.does_not_raise(TypeError):
        sum(vectors)
    assert helpers.vector_to_tuple(sum(vectors)) == helpers.decimal_tuple(0, 0, 6)
