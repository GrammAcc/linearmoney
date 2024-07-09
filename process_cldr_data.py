import functools
import json
import os
import unicodedata


def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")


def normalize_whitespace(char):
    return str(unicodedata.normalize("NFKD", char).encode("ascii", "ignore"))


def sort_dict(d: dict) -> dict:
    return {
        k: dict(sorted(v.items())) if isinstance(v, dict) else v
        for k, v in dict(sorted(d.items())).items()
    }


print("processing cldr data...")


_raw_currency_data: dict | None = None


def get_raw_currency_data() -> dict:
    """Returns the following structure:
    {
        "fractions": {
            "curr_code": {
                "_rounding": int,
                "_digits": int,
                "_cashRounding": int (optional),
                "_cashDigits": int (optional),
            },
            ...,
        },
        "region": {
            "county_code": [
                {
                    "curr_code": {
                        "_from": date_string,
                        "_to": date_string (optional) - indicates current circulation.
                    },
                    ...,
                },
                ...,
            ],
            ...,
        }
    }
    """
    global _raw_currency_data
    if _raw_currency_data is not None:
        return _raw_currency_data

    with open(
        "cldr-json/cldr-json/cldr-core/supplemental/currencyData.json", "r"
    ) as json_file:
        _raw_currency_data = json.load(json_file)["supplemental"]["currencyData"]
        return _raw_currency_data


_local_currency_tags: dict[str, str] | None = None


def get_local_currency_tags() -> dict[str, str]:
    global _local_currency_tags
    if _local_currency_tags is not None:
        return _local_currency_tags
    local_currencies = {}
    for country_code, tenders in get_raw_currency_data()["region"].items():
        for currencies in tenders:
            for curr_code, curr_status in currencies.items():
                if "_from" in curr_status and "_to" not in curr_status:
                    if country_code not in local_currencies:
                        local_currencies[country_code] = curr_code
    _local_currency_tags = dict(sorted(local_currencies.items()))
    return _local_currency_tags


_supported_currency_tags: list[str] | None = None


def get_supported_currency_tags() -> list[str]:
    global _supported_currency_tags
    if _supported_currency_tags is not None:
        return _supported_currency_tags
    supported_currencies = []
    for country_code, tenders in get_raw_currency_data()["region"].items():
        for currencies in tenders:
            for curr_code, curr_status in currencies.items():
                if "_from" in curr_status and "_to" not in curr_status:
                    if curr_code not in supported_currencies:
                        supported_currencies.append(curr_code.upper())
    _supported_currency_tags = sorted(supported_currencies)
    return _supported_currency_tags


def restructure_fractions_data(curr_data: dict, key: str) -> dict:
    output_dict = {}
    for k, v in curr_data[key].items():
        if k == "_rounding":
            output_dict["denomination"] = v
        elif k == "_digits":
            output_dict["places"] = v
        elif k == "_cashRounding":
            output_dict["cash_denomination"] = v
        elif k == "_cashDigits":
            output_dict["cash_places"] = v
    if "cash_denomination" not in output_dict:
        output_dict["cash_denomination"] = output_dict["denomination"]
    if "cash_places" not in output_dict:
        output_dict["cash_places"] = output_dict["places"]
    return output_dict


_parsed_currency_data: dict | None = None


def parse_currency_data() -> dict:
    global _parsed_currency_data
    if _parsed_currency_data is not None:
        return _parsed_currency_data
    raw_fractions_data = get_raw_currency_data()["fractions"]

    _currency_data = {}
    _currency_data["DEFAULT"] = restructure_fractions_data(
        raw_fractions_data, "DEFAULT"
    )
    for i in get_supported_currency_tags():
        if i in raw_fractions_data:
            _currency_data[i] = restructure_fractions_data(raw_fractions_data, i)
    for _data in _currency_data.values():
        for k, v in _data.items():
            _data[k] = int(v)
    _parsed_currency_data = sort_dict(_currency_data)
    return _parsed_currency_data


_locale_dirs: list[str] | None = None


def get_locale_dirs() -> list[str]:
    global _locale_dirs
    if _locale_dirs is not None:
        return _locale_dirs
    locale_dirs = []
    with os.scandir("cldr-json/cldr-json/cldr-numbers-modern/main") as dir_contents:
        for entry in dir_contents:
            if entry.is_dir():
                locale_dirs.append(entry.name)
    _locale_dirs = locale_dirs
    return locale_dirs


_raw_locale_data: dict | None = None


def get_raw_locale_data() -> dict:

    global _raw_locale_data
    if _raw_locale_data is not None:
        return _raw_locale_data

    locale_data = {}
    for locale_dir in get_locale_dirs():
        locale_dict = {}
        currencies = {}
        numbers = {}
        with open(
            "".join(
                [
                    "cldr-json/cldr-json/cldr-numbers-modern/main/",
                    locale_dir,
                    "/currencies.json",
                ]
            ),
            "r",
        ) as json_file:
            currencies = json.load(json_file)["main"][locale_dir]["numbers"][
                "currencies"
            ]

        with open(
            "".join(
                [
                    "cldr-json/cldr-json/cldr-numbers-modern/main/",
                    locale_dir,
                    "/numbers.json",
                ]
            ),
            "r",
        ) as json_file:
            numbers = json.load(json_file)["main"][locale_dir]["numbers"]
        default_number_system = numbers["defaultNumberingSystem"]

        format_symbols = {}
        patterns = {"standard": "", "accounting": ""}

        for key in numbers.keys():
            if key.startswith(
                "".join(["symbols-numberSystem-", default_number_system])
            ):
                format_symbols = numbers[key]
            elif key.startswith(
                "".join(["currencyFormats-numberSystem-", default_number_system])
            ):
                patterns["standard"] = numbers[key]["standard"]
                patterns["accounting"] = numbers[key]["accounting"]

        if not format_symbols or not patterns["standard"] or not patterns["accounting"]:
            # Incomplete locale data.
            print(locale_dir, " missing locale data")
            continue
        locale_dict["patterns"] = patterns
        locale_dict["format_symbols"] = format_symbols

        currency_symbols = {}
        for k, v in currencies.items():
            if "symbol" in v:
                currency_symbols[k.upper()] = v["symbol"]
            elif "symbol-alt-narrow" in v:
                currency_symbols[k.upper()] = v["symbol-alt-narrow"]
            else:
                currency_symbols[k.upper()] = k.upper()

        locale_dict["currency_symbols"] = currency_symbols

        locale_data[locale_dir] = locale_dict
    _raw_locale_data = locale_data
    return locale_data


_locale_strings: dict[str, str] | None = None


def get_locale_strings() -> dict[str, str]:
    global _locale_strings
    if _locale_strings is not None:
        return _locale_strings
    identities = {}
    for locale_dir in get_locale_dirs():
        with open(
            "".join(
                [
                    "cldr-json/cldr-json/cldr-numbers-modern/main/",
                    locale_dir,
                    "/currencies.json",
                ]
            ),
            "r",
        ) as json_file:
            identities[locale_dir] = json.load(json_file)["main"][locale_dir][
                "identity"
            ]

    with open(
        "cldr-json/cldr-json/cldr-core/supplemental/likelySubtags.json", "r"
    ) as json_file:
        dir_to_locale_mapping = json.load(json_file)["supplemental"]["likelySubtags"]

    locale_strings = {}
    for locale_dir in get_locale_dirs():
        identity = identities[locale_dir]
        if "language" not in identity:
            continue
        locale_string = ""
        if "territory" in identity:
            locale_string = "_".join([identity["language"], identity["territory"]])

        else:
            if locale_dir in dir_to_locale_mapping:
                new_string = dir_to_locale_mapping[locale_dir]
                split_string = new_string.split("-")
                language = split_string[0]
                # Teritory is last item in split.
                split_string.reverse()
                country = split_string[0]
                locale_string = "_".join([language, country])
            else:
                locale_string = locale_dir

        split_locale = locale_string.split("_")
        if len(split_locale) != 2:
            continue
        language = split_locale[0]
        country = split_locale[1]

        country_is_macroregion = False
        try:
            int(country)
            country_is_macroregion = True
        except:
            pass
        if country_is_macroregion:
            continue
        else:
            locale_strings[locale_dir] = locale_string
    _locale_strings = locale_strings
    return locale_strings


@functools.lru_cache
def parse_formatting_pattern(pattern: str) -> dict:
    parsed_data_dict: dict[str, int | tuple[int, ...]] = {}
    pattern_split = pattern.split(";")
    for sign in ["positive", "negative"]:
        parsed_pattern = remove_control_characters(pattern_split[0])
        if len(pattern_split) > 1:
            parsed_pattern = remove_control_characters(
                pattern_split[0 if sign == "positive" else 1]
            )

        symbol_placeholder = "¤"
        decimal_split = parsed_pattern.split(".")
        # A value of -1 for sign position means don't include the sign
        # in the formatted string, so we use this as default
        # for the positive sign. The negative sign should always
        # be shown unless the value is 0, which indicates parenthesis, so
        # We default to 1 for the negative sign.
        parsed_data_dict["positive_sign_position"] = -1
        parsed_data_dict["negative_sign_position"] = 1
        parsed_data_dict["_".join([sign, "symbol_space"])] = -1
        if parsed_pattern.startswith("(") and parsed_pattern.endswith(")"):
            parsed_data_dict["_".join([sign, "sign_position"])] = 0
            new_parsed_pattern = parsed_pattern.lstrip("(").rstrip(")")
            parsed_pattern = new_parsed_pattern
        if parsed_pattern.startswith("-"):
            parsed_data_dict["_".join([sign, "sign_position"])] = 1
            new_parsed_pattern = parsed_pattern.lstrip("-")
            if normalize_whitespace(new_parsed_pattern).startswith(
                normalize_whitespace(" ")
            ):
                parsed_data_dict["_".join([sign, "symbol_space"])] = 2
            parsed_pattern = new_parsed_pattern
        elif parsed_pattern.endswith("-"):
            parsed_data_dict["_".join([sign, "sign_position"])] = 2
            new_parsed_pattern = parsed_pattern.rstrip("-")
            if normalize_whitespace(new_parsed_pattern).endswith(
                normalize_whitespace(" ")
            ):
                parsed_data_dict["_".join([sign, "symbol_space"])] = 2
            parsed_pattern = new_parsed_pattern
        if parsed_pattern.startswith(symbol_placeholder):
            parsed_data_dict["_".join([sign, "symbol_before"])] = True
            if parsed_data_dict["_".join([sign, "symbol_space"])] == -1:
                if normalize_whitespace(parsed_pattern[1]) == normalize_whitespace(
                    normalize_whitespace(" ")
                ):
                    if parsed_pattern[2] == "-":
                        parsed_data_dict["_".join([sign, "sign_position"])] = 4
                        parsed_data_dict["_".join([sign, "symbol_space"])] = 2
                    else:
                        parsed_data_dict["_".join([sign, "symbol_space"])] = 1
                elif parsed_pattern[1] == "-":
                    parsed_data_dict["_".join([sign, "sign_position"])] = 4
                    if normalize_whitespace(parsed_pattern[2]) == normalize_whitespace(
                        " "
                    ):
                        parsed_data_dict["_".join([sign, "symbol_space"])] = 1
                else:
                    parsed_data_dict["_".join([sign, "symbol_space"])] = 0
        elif parsed_pattern.endswith(symbol_placeholder):
            parsed_data_dict["_".join([sign, "symbol_before"])] = False
            if parsed_data_dict["_".join([sign, "symbol_space"])] == -1:
                plen = len(parsed_pattern)
                if normalize_whitespace(
                    parsed_pattern[plen - 2]
                ) == normalize_whitespace(" "):
                    if parsed_pattern[plen - 3] == "-":
                        parsed_data_dict["_".join([sign, "sign_position"])] = 3
                        parsed_data_dict["_".join([sign, "symbol_space"])] = 2
                    else:
                        parsed_data_dict["_".join([sign, "symbol_space"])] = 1
                elif parsed_pattern[plen - 2] == "-":
                    parsed_data_dict["_".join([sign, "sign_position"])] = 3
                    if normalize_whitespace(
                        parsed_pattern[plen - 3]
                    ) == normalize_whitespace(" "):
                        parsed_data_dict["_".join([sign, "symbol_space"])] = 1
                else:
                    parsed_data_dict["_".join([sign, "symbol_space"])] = 0
        group_split = decimal_split[0].split(",")
        if len(group_split) > 1:
            grouping_list = []
            for grouping in group_split:
                if len(grouping) > 1:
                    should_append = True
                    for char in grouping:
                        if char != "#" and char != "0":
                            should_append = False
                    if should_append:
                        grouping_list.append(len(grouping))
            parsed_data_dict["_".join([sign, "grouping"])] = tuple(grouping_list)
        else:
            parsed_data_dict["_".join([sign, "grouping"])] = (-1,)
    return parsed_data_dict


_parsed_locale_data: dict[str, dict] | None = None


def parse_locale_data() -> dict[str, dict]:
    global _parsed_locale_data
    if _parsed_locale_data is not None:
        return _parsed_locale_data

    def sort_formatting_dict(formatting_dict):
        return sort_dict({k: sort_dict(v) for k, v in formatting_dict.items()})

    accounting_data, standard_data = {}, {}

    for locale_dir, locale_string in get_locale_strings().items():
        locale_dict_standard = {}
        locale_dict_accounting = {}
        raw_locale_data = get_raw_locale_data()[locale_dir]
        language, region = locale_string.split("_")
        locale_dict_standard["local_currency_code"] = get_local_currency_tags()[region]
        locale_dict_accounting["local_currency_code"] = get_local_currency_tags()[
            region
        ]

        locale_dict_accounting["currency_symbols"] = raw_locale_data["currency_symbols"]
        locale_dict_standard["currency_symbols"] = raw_locale_data["currency_symbols"]

        locale_dict_accounting["decimal_separator"] = raw_locale_data["format_symbols"][
            "decimal"
        ]
        locale_dict_standard["decimal_separator"] = raw_locale_data["format_symbols"][
            "decimal"
        ]
        locale_dict_accounting["grouping_separator"] = raw_locale_data[
            "format_symbols"
        ]["group"]
        locale_dict_standard["grouping_separator"] = raw_locale_data["format_symbols"][
            "group"
        ]
        locale_dict_accounting["positive_sign"] = raw_locale_data["format_symbols"][
            "plusSign"
        ]
        locale_dict_standard["positive_sign"] = raw_locale_data["format_symbols"][
            "plusSign"
        ]
        locale_dict_accounting["negative_sign"] = raw_locale_data["format_symbols"][
            "minusSign"
        ]
        locale_dict_standard["negative_sign"] = raw_locale_data["format_symbols"][
            "minusSign"
        ]

        parsed_pattern_data_accounting = parse_formatting_pattern(
            raw_locale_data["patterns"]["accounting"]
        )
        parsed_pattern_data_standard = parse_formatting_pattern(
            raw_locale_data["patterns"]["standard"]
        )

        locale_dict_accounting.update(parsed_pattern_data_accounting)
        locale_dict_standard.update(parsed_pattern_data_standard)

        accounting_data[locale_string] = locale_dict_accounting
        standard_data[locale_string] = locale_dict_standard
    _parsed_locale_data = {
        "accounting": sort_formatting_dict(accounting_data),
        "standard": sort_formatting_dict(standard_data),
    }
    return _parsed_locale_data


with open("src/linearmoney/locales.json", "w") as json_file:
    json.dump(parse_locale_data(), json_file)

with open("src/linearmoney/currencies.json", "w") as json_file:
    json.dump(parse_currency_data(), json_file)


with open("src/linearmoney/supported_iso_codes.json", "w") as json_file:
    json.dump(sorted(get_supported_currency_tags()), json_file)

with open("cldr-json/cldr-json/cldr-core/package.json", "r") as file:
    data = json.load(file)
    CLDR_VERSION = data["version"]
    with open("src/linearmoney/cldr_version.json", "w") as json_file:
        json.dump(CLDR_VERSION, json_file)

print("successfully processed cldr data")
