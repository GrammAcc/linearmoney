import pytest
from pytest_lazy_fixtures import lf
from pytest_parametrize_cases import Case, parametrize_cases

import linearmoney as lm


@pytest.fixture(scope="module")
def fixt_stored_usd():
    return "CAD;0:CNY;0:EUR;0:GBP;0:INR;0:JPY;0:USD;1E+1"


@pytest.fixture(scope="module")
def fixt_stored_jpy():
    return "CAD;0:CNY;0:EUR;0:GBP;0:INR;0:JPY;1E+3:USD;0"


@pytest.fixture(scope="module")
def fixt_stored_composite():
    return "CAD;0:CNY;0:EUR;0:GBP;0:INR;0:JPY;5E+2:USD;5"


@pytest.fixture(scope="module")
def fixt_stored_eur():
    return "CAD;0:CNY;0:EUR;4:GBP;0:INR;0:JPY;0:USD;0"


@pytest.fixture(scope="module")
def fixt_stored_forex():
    return "CAD;0.8:CNY;0.008:EUR;2.5:GBP;1.25:INR;0.0125:JPY;0.01:USD;1"


@pytest.fixture(scope="module")
def fixt_stored_basis_vector_usd():
    return "CAD;0:CNY;0:EUR;0:GBP;0:INR;0:JPY;0:USD;1"


@parametrize_cases(
    Case(
        "rudimentary_asset_usd",
        vec=lf("fixt_asset_usd"),
        expected=lf("fixt_stored_usd"),
    ),
    Case(
        "rudimentary_asset_jpy",
        vec=lf("fixt_asset_jpy"),
        expected=lf("fixt_stored_jpy"),
    ),
    Case(
        "composite_asset_usd_and_jpy",
        vec=lf("fixt_asset_composite"),
        expected=lf("fixt_stored_composite"),
    ),
    Case(
        "forex_vector",
        vec=lf("fixt_forex_usd"),
        expected=lf("fixt_stored_forex"),
    ),
    Case(
        "basis_vector",
        vec=lf("fixt_basis_usd"),
        expected=lf("fixt_stored_basis_vector_usd"),
    ),
)
def test_store(vec, expected):
    """Basic string serialization."""

    assert lm.vector.store(vec) == expected


@parametrize_cases(
    Case(
        "rudimentary_usd_to_jpy",
        currency_code="jpy",
        expected=lf("fixt_stored_jpy"),
    ),
    Case(
        "rudimentary_jpy_to_usd",
        currency_code="usd",
        expected=lf("fixt_stored_usd"),
    ),
    Case(
        "usd_and_jpy_composite_to_usd",
        currency_code="usd",
        expected=lf("fixt_stored_usd"),
    ),
    Case(
        "usd_and_jpy_composite_to_eur",
        currency_code="eur",
        expected=lf("fixt_stored_eur"),
    ),
)
def test_store_converted(currency_code, expected, fixt_assets, fixt_forex_usd):
    """Ensure that serializing a converted asset generates the
    correct output."""

    assert (
        lm.vector.store(lm.vector.convert(fixt_assets, currency_code, fixt_forex_usd))
        == expected
    )


def test_restore(fixt_assets):
    """Basic reconstruction from serialized strings."""

    serial_str = lm.vector.store(fixt_assets)
    assert lm.vector.restore(serial_str) == fixt_assets


def test_restore_converted(fixt_assets, fixt_forex_usd, fixt_iso_codes):
    """Ensure reconstruction from a serialized string after conversion gives the
    correct rudimentary asset."""

    converted = lm.vector.convert(fixt_assets, fixt_iso_codes, fixt_forex_usd)
    serial_str = lm.vector.store(converted)
    assert lm.vector.restore(serial_str) == converted


def test_restore_value_error():
    """Ensure the `restore` function raises value error when passed malformed input."""

    with pytest.raises(ValueError):
        lm.vector.restore("CAD;0:CNY;1:0.1")
