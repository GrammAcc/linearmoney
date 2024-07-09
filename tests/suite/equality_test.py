from collections.abc import Hashable

import pytest
from pytest_lazy_fixtures import lf


@pytest.fixture(
    scope="module",
    params=[
        lf("fixt_asset_usd"),
        lf("fixt_forex_usd"),
        lf("fixt_basis_usd"),
        lf("fixt_space"),
        lf("fixt_currency_usd"),
        lf("fixt_locale_en"),
    ],
    ids=[
        "asset_vector",
        "forex_vector",
        "basis_vector",
        "space",
        "currency",
        "locale",
    ],
)
def fixt_library_hashables(request):
    return request.param


class _MockHashable:
    """Mock Class with the same hash as the instance passed to its constructor."""

    def __init__(self, ins: Hashable) -> None:
        self._hash = hash(ins)

    def __hash__(self) -> int:
        return self._hash


_mock_not_hashable = object()
"""Mock instance that is not Hashable."""


def test_equality_by_hash(fixt_library_hashables):
    """Ensure that the `linearmoney.mixins.EqualityByHashMixin` implementation
    of __eq__ gives correct results."""

    hashable_ins = _MockHashable(fixt_library_hashables)
    assert fixt_library_hashables == hashable_ins
    assert fixt_library_hashables != _mock_not_hashable
