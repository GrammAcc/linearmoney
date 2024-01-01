# Quickstart Tutorial


In this quick start guide, we'll make a simple commandline currency converter.
Knowledge of commandline applications is not required to complete 
this tutorial. However, a basic understanding of Python and running Python 
scripts is assumed. It should take about 30 minutes to complete.

By the end of this tutorial, you should know how to:

- Parse and utilize foreign exchange rates, localization, and rounding data for currency conversions and formatting.
- Create money vectors and use them in calculations.
- Display money to a user in a localized format.


Let's get started!

## Installation

This tutorial does not use any dependencies outside the standard library other than
`linearmoney`.

```bash
pip install linearmoney
```

## Boilerplate

Add (or just copy and paste) the following code to a new file called `converter.py`:

```python
#!/usr/bin/python

"""Interactive commandline script for converting currencies.

Converts <amount> of <from_currency> to <to_currency>

Usage: [-h|--help] <amount> <from_currency> <to_currency>
"""

if __name__ != "__main__":
    raise ImportError("This is a standalone script and should not be imported.")

while True:
    readline = input("Currency Converter--> ")
```

Since we intend for this to be an interactive commandline app, we don't want the
code to execute when imported, so we raise an `ImportError` immediately if it is
not running directly from the commandline.

The infinite loop at the end creates our interactive command prompt with the builtin
[`input`](https://docs.python.org/3/library/functions.html#input) function.
If you've never built a commandline app before, this infinite loop might have you concerned, but this
is a very simple way to emulate a custom command prompt.
We're using the `input` builtin to provide a prompt and store whatever string that the user
inputs on the commandline into the `readline` variable. We aren't doing anything with this
user input yet, but this is the basic structure of our application. Ctrl+C can be used
to exit the infinite loop.

The docstring outlines what we expect the app to do. We pass in a numeric amount, a
currency to convert from, and a currency to convert to, and it converts the value
for us, so let's implement that.


## Converting Currencies

First off, we'll add `linearmoney` to our imports at the top of the file:

```python

...

if __name__ != "__main__":
    raise ImportError("This is a standalone script and should not be imported.")

import linearmoney as lm

while True:
    readline = input("Currency Converter--> ")
```

Next, if we are going to convert currencies, we'll need exchange rates. *linearmoney*
provides a helpful [`forex`](api_reference/linearmoney/vector.html#forex)
function for coercing a dictionary of exchange rates into a vector that can be
used by the conversion functions, but we still need to get rates from somewhere.

In this case, I'm using the awesome
[https://theforexapi.com](https://theforexapi.com), which is a free public web API for forex rates:

```python

import time
import urllib.request
import json

import linearmoney as lm

def request_rates() -> dict:
    """Request the latest rates from theforexapi.com and
    return them as a dict."""

    print("Fetching latest forex rates from theforexapi.com...")
    print("Waiting 2 seconds to comply with api rate limits...")
    time.sleep(2)  # Respect API rate limits.
    url = "https://theforexapi.com/api/latest"
    with urllib.request.urlopen(url) as response:
        rate_dict = json.loads(response.read().decode("utf-8"))
        return rate_dict
```

If you haven't made HTTP requests with Python before, don't worry about understanding this code.
The `request_rates` function just uses the standard library's
[`urllib.request`](https://docs.python.org/3/library/urllib.request.html#module-urllib.request)
to fetch the latest exchange rates from *theforexapi* and returns them as a Python dictionary.

We also wait two seconds before making the request to avoid violating the APIs soft
rate limits due to a programming oversight such as accidentally calling this function
in a loop.

This dictionary is of a particular structure that is common among web APIs for forex rates.
It includes a `base` key that indicates the base currency of each exchange rate pair, and
then a `rates` key, which is another nested Dictionary where each key is the quote
currency, and the value is the rate from the base currency to the quote currency.

The `forex` function accepts this structure of Dictionary
directly, so we can simply pass the result of the `request_rates` function into the
`forex` function to get a
[`ForexVector`](api_reference/linearmoney/vector.html#ForexVector) that we can use
to convert currencies in our script:

```python
forex_vector = lm.vector.forex(request_rates())
currency_space = lm.vector.space(forex_vector)
```

`ForexVectors` represent a specific set of exchange rates in a structure understood
internally by *linearmoney* and are not intended to be used in
calculations directly.

The `currency_space` is another key part of the linearmoney math model. In mathematical
terms, it defines the vector space of all monetary calculations, but in practical
terms, it's basically a strict definition of the *allowed* currencies for a calculation.
We will see how this is used and enforced later on, but for now we just need to know
that it is using the forex rates we fetched from `theforexapi` to determine which currencies
we can calculate/convert.

### Commandline Arguments

Just like a single-run commandline script, we'll treat user input as a set of
arguments, so we need to process the string that the user provides in our while loop.

Since our script is supposed to convert an amount of one currency to
another, we need three arguments:

1. The numeric amount to convert.
2. The currency code of the currency we are converting *from*.
3. The currency code of the currency we are converting *to*.

```python
while True:
    readline = input("Currency Converter--> ")
    raw_args = readline.split()  # [<amount>, <from_currency>, <to_currency>]
    print(f"amount: {raw_args[0]}")
    print(f"from_currency: {raw_args[1]}")
    print(f"to_currency: {raw_args[2]}")
``` 

This is the most basic way to parse the arguments for our currency converter.
Now let's use them to actually convert the amount:

```python
while True:
    readline = input("Currency Converter--> ")
    raw_args = readline.split()  # [<amount>, <from_currency>, <to_currency>]
    asset_vector = lm.vector.asset(raw_args[0], raw_args[1], currency_space)
    converted_value = lm.vector.evaluate(
        asset_vector, raw_args[2], forex_vector
    )
    to_currency = lm.data.currency(raw_args[2])
    result = lm.scalar.l10n(converted_value, to_currency, system_locale)
    print(result)
```

Let's break down the above code.

```python
    asset_vector = lm.vector.asset(raw_args[0], raw_args[1], currency_space)
```

The `asset_vector` uses the
[`asset`](api_reference/linearmoney/vector.html#asset) function
to create a new vector representing the monetary amount of the `amount` argument
in the currency `<from_currency>`.

Notice the use of the `currency_space` that we defined earlier. The `asset` function
requires us to provide a currency space when creating a vector in order to ensure
that any calculations with other vectors are in the same currency space. For example, if
we create another asset using a different currency space and then we try to add the two
different assets together, we will get a
[`SpaceError`](api_reference/linearmoney/exceptions.html#SpaceError), and the
same would happen if we tried to [*evaluate*](glossary.md#evaluation)
the asset vector we created using a forex vector that was in a different currency space.
Since we created our `currency_space` from our `forex_vector`, we can ensure that any math
required to *evaluate* the asset we create will work correctly by creating the
asset in the same currency space.

```python
    converted_value = lm.vector.evaluate(
        asset_vector, raw_args[2], forex_vector
    )
```

The call to [`evaluate`](api_reference/linearmoney/vector.html#evaluate)
converts the total value of the asset vector to the currency defined by `<to_currency>`
using the exchange rates in `forex_vector`. This function returns a
[`decimal.Decimal`](https://docs.python.org/3/library/decimal.html#decimal.Decimal), not
another asset vector. For the remainder of this tutorial, we
will refer to this as *evaluation*, not *conversion*. See also
[*Evaluation*](glossary.md#evaluation) and
[*Conversion*](glossary.md#conversion).

In this case, our asset vector was just created and only has one component in one
currency, so it doesn't really matter, but the `evaluate` function will give the total
value of the entire asset in the target currency even if our asset vector contained
values in multiple currencies, so this allows us to program more complex applications
in a way where we don't have to worry about what currency a monetary amount is in, we
just call `evaluate` to get the value in the currency we want at that point in
time, and it Just Works &trade;. The same goes for *converting* assets with
[`convert`](api_reference/linearmoney/vector.html#convert).

```python
    to_currency = lm.data.currency(raw_args[2])
    result = lm.scalar.l10n(converted_value, to_currency, system_locale)
    print(result)
```

The [`l10n`](api_reference/linearmoney/scalar.html#l10n)
function formats a decimal using the correct rounding for the provided currency
and the local currency representation for the provided locale. Both the locale
and the currency are [*Datasources*](glossary.md#datasource), and we have
to construct them using the corresponding factory functions.

The [`currency`](api_reference/linearmoney/data.html#currency)
function takes an ISO 4217 currency code (e.g. "USD") and returns the rounding data for the
corresponding currency, so we call it with the `<to_currency>` in order to get the
correct rounding data for our `converted_amount` before formatting with the current
system locale.

The `system_locale` variable used here has not been defined yet, but it's also not
dependent on the user's input, so we can define it at the script-level.

We'll use the standard library's
[`locale`](https://docs.python.org/3/library/locale.html)
module to get the locale of the running
machine and set the locale of the running Python process if it hasn't already been set:

```python
if __name__ != "__main__":
    raise ImportError("This is a standalone script and should not be imported.")

import time
import urllib.request
import json
import locale as posix_locale

import linearmoney as lm

if None in posix_locale.getlocale(posix_locale.LC_MONETARY):
    # Set the locale of the python session to the system locale.
    posix_locale.setlocale(posix_locale.LC_ALL, "")

system_locale_string: str | None = posix_locale.getlocale()[0]
assert (
    system_locale_string is not None
), "We init the system locale above, so it should not be None."
language, region = system_locale_string.split("_")

system_locale = lm.data.locale(language, region)
```

We import the stdlib `locale` module as `posix_locale` to avoid any
potential name collisions, and we use it to set the locale for the current
Python process to the locale of the running system only if it has not already been set.

The stdlib `locale` module is a bit tricky to work with
(this is one of the reasons *linearmoney* has its own locale system), and we generally
don't want to set the locale if another module has already set the locale for this
Python process, so we only set the locale to the system locale if the current
locale for the Python process is `None`.

The `assert` statement is just to make static type checkers happy since the stdlib
[`locale.getlocale()`](https://docs.python.org/3/library/locale.html#locale.getlocale)
function returns a two-element sequence of
`[language_code, encoding]`, but each element can be `None` if the correct
values cannot be determined. This will not happen since we explicitly set the
locale above this line, but static type checkers can't infer that, so we assert that
the variable is not `None` to make sure the next lines don't cause type checking errors.

The linearmoney [`locale`](api_reference/linearmoney/data.html#locale) function takes
a POSIX language and region tag (e.g. "en" and "us" for "en_US") and returns the
formatting data for that locale, so we just pass in the language and region we
obtained from the system locale, and we can then use this data for localizing
to the locale of the current user in our main loop.

All objects in *linearmoney* including datasources like the locale data
created by the [`locale`](api_reference/linearmoney/data.html#locale)
function are immutable, so we don't have to worry about passing around a
global reference to a complex data structure.

Now that we have the `system_locale` defined, we should have the following script:

```python
#!/usr/bin/python

"""Interactive commandline script for converting currencies.

Converts <amount> of <from_currency> to <to_currency>

Usage: [-h|--help] <amount> <from_currency> <to_currency>
"""

if __name__ != "__main__":
    raise ImportError("This is a standalone script and should not be imported.")

import time
import urllib.request
import json
import locale as posix_locale

import linearmoney as lm

if None in posix_locale.getlocale(posix_locale.LC_MONETARY):
    # Set the locale of the python session to the system locale.
    posix_locale.setlocale(posix_locale.LC_ALL, "")

system_locale_string: str | None = posix_locale.getlocale()[0]
assert (
    system_locale_string is not None
), "We init the system locale above, so it should not be None."
language, region = system_locale_string.split("_")

system_locale = lm.data.locale(language, region)


def request_rates() -> dict:
    """Request the latest rates from theforexapi.com and
    return them as a dict."""

    print("Fetching latest forex rates from theforexapi.com...")
    print("Waiting 2 seconds to comply with api rate limits...")
    time.sleep(2)  # Respect API rate limits.
    url = "https://theforexapi.com/api/latest"
    with urllib.request.urlopen(url) as response:
        rate_dict = json.loads(response.read().decode("utf-8"))
        return rate_dict


forex_vector = lm.vector.forex(request_rates())
currency_space = lm.vector.space(forex_vector)

while True:
    readline = input("Currency Converter--> ")
    raw_args = readline.split()  # [<amount>, <from_currency>, <to_currency>]
    asset_vector = lm.vector.asset(raw_args[0], raw_args[1], currency_space)
    converted_value = lm.vector.evaluate(
        asset_vector, raw_args[2], forex_vector
    )
    to_currency = lm.data.currency(raw_args[2])
    result = lm.scalar.l10n(converted_value, to_currency, system_locale)
    print(result)
```

If we run this with `python converter.py`, then we should see a couple of print
statements about fetching forex rates and then the prompt
`Currency Converter--> ` should come up.

If we enter something like `10 usd jpy` into this prompt and press enter, then
we should see the converted and formatted amount printed out.

Assuming the above is working correctly, we now have a working commandline currency
converter, but there is a problem; we have no error handling.
If we enter something like: `"bad argument values"`, then our app crashes with a
weird exception about `ARGUMENT` not being a part of currency space.

Since this is a REPL-like commandline app, we don't want it to crash when we get an
exception, and ideally, we would also have some helpful feedback if the user provides
invalid input.

Enter the standard library's
[`argparse`](https://docs.python.org/3/library/argparse.html) module.

### Argparse

Python's `argparse` module can be overwhelming if you've never used it
before, so you don't need to understand all of the code in this section.
All of the relevant objects and methods will be explained.

To start with, we'll import the `argparse` module and create an `ArgumentParser`:

```python
if __name__ != "__main__":

    raise ImportError("This is a standalone script and should not be imported.")

import argparse
import time
import urllib.request
import json
import locale as posix_locale

import linearmoney as lm

# system_locale and request_rates setup

forex_vector = lm.vector.forex(request_rates())
currency_space = lm.vector.space(forex_vector)

parser = argparse.ArgumentParser(
    prog="Currency Converter-->",
    description="Convert <amount> of <from_currency> to <to_currency>",
    epilog="Use ctrl+c to exit/quit.",
)
```

The `ArgumentParser` instance will be used to read the user input and validate it
as arguments while providing a standard help/man page for our commandline app.

The `prog` argument is what will be displayed in the help/man page as the invocation
for the usage examples. We set it to the text of our custom prompt to make the
examples in the generated help match the interactive prompt.

The `description` is like the first line of a Python docstring and gives a basic
summary of the app.

The `epilog` is an optional string that will be displayed after the rest of the generated
help/man page. Since we don't have an explicit exit command that will be
documented, we give an explanation of how to exit the application here.

### Parsing Args

Now that we have an `ArgumentParser` instance, we can define our three arguments:

```python
parser = argparse.ArgumentParser(
    prog="Currency Converter-->",
    description="Convert <amount> of <from_currency> to <to_currency>",
    epilog="Use ctrl+c to exit/quit.",
)

parser.add_argument(
    "amount",
    metavar="<amount>",
    help="""The monetary value to convert from one currency to another.
    Must be convertable to Python's decimal.Decimal type. E.g. 100, 100.0,
    1E+2, etc...""",
)

parser.add_argument(
    "from_currency",
    metavar="<from_currency>",
    help=f"""The case-insensitive ISO 4217 aplphabetic currency code
    of the <amount>. Accepted values: {currency_space.axes}.""",
)

parser.add_argument(
    "to_currency",
    metavar="<to_currency>",
    help=f"""The case-insensitive ISO 4217 alphabetic currency code
    to convert the <amount> to. Accepted values: {currency_space.axes}.""",
)
```

The `ArgumentParser.add_argument` method adds the metadata for an argument with
optional help text to the parser.

The `metavar` is how the argument will be displayed in usage examples in the
generated help/man page.

With the metadata for our commandline arguments added to the parser, we can now update
our while loop to use the parser instead of a simple list for our arguments:

```python
while True:
    readline = input("Currency Converter--> ")
    raw_args = readline.split()
    try:
        args = parser.parse_args(raw_args)
    except SystemExit:
        # We want to show the error, but not kill the interactive prompt.
        pass
    else:
        asset_vector = lm.vector.asset(args.amount, args.from_currency, currency_space)
        converted_value = lm.vector.evaluate(
            asset_vector, args.to_currency, forex_vector
        )
        to_currency = lm.data.currency(args.to_currency)
        result = lm.scalar.l10n(converted_value, to_currency, system_locale)
        print(result)
```

The `ArgumentParser.parse_args` method normally parses the arguments passed to the
script on the commandline, but since we are parsing args in a loop, we can pass
in the list of strings from the user input directly to the `parse_args` method, and
it will parse them as if they were passed directly to the script.

The standard behavior of a commandline app is to send an interrupt when
something goes wrong, which will cause the script to exit and dump some kind of
output, but we are running an interactive prompt, so we don't want our script to exit
when it runs into an error, so we catch the `SystemExit` exception, which should be
thrown by the `ArgumentParser` when it wants to indicate an exit interrupt should
be sent.

The members of `args` are the named arguments we defined with each call to `add_argument`
previously, so we can access them by name.

At this point, our `converter.py` should look like this:

```python
#!/usr/bin/python

"""Interactive commandline script for converting currencies.

Converts <amount> of <from_currency> to <to_currency>

Usage: [-h|--help] <amount> <from_currency> <to_currency>
"""

if __name__ != "__main__":
    raise ImportError("This is a standalone script and should not be imported.")

import argparse
import time
import urllib.request
import json
import locale as posix_locale

import linearmoney as lm

if None in posix_locale.getlocale(posix_locale.LC_MONETARY):
    # Set the locale of the python session to the system locale.
    posix_locale.setlocale(posix_locale.LC_ALL, "")

system_locale_string: str | None = posix_locale.getlocale()[0]
assert (
    system_locale_string is not None
), "We init the system locale above, so it should not be None."
language, region = system_locale_string.split("_")

system_locale = lm.data.locale(language, region)


def request_rates() -> dict:
    """Request the latest rates from theforexapi.com and
    return them as a dict."""

    print("Fetching latest forex rates from theforexapi.com...")
    print("Waiting 2 seconds to comply with api rate limits...")
    time.sleep(2)  # Respect API rate limits.
    url = "https://theforexapi.com/api/latest"
    with urllib.request.urlopen(url) as response:
        rate_dict = json.loads(response.read().decode("utf-8"))
        return rate_dict


forex_vector = lm.vector.forex(request_rates())
currency_space = lm.vector.space(forex_vector)

parser = argparse.ArgumentParser(
    prog="Currency Converter-->",
    description="Convert <amount> of <from_currency> to <to_currency>",
    epilog="Use ctrl+c to exit/quit.",
)

parser.add_argument(
    "amount",
    metavar="<amount>",
    help="""The monetary value to convert from one currency to another.
    Must be convertable to Python's decimal.Decimal type. E.g. 100, 100.0,
    1E+2, etc...""",
)

parser.add_argument(
    "from_currency",
    metavar="<from_currency>",
    help=f"""The case-insensitive ISO 4217 aplphabetic currency code
    of the <amount>. Accepted values: {currency_space.axes}.""",
)

parser.add_argument(
    "to_currency",
    metavar="<to_currency>",
    help=f"""The case-insensitive ISO 4217 alphabetic currency code
    to convert the <amount> to. Accepted values: {currency_space.axes}.""",
)
while True:
    readline = input("Currency Converter--> ")
    raw_args = readline.split()
    try:
        args = parser.parse_args(raw_args)
    except SystemExit:
        # We want to show the error, but not kill the interactive prompt.
        pass
    else:
        asset_vector = lm.vector.asset(args.amount, args.from_currency, currency_space)
        converted_value = lm.vector.evaluate(
            asset_vector, args.to_currency, forex_vector
        )
        to_currency = lm.data.currency(args.to_currency)
        result = lm.scalar.l10n(converted_value, to_currency, system_locale)
        print(result)
```

If we try running it as is, we can access the generated help/man page with the `-h` option
flag, and we see that our app does not exit, even though the generated help says
"show this help message and exit".

The `-h` option flag prints the generated help text and sends the `SystemExit`
exception, so our generated help doesn't quite match the behavior of our
interactive prompt, but changing this is outside the scope of this
tutorial, so we'll just ignore that minor inconsistency.

Unfortunately, we still haven't provided any error handling, and if we give our
script our `"bad argument values"`, it still crashes just like before.

Let's fix that.

### Error handling

The `add_argument` method can take an optional `type` argument that is used when
parsing arguments to coerce the type of the argument from the `str` that is provided
on the commandline to the appropriate runtime type. The value of the `type` argument
should therefore be a callable that takes in a string and returns a value of the
desired type.

Let's start with the `<amount>` argument:

```python
# imports
import decimal

parser.add_argument(
    "amount",
    metavar="<amount>",
    type=decimal.Decimal,
    help="""The monetary value to convert from one currency to another.
    Must be convertable to Python's decimal.Decimal type. E.g. 100, 100.0,
    1E+2, etc...""",
)
```

We set the `type` to `decimal.Decimal` since that is a valid type for our `asset`
function's `amount` argument that does not lose any information. E.g. we don't
want to use something like `int` as that would destroy any sub-currency amounts we
provide.

If we make this change and then pass in our `"bad argument values"`, we'll see that
the error has changed to `decimal.InvalidOperation`. This is because instead of simply
exposing the value as-is in `args`, the `ArgumentParser.parse_args` method first calls
the `decimal.Decimal` constructor with the value of the `<amount>` argument, which
results in an exception since `"bad"` can't be converted to a decimal.

What we want is to turn this exception into a `SystemExit` if we can't convert the
`<amount>` to a decimal, but we also want some kind of feedback to be printed out so
that the user knows that they provided an invalid value, so let's write a function
that we can provide as the `type` argument for `<amount>`:

```python

def _error_decimal(amount: str) -> decimal.Decimal:
    """Wrapper function that validates input as a decimal-compatible value."""

    try:
        return decimal.Decimal(amount)
    except decimal.InvalidOperation:
        raise argparse.ArgumentTypeError(f"Invalid numeric string '{amount}'")


parser = argparse.ArgumentParser(
    prog="Currency Converter-->",
    description="Convert <amount> of <from_currency> to <to_currency>",
    epilog="Use ctrl+c to exit/quit.",
)

parser.add_argument(
    "amount",
    metavar="<amount>",
    type=_error_decimal,
    help="""The monetary value to convert from one currency to another.
    Must be convertable to Python's decimal.Decimal type. E.g. 100, 100.0,
    1E+2, etc...""",
)
```

The `_error_decimal` function raises `argparse.ArgumentTypeError`, which will result
in the `parse_args` method printing the error message we provide to the exception before
raising a `SystemExit` exception, so we will get both proper error feedback to the
user, and we will not break our interactive prompt with an uncaught exception.

This takes care of the first argument, but what about the other two?

The `<from_currency>` and `<to_currency>` arguments are actually strings, but they need
to be valid currency codes in our `currency_space`. Fortunately for us, the `add_argument`
method takes another optional argument `choices`, which should be a
`Sequence` of valid values for the argument.

We can use our `currency_space` to define the valid values to avoid hard-coding any
currencies in our application:

```python
parser.add_argument(
    "from_currency",
    metavar="<from_currency>",
    choices=currency_space.axes,
    help=f"""The case-insensitive ISO 4217 aplphabetic currency code
    of the <amount>. Accepted values: {currency_space.axes}.""",
)

parser.add_argument(
    "to_currency",
    metavar="<to_currency>",
    choices=currency_space.axes,
    help=f"""The case-insensitive ISO 4217 alphabetic currency code
    to convert the <amount> to. Accepted values: {currency_space.axes}.""",
)
```

The `axes` of our `currency_space` are of course the valid currency codes that we have
forex rates for, so now, if we rerun with these changes, we'll see that passing in bad
input for the `<from_currency>` or `<to_currency>` arguments, such as `"10 bad USD"` or
`"10 USD bad"` gives an appropriate error message and doesn't crash our prompt.

However, we have another problem. Now if we provide a lower-case currency code, it
is considered invalid input, even if the currency code is supported by our app.
This didn't happen when we were using the values directly because *linearmoney*
forces currency codes to upper case whenever
they are used as strings for convenience, but the `choices` option for `add_argument`
compares strings literally and never passes them into a *linearmoney* function if
they don't match. We can solve this by providing a `type` function to the
`<from_currency>` and `<to_currency>` arguments that forces the argument to upper-case:

```python
def _upper_code(currency_code: str) -> str:
    """Ensure the currency code is uppercase."""

    return currency_code.upper()


parser.add_argument(
    "from_currency",
    metavar="<from_currency>",
    type=_upper_code,
    choices=currency_space.axes,
    help=f"""The case-insensitive ISO 4217 aplphabetic currency code
    of the <amount>. Accepted values: {currency_space.axes}.""",
)

parser.add_argument(
    "to_currency",
    metavar="<to_currency>",
    type=_upper_code,
    choices=currency_space.axes,
    help=f"""The case-insensitive ISO 4217 alphabetic currency code
    to convert the <amount> to. Accepted values: {currency_space.axes}.""",
)
```

At this point, our `converter.py` script should be complete, and you should be able
to play around with it to convert different currencies and amounts as well as see
how it handles various invalid inputs.

## Complete Script

```python
#!/usr/bin/python

"""Interactive commandline script for converting currencies.

Converts <amount> of <from_currency> to <to_currency>

Usage: [-h|--help] <amount> <from_currency> <to_currency>
"""

if __name__ != "__main__":
    raise ImportError("This is a standalone script and should not be imported.")

import decimal
import argparse
import time
import urllib.request
import json
import locale as posix_locale

import linearmoney as lm

if None in posix_locale.getlocale(posix_locale.LC_MONETARY):
    # Set the locale of the python session to the system locale.
    posix_locale.setlocale(posix_locale.LC_ALL, "")

system_locale_string: str | None = posix_locale.getlocale()[0]
assert (
    system_locale_string is not None
), "We init the system locale above, so it should not be None."
language, region = system_locale_string.split("_")

system_locale = lm.data.locale(language, region)


def request_rates() -> dict:
    """Request the latest rates from theforexapi.com and
    return them as a dict."""

    print("Fetching latest forex rates from theforexapi.com...")
    print("Waiting 2 seconds to comply with api rate limits...")
    time.sleep(2)  # Respect API rate limits.
    url = "https://theforexapi.com/api/latest"
    with urllib.request.urlopen(url) as response:
        rate_dict = json.loads(response.read().decode("utf-8"))
        return rate_dict


forex_vector = lm.vector.forex(request_rates())
currency_space = lm.vector.space(forex_vector)


def _upper_code(currency_code: str) -> str:
    """Ensure the currency code is uppercase."""

    return currency_code.upper()


def _error_decimal(amount: str) -> decimal.Decimal:
    """Wrapper function that validates input as a decimal-compatible value."""

    try:
        return decimal.Decimal(amount)
    except decimal.InvalidOperation:
        raise argparse.ArgumentTypeError(f"Invalid numeric string '{amount}'")


parser = argparse.ArgumentParser(
    prog="Currency Converter-->",
    description="Convert <amount> of <from_currency> to <to_currency>",
    epilog="Use ctrl+c to exit/quit.",
)

parser.add_argument(
    "amount",
    metavar="<amount>",
    type=_error_decimal,
    help="""The monetary value to convert from one currency to another.
    Must be convertable to Python's decimal.Decimal type. E.g. 100, 100.0,
    1E+2, etc...""",
)

parser.add_argument(
    "from_currency",
    metavar="<from_currency>",
    type=_upper_code,
    choices=currency_space.axes,
    help=f"""The case-insensitive ISO 4217 aplphabetic currency code
    of the <amount>. Accepted values: {currency_space.axes}.""",
)

parser.add_argument(
    "to_currency",
    metavar="<to_currency>",
    type=_upper_code,
    choices=currency_space.axes,
    help=f"""The case-insensitive ISO 4217 alphabetic currency code
    to convert the <amount> to. Accepted values: {currency_space.axes}.""",
)

while True:
    readline = input("Currency Converter--> ")
    raw_args = readline.split()
    try:
        args = parser.parse_args(raw_args)
    except SystemExit:
        # We want to show the error, but not kill the interactive prompt.
        pass
    else:
        asset_vector = lm.vector.asset(args.amount, args.from_currency, currency_space)
        converted_value = lm.vector.evaluate(
            asset_vector, args.to_currency, forex_vector
        )
        to_currency = lm.data.currency(args.to_currency)
        result = lm.scalar.l10n(converted_value, to_currency, system_locale)
        print(result)
```

## Conclusion

In this tutorial, we learned how to use *linearmoney* to create forex and
asset vectors, evaluate/convert monetary amounts as a specific currency, and
format a numeric value using the local currency format.

These functions can do a lot more than this though. To get a better idea of how to
integrate linearmoney with an application, take a look at the api documentation for the
[`l10n`](api_reference/linearmoney/scalar.html#l10n),
[`currency`](api_reference/linearmoney/data.html#currency), and
[`locale`](api_reference/linearmoney/data.html#locale) functions and change the
output to display the currency in the international format, as a cash value, or using
a custom format of your own creation.

