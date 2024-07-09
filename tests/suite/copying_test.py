import copy
import pickle

import pytest
from pytest_lazy_fixtures import lf


@pytest.fixture(
    scope="module",
    params=[
        lf("fixt_asset_usd"),
        lf("fixt_asset_composite"),
        lf("fixt_forex_usd"),
        lf("fixt_basis_usd"),
        lf("fixt_space"),
        lf("fixt_currency_usd"),
        lf("fixt_locale_en"),
    ],
    ids=[
        "asset_vector",
        "composite_asset_vector",
        "forex_vector",
        "basis_vector",
        "space",
        "currency",
        "locale",
    ],
)
def fixt_ins(request):
    return request.param


def test_pickling(fixt_ins):
    """Ensure pickling works as expected."""

    stored_ins = pickle.dumps(fixt_ins)
    restored_ins = pickle.loads(stored_ins)
    assert restored_ins == fixt_ins


def test_copy(fixt_ins):
    """Basic test of python's shallow copy.

    This test doesn't check the actual copying of objects because all of the classes
    in the linearmoney package are immutable and simply return self when
    copied, so any test for copying functionality would have to test
    implementation details.

    Instead, this test is intended to quicly catch errors in the shallow copy system,
    not to test its specific functionality as that will be tested through its
    use in other parts of the system.
    """

    cp = copy.copy(fixt_ins)
    assert cp == fixt_ins


def test_deepcopy(fixt_ins):
    """Basic test of python's deep copy.

    This test doesn't check the actual copying of objects because all of the classes
    in the linearmoney package are immutable and simply return self when
    copied, so any test for copying functionality would have to test
    implementation details.

    Instead, this test is intended to quicly catch errors in the deep copy system, not
    to test its specific functionality as that will be tested through its use
    in other parts of the system.
    """

    cp = copy.deepcopy(fixt_ins)
    assert cp == fixt_ins
