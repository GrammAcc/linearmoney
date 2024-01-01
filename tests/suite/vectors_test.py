import decimal
import fractions

import pytest

import linearmoney as lm
from linearmoney.exceptions import SpaceError, IntegrityError

from tests.conftest import helpers


_vector_classes = [lm.vector.MoneyVector, lm.vector.ForexVector]


@pytest.fixture(
    scope="module", params=_vector_classes, ids=[i.__name__ for i in _vector_classes]
)
def fixt_vector_classes(request):
    return request.param


def test_components_and_axes_mismatch(fixt_vector_classes):
    """Ensure that all vector constructors raise the appropriate error when attempting
    to construct a vector using a decimal tuple and axes tuple that are of different
    lengths."""

    decimal_tuple = (decimal.Decimal(1), decimal.Decimal(1), decimal.Decimal(1))
    axes_tuple = ("JPY", "USD")
    with pytest.raises(SpaceError):
        # Different dimensions.
        fixt_vector_classes(decimal_tuple, axes_tuple)


class TestMoneyVectors:
    def test_space_error(self, fixt_space):
        """A SpaceError will be raised when attempting to create an `MoneyVector` with
        a currency that does not belong to the space provided."""

        with pytest.raises(SpaceError):
            lm.vector.asset(100, "GIL", fixt_space)

    _allowed_input_types = [
        10,
        10.0,
        decimal.Decimal("1E+1"),
    ]

    _invalid_input_types = [
        [],
        fractions.Fraction(2, 1),
        {},
        set(),
        tuple(),
        "invalid input string",
    ]

    def _asset_input_type_names(param):
        return param.__class__.__name__

    @pytest.fixture(
        scope="class", params=_allowed_input_types, ids=_asset_input_type_names
    )
    def fixt_allowed_asset_input_types(self, request):
        return request.param

    @pytest.fixture(
        scope="class", params=_invalid_input_types, ids=_asset_input_type_names
    )
    def fixt_invalid_asset_input_types(self, request):
        return request.param

    def test_input_types(
        self, fixt_allowed_asset_input_types, fixt_invalid_asset_input_types, fixt_space
    ):
        """Ensure that the `asset` function accepts a strict set of numeric types."""

        with helpers.does_not_raise(TypeError):
            lm.vector.asset(fixt_allowed_asset_input_types, "usd", fixt_space)
        with pytest.raises(TypeError):
            lm.vector.asset(fixt_invalid_asset_input_types, "usd", fixt_space)


class TestForexVectors:
    @pytest.fixture(scope="class")
    def fixt_rates_usd(self):
        """A simple dictionary providing rates of 1 USD -> 100 JPY for easy result
        verification."""

        return {"base": "USD", "rates": {"JPY": 100}}

    @pytest.fixture(scope="module")
    def fixt_rates_jpy(self):
        """A simple dictionary providing rates of 1 JPY -> 0.01 USD for easy result
        verification."""

        return {"base": "JPY", "rates": {"USD": 0.01}}

    @pytest.fixture(scope="module")
    def fixt_api_rates_usd(self):
        """A simple dictionary providing rates in the structure commonly provided by
        public web APIs.

        Additional keys are included in this dictionary to simulate the API providing
        extra information in the JSON response, which is very common.
        """

        _ = {
            "date": "21-07-2022",
            "base": "USD",
            "rates": {"JPY": 100},
            "encoding": "text/json",
        }
        return _

    @pytest.fixture(scope="module")
    def fixt_api_rates(self):
        """A dictionary providing rates in the structure commonly provided by
        public web APIs."""

        _ = {
            "date": "2021-06-01",
            "base": "EUR",
            "rates": {
                "USD": "1.2225",
                "JPY": "134.05",
                "BGN": "1.9558",
                "CZK": "25.462",
                "DKK": "7.4366",
                "GBP": "0.86285",
                "HUF": "346.46",
                "PLN": "4.4661",
                "RON": "4.9191",
                "SEK": "10.0955",
                "CHF": "1.0986",
                "ISK": "147.50",
                "NOK": "10.1113",
                "HRK": "7.5085",
                "RUB": "89.9113",
                "TRY": "10.4162",
                "AUD": "1.5793",
                "BRL": "6.3596",
                "CAD": "1.4708",
                "CNY": "7.8043",
                "HKD": "9.4853",
                "IDR": "17426.60",
                "INR": "89.1155",
                "KRW": "1355.39",
                "MXN": "24.3279",
                "MYR": "5.0446",
                "NZD": "1.6837",
                "PHP": "58.406",
                "SGD": "1.6169",
                "THB": "38.105",
                "ZAR": "16.8285",
            },
        }
        return _

    @pytest.fixture(scope="module")
    def fixt_additional_rates(self):
        """A simple dictionary providing additional rates for the Panamanian Balboa
        pegged to BASE at 1 BASE > 1 PAB, the Jordanian Dinar pegged to BASE at 1
        BASE > 0.71 JOD."""

        return {"PAB": 1, "JOD": 0.71}

    @pytest.fixture(scope="module")
    def fixt_additional_rates_custom(self):
        """A simple dictionary providing additional rates for the fictitious Gil pegged
        to BASE at 1 BASE > 1 GIL."""

        return {"GIL": 1}

    def test_basic_usage(self, fixt_rates_usd):
        """Check basic forex vector instance creation.

        The call should result in a rate of 1 for the `base` and a rate
        of `1 / value` for the value of each key in `rates` of the passed in mapping.
        """

        fo = lm.vector.forex(fixt_rates_usd)
        assert fo[0] == decimal.Decimal("0.01")
        assert fo[1] == decimal.Decimal(1)

    def test_currency_codes_in_mapping_case_insensitive(self):
        """Ensure that the currency codes used as keys and values in the input mapping
        are case insensitive. E.g. `{"base": "uSd", "rates": {"JpY": 100}}`,
        `{"base": "usd", "rates": {"jpy": 100}} and
        `{"base": "USD", "rates": {"JPY": 100}} are all treated equivalently."""

        fo = lm.vector.forex({"base": "USD", "rates": {"JPY": 100}})
        fo_lower = lm.vector.forex({"base": "usd", "rates": {"jpy": 100}})
        assert fo == fo_lower

    def test_with_rates_overrides(self, fixt_rates_usd, fixt_additional_rates):
        """Ensure passing in extra rates as keyword arguments overrides the rates in
        the resulting forex vector."""

        fo = lm.vector.forex(fixt_rates_usd, **fixt_additional_rates)
        pab = fo[fo.axes.index("PAB")]
        assert pab == 1
        jod = fo[fo.axes.index("JOD")]
        assert jod == decimal.Decimal("1.0") / decimal.Decimal("0.71")

    def test_with_rates_overrides_custom_currency(
        self, fixt_rates_jpy, fixt_additional_rates_custom
    ):
        """Ensure passing in extra rates as keyword arguments overrides the rates in
        the resulting forex vector even if the additional rates are for currencies
        that don't exist in the base rates dict."""

        fo = lm.vector.forex(fixt_rates_jpy, **fixt_additional_rates_custom)
        gil = fo[fo.axes.index("GIL")]
        assert gil == 1

    def test_from_api_sourced_rates(self, fixt_rates_usd, fixt_api_rates_usd):
        """Ensure that extra fields in the rates dict don't affect the results."""

        fo = lm.vector.forex(fixt_rates_usd)
        api_fo = lm.vector.forex(fixt_api_rates_usd)
        assert api_fo == fo

    def test_forex_integrity_error(self):
        """The `forex` function should raise a `linearmoney.exceptions.IntegrityError`
        if the provided rates contain a value that is less than or equal to 0 since
        that would break the math model of linear money."""

        with pytest.raises(IntegrityError):
            lm.vector.forex({"base": "USD", "rates": {"JPY": 0}})

        with pytest.raises(IntegrityError):
            lm.vector.forex({"base": "USD", "rates": {"JPY": -100}})

    def test_forex_constraints(self, fixt_api_rates):
        """ForexVectors must not have any components less than or equal to 0, and they
        must contain at least one component that is exactly equal to 1.

        See [linear money model](/linear_money.html#math-with-forex-rates) for details.
        """

        forex = lm.vector.forex(fixt_api_rates)
        found = False
        for r in forex:
            assert r > 0
            if r == 1:
                found = True
        assert found

    def test_forex_caching_regression(self):
        """This is a regression test to ensure that creating forex vectors
        with the same rates dict but different bases works correctly.

        The `forex` function was returning a forex vector that included the base
        of a previous call when called with a matching rates dict but a different
        base.

        This was caused by a caching problem in the private functions that
        build out the rates.
        """

        usd = lm.vector.forex({"base": "usd", "rates": {"jpy": 100}})
        assert usd.dim == 2
        eur = lm.vector.forex({"base": "eur", "rates": {"jpy": 100}})
        assert eur.dim == 2

        usd = lm.vector.forex({"base": "usd", "rates": {}})
        assert usd.dim == 1
        eur = lm.vector.forex({"base": "eur", "rates": {}})
        assert eur.dim == 1
