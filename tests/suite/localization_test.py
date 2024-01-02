"""Test cases related to localization and formatting of monetary values."""

import pytest

from pytest_lazy_fixtures import lf
from pytest_parametrize_cases import parametrize_cases, Case

import linearmoney as lm

# TODO Write test case for formatting of locale with grouping of [-1]

# Fixtures #


# JPY Formatted Strings #
@pytest.fixture(scope="class")
def fixt_formatted_positive_jpy(fixt_yen_symbol):
    return "".join([fixt_yen_symbol, "1,000,000"])


@pytest.fixture(scope="class")
def fixt_formatted_positive_jpy_with_jp_locale_symbol(fixt_yen_symbol_jp_locale):
    return "".join([fixt_yen_symbol_jp_locale, "1,000,000"])


@pytest.fixture(scope="class")
def fixt_formatted_negative_jpy_standard(fixt_yen_symbol):
    return "".join(["-", fixt_yen_symbol, "1,000,000"])


@pytest.fixture(scope="class")
def fixt_formatted_negative_jpy_accounting(fixt_yen_symbol):
    return "".join(["(", fixt_yen_symbol, "1,000,000)"])


@pytest.fixture(scope="class")
def fixt_formatted_negative_jpy_with_jp_locale_symbol_standard(
    fixt_yen_symbol_jp_locale,
):
    return "".join(["-", fixt_yen_symbol_jp_locale, "1,000,000"])


@pytest.fixture(scope="class")
def fixt_formatted_negative_jpy_with_jp_locale_symbol_accounting(
    fixt_yen_symbol_jp_locale,
):
    return "".join(["(", fixt_yen_symbol_jp_locale, "1,000,000)"])


@pytest.fixture(scope="class")
def fixt_formatted_positive_jpy_international():
    return "JPY 1,000,000"


@pytest.fixture(scope="class")
def fixt_formatted_negative_jpy_international_standard():
    return "JPY -1,000,000"


@pytest.fixture(scope="class")
def fixt_formatted_negative_jpy_international_accounting():
    return "(JPY 1,000,000)"


# USD Formatted Strings #
@pytest.fixture(scope="class")
def fixt_formatted_positive_usd():
    return "$10,000.00"


@pytest.fixture(scope="class")
def fixt_formatted_negative_usd_standard():
    return "-$10,000.00"


@pytest.fixture(scope="class")
def fixt_formatted_negative_usd_accounting():
    return "($10,000.00)"


@pytest.fixture(scope="class")
def fixt_formatted_positive_usd_international():
    return "USD 10,000.00"


@pytest.fixture(scope="class")
def fixt_formatted_negative_usd_international_standard():
    return "USD -10,000.00"


@pytest.fixture(scope="class")
def fixt_formatted_negative_usd_international_accounting():
    return "(USD 10,000.00)"


# Preconfigured Assets #
@pytest.fixture(scope="class")
def fixt_positive_l10n_asset(fixt_space):
    """Provides a rudimentary asset suitable for testing the
    l10n() method for positive values."""

    return lm.vector.asset("1000000.0000", "jpy", fixt_space)


@pytest.fixture(scope="class")
def fixt_negative_l10n_asset(fixt_space):
    """Provides a rudimentary asset suitable for testing the
    l10n() method for negative values."""

    return lm.vector.asset("-1000000.0000", "jpy", fixt_space)


# Test Cases #


@parametrize_cases(
    Case(
        "positive_usd",
        locale=lm.data.locale("en", "us", nformat="standard"),
        iso_code="USD",
        asset=lf("fixt_positive_l10n_asset"),
        expected=lf("fixt_formatted_positive_usd"),
    ),
    Case(
        "negative_usd_standard",
        locale=lm.data.locale("en", "us", nformat="standard"),
        iso_code="USD",
        asset=lf("fixt_negative_l10n_asset"),
        expected=lf("fixt_formatted_negative_usd_standard"),
    ),
    Case(
        "negative_usd_accounting",
        locale=lm.data.locale("en", "us", nformat="accounting"),
        iso_code="USD",
        asset=lf("fixt_negative_l10n_asset"),
        expected=lf("fixt_formatted_negative_usd_accounting"),
    ),
    Case(
        "positive_jpy",
        locale=lm.data.locale("en", "us", nformat="standard"),
        iso_code="JPY",
        asset=lf("fixt_positive_l10n_asset"),
        expected=lf("fixt_formatted_positive_jpy"),
    ),
    Case(
        "negative_jpy_standard",
        locale=lm.data.locale("en", "us", nformat="standard"),
        iso_code="JPY",
        asset=lf("fixt_negative_l10n_asset"),
        expected=lf("fixt_formatted_negative_jpy_standard"),
    ),
    Case(
        "negative_jpy_accounting",
        locale=lm.data.locale("en", "us", nformat="accounting"),
        iso_code="JPY",
        asset=lf("fixt_negative_l10n_asset"),
        expected=lf("fixt_formatted_negative_jpy_accounting"),
    ),
    Case(
        "positive_jpy_jp_locale",
        locale=lm.data.locale("ja", "jp", nformat="standard"),
        iso_code="JPY",
        asset=lf("fixt_positive_l10n_asset"),
        expected=lf("fixt_formatted_positive_jpy_with_jp_locale_symbol"),
    ),
    Case(
        "negative_jpy_standard_jp_locale",
        locale=lm.data.locale("ja", "jp", nformat="standard"),
        iso_code="JPY",
        asset=lf("fixt_negative_l10n_asset"),
        expected=lf("fixt_formatted_negative_jpy_with_jp_locale_symbol_standard"),
    ),
    Case(
        "negative_jpy_accounting_jp_locale",
        locale=lm.data.locale("ja", "jp", nformat="accounting"),
        iso_code="JPY",
        asset=lf("fixt_negative_l10n_asset"),
        expected=lf("fixt_formatted_negative_jpy_with_jp_locale_symbol_accounting"),
    ),
)
def test_basic_l10n(locale, iso_code, asset, expected, fixt_forex_usd):
    """Basic localization functionality."""

    val = lm.vector.evaluate(asset, iso_code, fixt_forex_usd)
    currency = lm.data.currency(iso_code)
    rounded_val = lm.scalar.roundas(val, currency)
    assert lm.scalar.l10n(rounded_val, currency, locale) == expected


@parametrize_cases(
    Case(
        "positive_usd",
        locale=lm.data.locale("en", "us", nformat="standard"),
        iso_code="USD",
        asset=lf("fixt_positive_l10n_asset"),
        expected=lf("fixt_formatted_positive_usd_international"),
    ),
    Case(
        "negative_usd_standard",
        locale=lm.data.locale("en", "us", nformat="standard"),
        iso_code="USD",
        asset=lf("fixt_negative_l10n_asset"),
        expected=lf("fixt_formatted_negative_usd_international_standard"),
    ),
    Case(
        "negative_usd_accounting",
        locale=lm.data.locale("en", "us", nformat="accounting"),
        iso_code="USD",
        asset=lf("fixt_negative_l10n_asset"),
        expected=lf("fixt_formatted_negative_usd_international_accounting"),
    ),
    Case(
        "positive_jpy",
        locale=lm.data.locale("en", "us", nformat="standard"),
        iso_code="JPY",
        asset=lf("fixt_positive_l10n_asset"),
        expected=lf("fixt_formatted_positive_jpy_international"),
    ),
    Case(
        "negative_jpy_standard",
        locale=lm.data.locale("en", "us", nformat="standard"),
        iso_code="JPY",
        asset=lf("fixt_negative_l10n_asset"),
        expected=lf("fixt_formatted_negative_jpy_international_standard"),
    ),
    Case(
        "negative_jpy_accounting",
        locale=lm.data.locale("en", "us", nformat="accounting"),
        iso_code="JPY",
        asset=lf("fixt_negative_l10n_asset"),
        expected=lf("fixt_formatted_negative_jpy_international_accounting"),
    ),
    Case(
        "positive_jpy_jp_locale",
        locale=lm.data.locale("ja", "jp", nformat="standard"),
        iso_code="JPY",
        asset=lf("fixt_positive_l10n_asset"),
        expected=lf("fixt_formatted_positive_jpy_international"),
    ),
    Case(
        "negative_jpy_standard_jp_locale",
        locale=lm.data.locale("ja", "jp", nformat="standard"),
        iso_code="JPY",
        asset=lf("fixt_negative_l10n_asset"),
        expected=lf("fixt_formatted_negative_jpy_international_standard"),
    ),
    Case(
        "negative_jpy_accounting_jp_locale",
        locale=lm.data.locale("ja", "jp", nformat="accounting"),
        iso_code="JPY",
        asset=lf("fixt_negative_l10n_asset"),
        expected=lf("fixt_formatted_negative_jpy_international_accounting"),
    ),
)
def test_l10n_international(locale, iso_code, asset, expected, fixt_forex_usd):
    """International format."""

    val = lm.vector.evaluate(asset, iso_code, fixt_forex_usd)
    currency = lm.data.currency(iso_code)
    rounded_val = lm.scalar.roundas(val, currency)
    assert lm.scalar.l10n(rounded_val, currency, locale, international=True) == expected


@parametrize_cases(
    Case(
        "sign_position_1_symbol_after",
        overrides={
            "negative_sign_position": 1,
            "negative_symbol_before": False,
        },
        expected="-10,000.00$",
    ),
    Case(
        "sign_position_1_symbol_space_1_symbol_after",
        overrides={
            "negative_sign_position": 1,
            "negative_symbol_space": 1,
            "negative_symbol_before": False,
        },
        expected="-10,000.00 $",
    ),
    Case(
        "sign_position_1_symbol_space_2_symbol_after",
        overrides={
            "negative_sign_position": 1,
            "negative_symbol_space": 2,
            "negative_symbol_before": False,
        },
        expected="- 10,000.00$",
    ),
    Case(
        "sign_position_2",
        overrides={"negative_sign_position": 2},
        expected="$10,000.00-",
    ),
    Case(
        "sign_position_2_symbol_space_1",
        overrides={
            "negative_sign_position": 2,
            "negative_symbol_space": 1,
        },
        expected="$ 10,000.00-",
    ),
    Case(
        "sign_position_2_symbol_space_2",
        overrides={
            "negative_sign_position": 2,
            "negative_symbol_space": 2,
        },
        expected="$10,000.00 -",
    ),
    Case(
        "sign_position_3_symbol_after",
        overrides={
            "negative_sign_position": 3,
            "negative_symbol_before": False,
        },
        expected="10,000.00-$",
    ),
    Case(
        "sign_position_3_symbol_after_symbol_space_1",
        overrides={
            "negative_sign_position": 3,
            "negative_symbol_before": False,
            "negative_symbol_space": 1,
        },
        expected="10,000.00 -$",
    ),
    Case(
        "sign_position_3_symbol_after_symbol_space_2",
        overrides={
            "negative_sign_position": 3,
            "negative_symbol_before": False,
            "negative_symbol_space": 2,
        },
        expected="10,000.00- $",
    ),
    Case(
        "sign_position_4_symbol_after",
        overrides={
            "negative_sign_position": 4,
            "negative_symbol_before": False,
        },
        expected="10,000.00$-",
    ),
    Case(
        "sign_position_4_symbol_after_symbol_space_1",
        overrides={
            "negative_sign_position": 4,
            "negative_symbol_before": False,
            "negative_symbol_space": 1,
        },
        expected="10,000.00 $-",
    ),
    Case(
        "sign_position_4_symbol_after_symbol_space_2",
        overrides={
            "negative_sign_position": 4,
            "negative_symbol_before": False,
            "negative_symbol_space": 2,
        },
        expected="10,000.00$ -",
    ),
)
def test_l10n_with_formatting_overrides(
    fixt_negative_l10n_asset, overrides, expected, fixt_forex_usd
):
    """Localization with overriden formatting data."""

    iso_code = "usd"
    lc = lm.data.locale("en", "us", **overrides)
    val = lm.vector.evaluate(fixt_negative_l10n_asset, iso_code, fixt_forex_usd)
    currency = lm.data.currency(iso_code)
    rounded_val = lm.scalar.roundas(val, currency)
    assert lm.scalar.l10n(rounded_val, currency, lc) == expected


def test_l10n_non_ascii_format(
    fixt_positive_l10n_asset,
    fixt_euro_symbol,
    fixt_french_thousands_space,
    fixt_forex_usd,
):
    """Ensure that the `l10n` function generates the correct output in
    locales that use non-ASCII characters in their formatting data."""

    lc = lm.data.locale("fr", "fr")
    val_eur = lm.vector.evaluate(fixt_positive_l10n_asset, "eur", fixt_forex_usd)
    curr_eur = lm.data.currency("eur")
    rounded_val_eur = lm.scalar.roundas(val_eur, curr_eur)
    assert lm.scalar.l10n(rounded_val_eur, curr_eur, lc) == "".join(
        ["4", fixt_french_thousands_space, "000,00", fixt_euro_symbol]
    )
    val_usd = lm.vector.evaluate(fixt_positive_l10n_asset, "usd", fixt_forex_usd)
    curr_usd = lm.data.currency("usd")
    rounded_val_usd = lm.scalar.roundas(val_usd, curr_usd)
    assert lm.scalar.l10n(rounded_val_usd, curr_usd, lc) == "".join(
        ["10", fixt_french_thousands_space, "000,00$US"]
    )


def test_l10n_multiple_groupings(fixt_indian_rupee_symbol, fixt_space, fixt_forex_usd):
    """Ensure that the `l10n` function generates the correct output in
    locales that use two or more different groupings for the numeric
    portion of a formatted currency string."""

    lc = lm.data.locale("hi", "in")
    inr = lm.vector.asset("1000000000", "inr", fixt_space)
    val = lm.vector.evaluate(inr, "inr", fixt_forex_usd)
    currency = lm.data.currency("inr")
    rounded_val = lm.scalar.roundas(val, currency)
    assert lm.scalar.l10n(rounded_val, currency, lc) == "".join(
        [fixt_indian_rupee_symbol, "1,00,00,00,000.00"]
    )


def test_l10n_multiple_groupings_small_number(
    fixt_indian_rupee_symbol, fixt_space, fixt_forex_usd
):
    """Ensure that the `l10n` function generates the correct output in
    locales that use two or more different groupings when used on a number
    that is too small to have more than one grouping."""

    lc = lm.data.locale("hi", "in")
    inr = lm.vector.asset("1000", "inr", fixt_space)
    val = lm.vector.evaluate(inr, "inr", fixt_forex_usd)
    currency = lm.data.currency("inr")
    rounded_val = lm.scalar.roundas(val, currency)
    assert lm.scalar.l10n(rounded_val, currency, lc) == "".join(
        [fixt_indian_rupee_symbol, "1,000.00"]
    )


def test_l10n_currency_with_None_symbol(fixt_space, fixt_forex_usd):
    """Ensure that calling l10n() with a currency that has None as its
    symbol in the locale data correctly formats the
    result as if the `international` keyword argument had been passed as True."""

    lc = lm.data.locale("en", "us", currency_symbols={"usd": None})
    sut = lm.vector.asset("10", "usd", fixt_space)
    val = lm.vector.evaluate(sut, "usd", fixt_forex_usd)
    currency = lm.data.currency("usd")
    rounded_val = lm.scalar.roundas(val, currency)
    assert lm.scalar.l10n(rounded_val, currency, lc) == "USD 10.00"


def test_l10n_does_not_group_decimal_portion(fixt_space, fixt_forex_usd):
    """Ensure that the `l10n` function does not adding grouping separators
    to the decimal portion of the `amount` argument if it is longer than the
    grouping value for the locale."""

    lc = lm.data.locale("en", "us")  # Groups every three digits with a comma.
    sut = lm.vector.asset(1000000.111111111111, "usd", fixt_space)
    val = lm.vector.evaluate(sut, "usd", fixt_forex_usd)
    localized_val = lm.scalar.l10n(val, lm.data.currency("usd"), lc)
    integral, fractional = localized_val.split(".")
    assert "," not in fractional
