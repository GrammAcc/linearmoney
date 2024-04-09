import json
import os
import unicodedata


def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")


currency_data = {}
currency_mapping = {}
locale_data = {}
temp_locales = {}
temp_currency_data = {}
temp_locale_data = {}
temp_locale_mappings = {}

locale_dirs = []
with os.scandir("cldr-json/cldr-json/cldr-numbers-modern/main") as dir_contents:
    for entry in dir_contents:
        if entry.is_dir():
            locale_dirs.append(entry.name)

with open(
    "cldr-json/cldr-json/cldr-core/supplemental/likelySubtags.json", "r"
) as json_file:
    temp_locale_mappings = json.load(json_file)["supplemental"]["likelySubtags"]


with open(
    "cldr-json/cldr-json/cldr-core/supplemental/currencyData.json", "r"
) as json_file:
    temp_currency_data = json.load(json_file)


for i in locale_dirs:
    temp_locale_data[i] = {}
    with open(
        "".join(
            ["cldr-json/cldr-json/cldr-numbers-modern/main/", i, "/currencies.json"]
        ),
        "r",
    ) as json_file:
        temp_locale_data[i]["currencies"] = json.load(json_file)

    with open(
        "".join(["cldr-json/cldr-json/cldr-numbers-modern/main/", i, "/numbers.json"]),
        "r",
    ) as json_file:
        temp_locale_data[i]["numbers"] = json.load(json_file)


temp_currency_regions = temp_currency_data["supplemental"]["currencyData"]["region"]
for i in temp_currency_regions.keys():
    for j in temp_currency_regions[i]:
        for k in j.keys():
            if "_from" in j[k] and not "_to" in j[k]:
                if not i in currency_mapping:
                    currency_mapping[i] = k
                if not k in currency_data:
                    currency_data[k] = {}


def _build_fractions_data(curr_data: dict, key: str) -> dict:
    output_dict = {}
    for i in curr_data[key]:
        if i == "_rounding":
            output_dict["denomination"] = curr_data[key][i]
        elif i == "_digits":
            output_dict["places"] = curr_data[key][i]
        elif i == "_cashRounding":
            output_dict["cash_denomination"] = curr_data[key][i]
        elif j == "_cashDigits":
            output_dict["cash_places"] = curr_data[key][i]
    if "cash_denomination" not in output_dict:
        output_dict["cash_denomination"] = output_dict["denomination"]
    if "cash_places" not in output_dict:
        output_dict["cash_places"] = output_dict["places"]
    return output_dict


new_currency_data = {}
temp_fractions = temp_currency_data["supplemental"]["currencyData"]["fractions"]
new_currency_data["DEFAULT"] = _build_fractions_data(temp_fractions, "DEFAULT")

supported_currencies = list(currency_data.keys())
# supported_currencies.append("COMPOSITE")

for i in currency_data.keys():
    if i in temp_fractions:
        new_currency_data[i] = _build_fractions_data(temp_fractions, i)

locale_data["fractions"] = new_currency_data

locale_data["accounting"] = {}
locale_data["standard"] = {}

for i in temp_locale_data.keys():
    identity = temp_locale_data[i]["currencies"]["main"][i]["identity"]

    if not "language" in identity:
        continue
    locale_string = ""
    if "territory" in identity:
        locale_string = "_".join([identity["language"], identity["territory"]])

    else:
        if i in temp_locale_mappings:
            new_string = temp_locale_mappings[i]
            split_string = new_string.split("-")
            language = split_string[0]
            split_string.reverse()
            country = split_string[0]
            locale_string = "_".join([language, country])
        else:
            locale_string = i

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

    locale_data["accounting"][locale_string] = {}
    locale_data["standard"][locale_string] = {}
    locale_data["accounting"][locale_string]["local_currency_code"] = currency_mapping[
        country
    ]
    locale_data["standard"][locale_string]["local_currency_code"] = currency_mapping[
        country
    ]
    number_data = temp_locale_data[i]["numbers"]["main"][i]["numbers"]
    default_number_system = number_data["defaultNumberingSystem"]
    currencies_data = temp_locale_data[i]["currencies"]["main"][i]["numbers"][
        "currencies"
    ]

    currency_symbols = {}
    for k, v in currencies_data.items():
        if "symbol" in v:
            currency_symbols[k.upper()] = v["symbol"]
        elif "symbol-alt-narrow" in v:
            currency_symbols[k.upper()] = v["symbol-alt-narrow"]
        else:
            currency_symbols[k.upper()] = k.upper()

    locale_data["accounting"][locale_string]["currency_symbols"] = currency_symbols
    locale_data["standard"][locale_string]["currency_symbols"] = currency_symbols

    for j in number_data.keys():
        if j.startswith("".join(["symbols-numberSystem-", default_number_system])):
            locale_data["accounting"][locale_string]["decimal_separator"] = number_data[
                j
            ]["decimal"]
            locale_data["standard"][locale_string]["decimal_separator"] = number_data[
                j
            ]["decimal"]
            locale_data["accounting"][locale_string]["grouping_separator"] = (
                number_data[j]["group"]
            )
            locale_data["standard"][locale_string]["grouping_separator"] = number_data[
                j
            ]["group"]
            locale_data["accounting"][locale_string]["positive_sign"] = number_data[j][
                "plusSign"
            ]
            locale_data["standard"][locale_string]["positive_sign"] = number_data[j][
                "plusSign"
            ]
            locale_data["accounting"][locale_string]["negative_sign"] = number_data[j][
                "minusSign"
            ]
            locale_data["standard"][locale_string]["negative_sign"] = number_data[j][
                "minusSign"
            ]
        elif j.startswith(
            "".join(["currencyFormats-numberSystem-", default_number_system])
        ):
            patterns = {
                "standard": number_data[j]["standard"],
                "accounting": number_data[j]["accounting"],
            }
            tmp_list = ["positive", "negative"]
            for i in patterns.keys():
                pattern_split = patterns[i].split(";")
                for j in tmp_list:
                    locale_dict = {}
                    pattern = remove_control_characters(pattern_split[0])
                    if len(pattern_split) > 1:
                        pattern = remove_control_characters(
                            pattern_split[tmp_list.index(j)]
                        )

                    elif j == "negative":
                        locale_dict["negative_symbol_before"] = locale_data[i][
                            locale_string
                        ]["positive_symbol_before"]
                        locale_dict["negative_symbol_space"] = locale_data[i][
                            locale_string
                        ]["positive_symbol_space"]
                        locale_dict["negative_grouping"] = locale_data[i][
                            locale_string
                        ]["positive_grouping"]
                        locale_dict["negative_sign_position"] = 1
                        locale_data[i][locale_string].update(locale_dict)
                        continue

                    symbol_placeholder = "¤"
                    decimal_split = pattern.split(".")
                    locale_dict["_".join([j, "sign_position"])] = -1
                    locale_dict["_".join([j, "symbol_space"])] = -1
                    if pattern.startswith("(") and pattern.endswith(")"):
                        locale_dict["_".join([j, "sign_position"])] = 0
                        new_pattern = pattern.lstrip("(").rstrip(")")
                        pattern = new_pattern
                    if pattern.startswith("-"):
                        locale_dict["_".join([j, "sign_position"])] = 1
                        new_pattern = pattern.lstrip("-")
                        if new_pattern.startswith(" "):
                            locale_dict["_".join([j, "symbol_space"])] = 2
                        pattern = new_pattern
                    elif pattern.endswith("-"):
                        locale_dict["_".join([j, "sign_position"])] = 2
                        new_pattern = pattern.rstrip("-")
                        if new_pattern.endswith(" "):
                            locale_dict["_".join([j, "symbol_space"])] = 2
                        pattern = new_pattern
                    if pattern.startswith(symbol_placeholder):
                        locale_dict["_".join([j, "symbol_before"])] = True
                        if locale_dict["_".join([j, "symbol_space"])] == -1:
                            if pattern[1] == " ":
                                if pattern[2] == "-":
                                    locale_dict["_".join([j, "sign_position"])] = 4
                                    locale_dict["_".join([j, "symbol_space"])] = 2
                                else:
                                    locale_dict["_".join([j, "symbol_space"])] = 1
                            elif pattern[1] == "-":
                                locale_dict["_".join([j, "sign_position"])] = 4
                                if pattern[2] == " ":
                                    locale_dict["_".join([j, "symbol_space"])] = 1
                            else:
                                locale_dict["_".join([j, "symbol_space"])] = 0
                    elif pattern.endswith(symbol_placeholder):
                        locale_dict["_".join([j, "symbol_before"])] = False
                        if locale_dict["_".join([j, "symbol_space"])] == -1:
                            plen = len(pattern)
                            if pattern[plen - 2] == " ":
                                if pattern[plen - 3] == "-":
                                    locale_dict["_".join([j, "sign_position"])] = 3
                                    locale_dict["_".join([j, "symbol_space"])] = 2
                                else:
                                    locale_dict["_".join([j, "symbol_space"])] = 1
                            elif pattern[plen - 2] == "-":
                                locale_dict["_".join([j, "sign_position"])] = 3
                                if pattern[plen - 3] == " ":
                                    locale_dict["_".join([j, "symbol_space"])] = 1
                            else:
                                locale_dict["_".join([j, "symbol_space"])] = 0
                    group_split = decimal_split[0].split(",")
                    if len(group_split) > 1:
                        grouping_list = []
                        for k in group_split:
                            if len(k) > 1:
                                should_append = True
                                for l in k:
                                    if l != "#" and l != "0":
                                        should_append = False
                                if should_append:
                                    grouping_list.append(len(k))
                        locale_dict["_".join([j, "grouping"])] = tuple(grouping_list)
                    else:
                        locale_dict["_".join([j, "grouping"])] = (-1,)

                    locale_data[i][locale_string].update(locale_dict)


def _sorted_dict(d: dict) -> dict:
    return {
        k: dict(sorted(v.items())) if isinstance(v, dict) else v
        for k, v in dict(sorted(d.items())).items()
    }


_sorted_l10n = lambda l10n: _sorted_dict({k: _sorted_dict(v) for k, v in l10n.items()})


def _build_fractions_data(fractions_dict: dict) -> dict:
    for i in fractions_dict.values():
        for k, v in i.items():
            i[k] = int(v)
    return _sorted_dict(fractions_dict)


_standard_formatting = _sorted_l10n(locale_data["standard"])
_accounting_formatting = _sorted_l10n(locale_data["accounting"])

_formatting_data = {
    "accounting": _accounting_formatting,
    "standard": _standard_formatting,
}

_fractions_data = _build_fractions_data(locale_data["fractions"])

with open("src/linearmoney/locales.json", "w") as json_file:
    json.dump(_formatting_data, json_file)


with open("src/linearmoney/currencies.json", "w") as json_file:
    json.dump(_fractions_data, json_file)

with open("src/linearmoney/supported_iso_codes.json", "w") as json_file:
    json.dump(sorted(supported_currencies), json_file)

with open("cldr-json/cldr-json/cldr-core/package.json", "r") as file:
    data = json.load(file)
    CLDR_VERSION = data["version"]
    with open("src/linearmoney/cldr_version.json", "w") as json_file:
        json.dump(CLDR_VERSION, json_file)
