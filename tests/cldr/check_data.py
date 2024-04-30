import json

cldr_version = ""
currencies = ""
locales = ""
supported_iso_codes = ""
new_cldr_version = ""
new_currencies = ""
new_locales = ""
new_supported_iso_codes = ""


with open("src/linearmoney/cldr_version.json", "r") as json_file:
    new_cldr_version = json.load(json_file)
with open("src/linearmoney/currencies.json", "r") as json_file:
    new_currencies = json.load(json_file)
with open("src/linearmoney/locales.json", "r") as json_file:
    new_locales = json.load(json_file)
with open("src/linearmoney/supported_iso_codes.json", "r") as json_file:
    new_supported_iso_codes = json.load(json_file)

with open("tests/cldr/cldr_version.json", "r") as json_file:
    cldr_version = json.load(json_file)
with open("tests/cldr/currencies.json", "r") as json_file:
    currencies = json.load(json_file)
with open("tests/cldr/locales.json", "r") as json_file:
    locales = json.load(json_file)
with open("tests/cldr/supported_iso_codes.json", "r") as json_file:
    supported_iso_codes = json.load(json_file)

try:
    assert new_cldr_version == cldr_version
except AssertionError:
    print("CLDR Version: Failed")
else:
    print("CLDR Version: Passed")
try:
    assert new_currencies == currencies
except AssertionError:
    print("Currencies: Failed")
else:
    print("Currencies: Passed")
try:
    assert new_locales == locales
except AssertionError:
    print("Locales: Failed")
else:
    print("Locales: Passed")
try:
    assert new_supported_iso_codes == supported_iso_codes
except AssertionError:
    print("Supported ISO Codes: Failed")
else:
    print("Supported ISO Codes: Passed")
