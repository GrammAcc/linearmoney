import locale as posix_locale

import pytest
from pytest_lazy_fixtures import lf
from pytest_parametrize_cases import Case, parametrize_cases

import linearmoney as lm
from linearmoney.exceptions import UnknownDataError
from tests.conftest import helpers


@pytest.fixture(scope="module")
def fixt_en():
    """Fixture returning a single LocaleData instance for the en_US locale."""

    return lm.data.locale("en", "us")


@pytest.fixture(scope="module")
def fixt_formatting_standard():
    """A dictionary containing the default standard format data for all locales
    with built-in support."""

    return lm.resources.get_package_resource("locales")["standard"]


@pytest.fixture(scope="module")
def fixt_formatting_accounting():
    """A dictionary containing the default accounting format data for all locales
    with built-in support."""

    return lm.resources.get_package_resource("locales")["accounting"]


def test_basic_usage(fixt_en, fixt_formatting_standard):
    """Basic LocaleData creation."""

    assert helpers.map_to_dict(fixt_en.data) == fixt_formatting_standard["en_US"]


#    for k, v in fixt_formatting_standard["en_US"].items():
#        assert fixt_en[k] == v


def test_data_is_read_only(fixt_en):
    """LocaleData should be read-only at all levels of nesting."""

    with pytest.raises(TypeError):
        fixt_en["positive_symbol_before"] = "some_value"

    with pytest.raises(TypeError):
        fixt_en["currency_symbols"]["USD"] = "some_value"


def test_currency_symbols_keys_casing():
    """The keys for the `currency_symbols` dictionary should be
    case-insensitive."""

    en = lm.data.locale("en", "us", currency_symbols={"usd": "$"})
    assert "USD" in en.data["currency_symbols"]
    assert "usd" not in en.data["currency_symbols"]


def test_with_formatting_overrides(fixt_formatting_standard):
    r"""Passing in \*\*overrides keyword arguments should result in the created
    LocaleData having the supplied vaues for the corresponding keys."""

    en = lm.data.locale("en", "us", positive_sign="some_random_positive_sign")
    en_dict = helpers.map_to_dict(en.data)
    for k, v in fixt_formatting_standard["en_US"].items():
        if k == "positive_sign":
            assert en_dict[k] == "some_random_positive_sign"
        else:
            assert en_dict[k] == v


def test_currency_symbols_overrides_non_destructive(fixt_formatting_standard):
    """If `currency_symbols` is passed in, it should not completely override the
    `currency_symbols` dict in the resulting locale data, but will
    instead override the individual values for each of its keys, so the
    resulting locale data should retain the default value for any keys
    that the passed in `currency_symbols` does not provide."""

    en = lm.data.locale("en", "us", currency_symbols={"USD": "USD", "GIL": "GIL"})
    en_dict = helpers.map_to_dict(en.data)
    for k, v in fixt_formatting_standard["en_US"].items():
        if k == "currency_symbols":
            assert en_dict[k]["GIL"] == "GIL"

            for i in v.keys():
                if i == "USD":
                    assert en_dict[k][i] == "USD"
                else:
                    assert en_dict[k][i] == v[i]
        else:
            assert en_dict[k] == v


@parametrize_cases(
    Case("lowercase_language_and_region", language="en", region="us"),
    Case("uppercase_language_and_region", language="EN", region="US"),
    Case("mixedcase_language_and_region", language="En", region="uS"),
    Case(
        "uppercase_language_and_lowercase_region",
        language="EN",
        region="us",
    ),
    Case(
        "lowercase_language_and_uppercase_region",
        language="en",
        region="US",
    ),
)
def test_language_and_region_casing(language, region, fixt_formatting_standard):
    """The `language` and `region` arguments should be case insensitive."""

    default = fixt_formatting_standard["en_US"]
    en = lm.data.locale(language, region)
    en_dict = helpers.map_to_dict(en.data)
    assert en_dict == default


def test_regression_overrides_do_not_affect_fallback_formatting(
    fixt_formatting_standard,
):
    """Creating a Locale with override for a nested dict formatting key was
    overwriting the fallback formatting data which is supposed to remain
    constant for the life of the application."""

    default = fixt_formatting_standard["en_US"]
    overwrite = lm.data.locale(
        "en",
        "us",
        nformat=lm.data.FormatType.STANDARD,
        currency_symbols={"USD": "OVERWRITTEN"},
    )
    overwrite_dict = helpers.map_to_dict(overwrite.data)
    en = lm.data.locale("en", "us", nformat=lm.data.FormatType.STANDARD)
    en_dict = helpers.map_to_dict(en.data)
    assert en_dict["currency_symbols"] != overwrite_dict["currency_symbols"]
    assert en_dict["currency_symbols"] == default["currency_symbols"]


@parametrize_cases(
    Case(
        "standard",
        nformat=lm.data.FormatType.STANDARD,
        fallback_data=lf("fixt_formatting_standard"),
    ),
    Case(
        "accounting",
        nformat=lm.data.FormatType.ACCOUNTING,
        fallback_data=lf("fixt_formatting_accounting"),
    ),
)
def test_with_nformat(fallback_data, nformat):
    """The `locale` function should use either the 'standard' or 'accounting'
    formatting from the Unicode CLDR data based on the value of the
    `nformat` argument."""

    en = lm.data.locale("en", "us", nformat=nformat)
    en_dict = helpers.map_to_dict(en.data)
    for k, v in fallback_data["en_US"].items():
        assert en_dict[k] == v

    with pytest.raises(ValueError):
        lm.data.locale("en", "us", nformat="not_standard_or_accounting")


@parametrize_cases(
    Case(
        "custom_language_string",
        language="some_bogus_language_string",
        region="US",
    ),
    Case(
        "custom_region_string",
        language="en",
        region="some_bogus_region_string",
    ),
    Case(
        "custom_language_and_region_strings",
        language="some_bogus_language_string",
        region="some_bogus_region_string",
    ),
)
def test_with_custom_language_or_region(language, region):
    """The `locale` function does not allow defining arbitrary locales
    since it does not have any way to determine the correct locale data, so passing
    in a `language` or `region` that does not exist in the cldr formatting
    data should result in an exception."""

    with pytest.raises(UnknownDataError):
        lm.data.locale(language, region)


def test_system_locale_basic_usage():
    """Ensure the `system_locale` gives the locale of the running Python process."""

    system_locale_string = posix_locale.getlocale()[0]
    if system_locale_string.upper() == "C" or system_locale_string.upper() == "POSIX":
        system_locale_string = "en_US"
    assert system_locale_string == lm.data.system_locale().tag


def test_system_locale_after_update():
    """Ensure the `system_locale` gives the correct locale
    if the POSIX locale is updated using the stdlib."""

    system_locale_string = posix_locale.getlocale()[0]

    if system_locale_string == "ja_JP":
        posix_locale.setlocale(posix_locale.LC_ALL, "en_US.UTF-8")
        assert lm.data.system_locale().tag == "en_US"
    else:
        posix_locale.setlocale(posix_locale.LC_ALL, "ja_JP.UTF-8")
        assert lm.data.system_locale().tag == "ja_JP"


def test_system_locale_c_locale():
    """The default "C" or "POSIX" locale should be interpreted as "en_US"
    by the `system_locale` function."""

    posix_locale.setlocale(posix_locale.LC_ALL, "C.UTF-8")
    assert lm.data.system_locale().tag == "en_US"
