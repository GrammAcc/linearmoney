import decimal
import fractions

import pytest
from pytest_parametrize_cases import Case, parametrize_cases

import linearmoney as lm
from linearmoney.exceptions import CacheError


def test_size():
    """The size() method should return the total number of return values cached
    among all cached functions if called with no arguments."""

    @lm.cache.cached()
    def _add1(num: int) -> int:
        return num + 1

    @lm.cache.cached()
    def _add2(num: int) -> int:
        return num + 2

    cur_size = lm.cache.size()
    _add1(20)  # Hit the cache.
    _add2(20)  # Hit the cache.
    assert lm.cache.size() == cur_size + 2
    for i in range(10):
        # Hit the cache some more.
        _add1(i)
        _add2(i)
    assert lm.cache.size() == cur_size + 22

    _add1(20)  # Shouldn't add to the cache.
    _add2(20)  # Shouldn't add to the cache.
    assert lm.cache.size() == cur_size + 22


def test_size_specific_cache():
    """The size() method should return the total number of return values cached
    for the specified function if called with the `cached_func` argument."""

    @lm.cache.cached()
    def _add1(num: int) -> int:
        return num + 1

    # Cached functions need to be called once before the function cache is actually
    # created.
    _add1(40)
    assert lm.cache.size(_add1) == 1
    _add1(20)  # Hit the cache.
    assert lm.cache.size(_add1) == 2
    for i in range(10):
        _add1(i)  # Hit the cache some more.
    assert lm.cache.size(_add1) == 12

    _add1(20)  # Shouldn't add a new value.
    assert lm.cache.size(_add1) == 12


def test_invalidate_entire_cache():
    """The invalidate() method should invalidate all data in the cache if called
    without arguments."""

    @lm.cache.cached()
    def _add1(num: int) -> int:
        return num + 1

    _add1(2)  # Ensure the cache isn't empty.

    assert lm.cache.size() > 0
    lm.cache.invalidate()
    assert lm.cache.size() == 0


def test_invalidate_specific_funccache():
    """The invalidate() method should invalidate all data from the specified function's
    cache if called with the `cached_func` argument."""

    @lm.cache.cached()
    def _add1(num: int) -> int:
        return num + 1

    @lm.cache.cached()
    def _add2(num: int) -> int:
        return num + 2

    _add1(2)  # Ensure the cache isn't empty.
    _add2(2)  # Ensure the cache isn't empty.
    assert lm.cache.size(_add1) == 1
    assert lm.cache.size(_add2) == 1
    lm.cache.invalidate(_add1)
    assert lm.cache.size(_add1) == 0
    assert lm.cache.size(_add2) == 1


def test_max_size():
    """The `max_size` function returns the maximum number of cache entries for the
    specified `cached_func` before the LRU algorithm begins evicting old values.

    A cached function's max size is determined by the `base_size` of the cache and
    the `size_multiplier` of the function cache, which should be passed as an
    argument to the caching decorator and is not public."""

    @lm.cache.cached()
    def _add1(num: int) -> int:
        return num + 1

    @lm.cache.cached(size_multiplier=2)
    def _mul2(num: int) -> int:
        return num * 2

    @lm.cache.cached(size_multiplier=0.5)
    def _div2(num: float) -> float:
        return num / 2

    # Cached functions need to be called once before the function cache is actually
    # created.
    _add1(1)
    _mul2(2)
    _div2(4)
    assert lm.cache.max_size(_add1) == 256  # Default `base_size` for the cache.
    assert lm.cache.max_size(_mul2) == 512  # Multiplied by the `size_multipler`.
    assert lm.cache.max_size(_div2) == 128  # Multiplied by the `size_multipler`.


def test_setget_base_size():
    """The `base_size` of the cache is used to determine
    the `max_size` of each individual function cache based on the individual
    cache's `size_multiplier`."""

    assert lm.cache.get_base_size() == 256  # The default `base_size`.

    @lm.cache.cached(size_multiplier=2)
    def _add1(num: int) -> int:
        return num + 1

    # Cached functions need to be called once before the function cache is actually
    # created.
    _add1(1)

    assert lm.cache.max_size(_add1) == 512
    lm.cache.set_base_size(384)
    assert lm.cache.max_size(_add1) == 768


_valid_values = [
    112,
    112.12,
    decimal.Decimal(112.12),
    # Fractions don't have SupportsInt protocol until python 3.11.
    # fractions.Fraction(225, 2),
]


@pytest.fixture(
    scope="module",
    params=_valid_values,
    ids=[i.__class__.__name__ for i in _valid_values],
)
def fixt_valid_base_size_types(request):
    return request.param


def test_set_base_size_valid_input(fixt_valid_base_size_types):
    """The `set_base_size` should accept any type that `SupportsInt` and convert the
    value to an integer."""

    lm.cache.set_base_size(fixt_valid_base_size_types)
    assert isinstance(lm.cache.get_base_size(), int)
    assert lm.cache.get_base_size() == 112


_invalid_values = [
    {},
    [],
    set(),
    tuple(),
    "some_bad_input",
]


@pytest.fixture(
    scope="module",
    params=_invalid_values,
    ids=[i.__class__.__name__ for i in _invalid_values],
)
def fixt_invalid_base_size_types(request):
    return request.param


def test_set_base_size_invalid_input(fixt_invalid_base_size_types):
    """The `set_base_size` function should raise a TypeError if the provided value is
    not an `int`."""

    with pytest.raises(TypeError):
        lm.cache.set_base_size(fixt_invalid_base_size_types)


@parametrize_cases(
    Case("max_size", func=lm.cache.max_size),
    Case("size_with_arg", func=lm.cache.size),
    Case("invalidate_with_arg", func=lm.cache.invalidate),
    Case("tail", func=lm.cache.tail),
    Case("head", func=lm.cache.head),
)
def test_cache_not_found_error(func):
    """Functions in the cache module that accept a `cached_func` as an argument
    should raise a `CacheError` if the passed function is not cached."""

    def _add1(num: int) -> int:
        return num + 1

    _add1(1)

    with pytest.raises(CacheError):
        func(_add1)


@parametrize_cases(
    Case("max_size", func=lm.cache.max_size),
    Case("size_with_arg", func=lm.cache.size),
    Case("invalidate_with_arg", func=lm.cache.invalidate),
    Case("tail", func=lm.cache.tail),
    Case("head", func=lm.cache.head),
)
def test_cache_not_found_error_before_first_call(func):
    """The caches for functions and methods lm.cached with the @cache.cached()
    decorator won't actually be created until the first time the function/method
    is called, so attempting any of the cache functions that requests a specific
    funccache before the first call to the `cached_func` will still raise a
    CacheError, even though the function was decorated with @cache.cached().
    """

    @lm.cache.cached()
    def _add1(num: int) -> int:
        return num + 1

    with pytest.raises(CacheError):
        func(_add1)


def test_max_size_not_exceeded():
    """Ensure that caching more values than the calculated `max_size` of a cached
    function does not cache more values than the function cache's `max_size`."""

    @lm.cache.cached()
    def _add1(num: int) -> int:
        return num + 1

    # Cached functions need to be called once before the function cache is actually
    # created.
    _add1(1)

    for i in range(lm.cache.max_size(_add1) + 5):
        _add1(i)
    assert lm.cache.size(_add1) == lm.cache.max_size(_add1)


def test_tail_updated_after_write():
    """Ensure that the LRU algorithm is properly placing newly written values
    at the *tail* of the cache."""

    @lm.cache.cached()
    def _add1(num: int) -> int:
        return num + 1

    _add1(1)  # Hit the cache.
    assert lm.cache.tail(_add1) == 2
    _add1(3)  # Hit the cache.
    assert lm.cache.tail(_add1) == 4
    _add1(7)  # Hit the cache.
    assert lm.cache.tail(_add1) == 8


def test_tail_updated_after_read():
    """Ensure that the LRU algorithm is properly placing the latest read value
    at the *tail* of the cache."""

    @lm.cache.cached()
    def _add1(num: int) -> int:
        return num + 1

    _add1(1)  # Hit the cache.
    _add1(3)  # Hit the cache.
    _add1(7)  # Hit the cache.

    assert lm.cache.tail(_add1) == 8  # The latest call.

    _add1(3)  # Move to the *tail* of the cache.

    assert lm.cache.tail(_add1) == 4


def test_head_is_least_recently_used():
    """Ensure that the order of cached values is properly updated and the *head*
    is in fact the least recently used value in the cache."""

    @lm.cache.cached()
    def _add1(num: int) -> int:
        return num + 1

    _add1(1)  # Hit the cache.
    _add1(3)  # Hit the cache.
    _add1(7)  # Hit the cache.

    assert lm.cache.head(_add1) == 2  # _add(1)

    # Move to the *tail* of the cache.
    _add1(3)
    _add1(1)

    assert lm.cache.head(_add1) == 8  # _add(7) should now be the *head*


@pytest.mark.usefixtures("fixt_restore_global_cache")
def test_enable_and_disable():
    """Ensure that enabling/disabling the cache works as expected."""

    lm.cache.enable(True)

    @lm.cache.cached()
    def _add1(num: int) -> int:
        return num + 1

    _add1(1)  # Hit the cache.

    assert lm.cache.size(_add1) == 1

    lm.cache.enable(False)

    _add1(2)  # Shouldn't hit the cache when disabled.

    assert lm.cache.size(_add1) == 1

    lm.cache.enable(True)

    _add1(2)  # Should hit the cache after reenabling.

    assert lm.cache.size(_add1) == 2


def test_caching_with_numeric_inputs_of_different_types(fixt_space):
    """This is a regression test.

    Unsupported numeric types passed to operators are hashed as arguments
    and used as part of the cache key, so subsequent calls with correctly
    supported numeric types with the same numeric value were returning
    NotImplemented due to numeric types hashing by value, resulting in
    identical cache keys.
    """

    usd = lm.vector.asset(10, "usd", fixt_space)
    with pytest.raises(TypeError):
        usd * fractions.Fraction(2, 1)
    assert usd.__mul__(decimal.Decimal("2")) != NotImplemented


def test_hash_collisions(fixt_space, fixt_forex_usd):
    """Ensure that two different arguments that result in a hash collision
    will be correctly cached separately."""

    av = lm.vector.asset(-2, "usd", fixt_space)
    assert lm.vector.evaluate(av, "usd", fixt_forex_usd) == -2
    av = lm.vector.asset(-1, "usd", fixt_space)
    assert lm.vector.evaluate(av, "usd", fixt_forex_usd) == -1


def test_decimal_hash_collisions_regression():
    """Regression test to ensure that the cache hashes Decimals with different
    precision but equal value differently."""

    @lm.cache.cached()
    def _mul1(num: decimal.Decimal) -> decimal.Decimal:
        return num * decimal.Decimal("1.00")

    two_places = decimal.Decimal("2.00")
    four_places = decimal.Decimal("2.0000")
    assert two_places == four_places
    # Positional argument hashing.
    assert str(_mul1(two_places)) == "2.0000"
    assert str(_mul1(four_places)) == "2.000000"
    # Keyword argument hashing.
    assert str(_mul1(num=two_places)) == "2.0000"
    assert str(_mul1(num=four_places)) == "2.000000"
