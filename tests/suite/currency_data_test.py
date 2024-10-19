import pytest

import linearmoney as lm
from linearmoney.exceptions import InvalidDataError, UnknownDataError
from tests.conftest import helpers


def test_basic_usage():
    """Check basic CurrencyData creation."""

    usd = lm.data.currency("usd")
    assert usd.data["places"] == 2


def test_data_is_read_only():
    """CurrencyData should be read-only."""

    override_dict = {
        "places": 2,
        "cash_places": 2,
        "denomination": 0,
        "cash_denomination": 5,
    }
    cu = lm.data.currency("usd", **override_dict)

    with pytest.raises(TypeError):
        cu.data["places"] = "some_value"


def test_data_has_correct_python_types(fixt_currency_usd):
    """Ensure currency data is of the correct type."""

    for i in fixt_currency_usd.data.values():
        assert isinstance(i, int)


def test_with_fractions_overrides():
    """Passing in **overrides keyword arguments should result in the created
    CurrencyData having the supplied values for the corresponding keys."""

    assert (
        lm.data.currency("usd").data["places"] == 2
    )  # Ensure default is different from the override below.

    usd_override = lm.data.currency("usd", places=5)
    assert usd_override.data["places"] == 5


def test_custom_currency():
    """The `currency` producer function should allow creating `CurrencyData`
    for an unknown `iso_code` as long as all of the data fields are provided as
    keyword arguments."""

    jpy = lm.data.currency("jpy")
    custom_curr = lm.data.currency("gil", **jpy.data)
    assert custom_curr.iso_code == "GIL"
    assert custom_curr.data == jpy.data


def test_custom_currency_unknown_data_error():
    """Passing in an `iso_code` for a currency that is not in the cldr data
    without providing all denominational data values as keyword arguments is an
    error."""

    with pytest.raises(UnknownDataError):
        lm.data.currency("GIL")
    with pytest.raises(UnknownDataError):
        lm.data.currency("GIL", denomination=0)
    with pytest.raises(UnknownDataError):
        lm.data.currency("GIL", denomination=0, places=2)
    with pytest.raises(UnknownDataError):
        lm.data.currency("GIL", denomination=0, places=2, cash_denomination=0)


def test_custom_currency_invalid_data_error():
    """Attempting to create a CurrencyData with a {cash_}denomination that uses more digits
    than its {cash_}places should raise an InvalidDataError."""

    with pytest.raises(InvalidDataError):
        lm.data.currency("USD", denomination=25, places=1)
    with pytest.raises(InvalidDataError):
        lm.data.currency("USD", cash_denomination=25, cash_places=1)
    with helpers.does_not_raise(InvalidDataError):
        lm.data.currency(
            "USD", cash_denomination=25, cash_places=2, denomination=1, places=1
        )

    with helpers.does_not_raise(InvalidDataError):
        lm.data.currency(
            "USD", denomination=25, places=2, cash_denomination=1, cash_places=1
        )
