import threading
import decimal
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from pytest_lazy_fixtures import lf

import linearmoney as lm
from linearmoney.vector import MoneyVector
from linearmoney.data import DataMap


def pytest_deselected(items):
    if not items:
        return
    config = items[0].session.config
    reporter = config.pluginmanager.getplugin("terminalreporter")
    reporter.ensure_newline()
    for item in items:
        reporter.line(f"deselected: {item.nodeid}", yellow=True, bold=True)


def pytest_sessionstart(session):
    # Force banker's rounding for test cases.
    decimal.DefaultContext.rounding = "ROUND_HALF_EVEN"
    decimal.getcontext().rounding = "ROUND_HALF_EVEN"


@pytest.fixture(scope="session")
def fixt_yen_symbol_jp_locale():
    return "￥"


@pytest.fixture(scope="session")
def fixt_yen_symbol():
    return "¥"


@pytest.fixture(scope="session")
def fixt_euro_symbol():
    return "€"


@pytest.fixture(scope="session")
def fixt_french_thousands_space():
    return "\u202f"


@pytest.fixture(scope="session")
def fixt_indian_rupee_symbol():
    return "₹"


class ExcThread(threading.Thread):
    def run(self):
        self.exc = None
        try:
            super().run()
        except Exception as e:
            self.exc = e

    def join(self):
        super().join()
        if self.exc is not None:
            raise self.exc


@pytest.fixture(scope="session")
def FixtExcThread():
    return ExcThread


_unbuilt_rates = {
    "base": "USD",
    "date": "2-22-2022",
    "rates": {
        "CAD": "1.25",
        "CNY": "125.0",
        "EUR": "0.4",
        "GBP": "0.8",
        "INR": "80.0",
        "JPY": "100.0",
    },
}

_unbuilt_three_rates = {
    "base": "USD",
    "date": "2-22-2022",
    "rates": {
        "EUR": "0.4",
        "JPY": "100.0",
    },
}


def _three_forex_usd():
    return lm.vector.forex(_unbuilt_three_rates)


def _three_space():
    return lm.vector.space(_three_forex_usd())


@pytest.fixture(scope="session")
def fixt_three_forex_usd():
    return _forex_usd()


@pytest.fixture(scope="session")
def fixt_three_space():
    return _three_space()


def _forex_usd():
    return lm.vector.forex(_unbuilt_rates)


def _space():
    return lm.vector.space(_forex_usd())


@pytest.fixture(scope="session")
def fixt_forex_usd():
    return _forex_usd()


@pytest.fixture(scope="session")
def fixt_space():
    return _space()


@pytest.fixture(scope="session")
def fixt_basis_usd(fixt_space):
    return lm.vector.basis_vector(fixt_space, "USD")


@pytest.fixture(scope="session", params=_space().axes, ids=_space().axes)
def fixt_iso_codes(request):
    return request.param


@pytest.fixture(scope="session")
def fixt_asset_usd(fixt_space):
    """Rudimentary asset vector in USD."""

    return lm.vector.asset(10, "usd", fixt_space)


@pytest.fixture(scope="session")
def fixt_asset_jpy(fixt_space):
    """Rudimentary asset vector in jpy."""

    return lm.vector.asset(1000, "jpy", fixt_space)


@pytest.fixture(scope="session")
def fixt_asset_composite(fixt_space):
    """Provides a composite asset with the same potential value as the `fixt_usd` and
    `fixt_jpy` fixtures."""

    return lm.vector.asset(5, "usd", fixt_space) + lm.vector.asset(
        500, "jpy", fixt_space
    )


@pytest.fixture(
    scope="session",
    params=[
        lf("fixt_asset_usd"),
        lf("fixt_asset_jpy"),
        lf("fixt_asset_composite"),
    ],
    ids=["rudimentary_usd", "rudimentary_jpy", "composite"],
)
def fixt_assets(request):
    """Parametrized fixture providing rudimentary asset vectors with
    different currencies and also a composite asset.

    Useful for test cases that need to test functionality that does not depend on any
    specific currency.
    """

    return request.param


@pytest.fixture(
    scope="session",
    params=[
        lf("fixt_asset_usd"),
        lf("fixt_asset_jpy"),
        lf("fixt_asset_composite"),
        lf("fixt_forex_usd"),
        lf("fixt_basis_usd"),
    ],
    ids=[
        "rudimentary_usd",
        "rudimentary_jpy",
        "composite",
        "forex_vector",
        "basis_vector",
    ],
)
def fixt_vectors(request):
    """Parametrized fixture providing an example of each vector type and meaningful
    variation.

    Useful for tests that need to provide the same behavior across all vectors, but
    are not concerned with the specific value of the vector.
    """

    return request.param


@pytest.fixture(scope="module")
def fixt_currency_usd():
    """Fixture returning the default CurrencyData for "USD"."""

    return lm.data.currency("USD")


@pytest.fixture(scope="module")
def fixt_currency_jpy():
    """Fixture returning the default CurrencyData for "JPY"."""

    return lm.data.currency("JPY")


@pytest.fixture(scope="module")
def fixt_locale_en():
    """Fixture returning a single LocaleData instance for en_US."""

    return lm.data.locale("en", "US")


@pytest.fixture(scope="module")
def fixt_locale_ja():
    """Fixture returning a single LocaleData instance for ja_JP."""

    return lm.data.locale("ja", "JP")


@pytest.fixture(scope="function")
def fixt_no_caching():
    stored_enabled = lm.cache.is_enabled()
    lm.cache.enable(False)
    yield None
    lm.cache.enable(stored_enabled)


@pytest.fixture(scope="function")
def fixt_restore_global_cache():
    """A fixture that will store the current global cache's state before
    the test case is executed and then restore it after the test case finishes.

    Use with @pytest.mark.usefixtures()
    """

    stored_bs = lm.cache.get_base_size()
    stored_enabled = lm.cache.is_enabled()
    yield None
    lm.cache.set_base_size(stored_bs)
    lm.cache.enable(stored_enabled)


helpers = SimpleNamespace()


@contextmanager
def _does_not_raise(exception):
    """The opposite of `pytest.raises`."""

    try:
        yield
    except exception:
        raise pytest.fail("Raised {0}".format(exception))


helpers.does_not_raise = _does_not_raise


def _vector_to_tuple(vec: MoneyVector) -> tuple[decimal.Decimal, ...]:
    """MoneyVectors are compared by hash, so we use this helper to convert a
    MoneyVector to a regular tuple to make comparison of vector values to expected
    output in test cases easier."""

    return tuple([i for i in vec])


helpers.vector_to_tuple = _vector_to_tuple


def _decimal_tuple(*args: int | float) -> tuple[decimal.Decimal, ...]:
    r"""Converts all of a tuple's elements to `decimal.Decimal`, so that we don't have
    to repeat calls to the `decimal.Decimal` contructor in long numeric tuple
    definitions.

    Any `float`s provided as `*args` will be stringified before being
    constructed to make sure the result reflects the input exactly.
    """

    return tuple([decimal.Decimal(str(i)) for i in args])


helpers.decimal_tuple = _decimal_tuple


def _map_to_dict(map_obj: DataMap) -> dict:
    """Recursively converts an immutable map to a mutable dict for easier comparisons
    in the test suite."""

    new_dict = {}
    for k, v in map_obj.items():
        if isinstance(v, DataMap):
            # We should not hit the recursion limit with any data structures used
            # in the linearmoney library.
            new_dict[k] = _map_to_dict(v)
        else:
            new_dict[k] = v
    return new_dict


helpers.map_to_dict = _map_to_dict
