# linearmoney

Full multi-currency support for python.

---

Quickstart Tutorial: https://grammacc.github.io/linearmoney/quickstart.html

Full Documentation: https://grammacc.github.io/linearmoney

License: [MIT](LICENSE)

This project uses [semantic versioning](https://semver.org). However, this
is a pre-release piece of software, so until the first stable release, minor versions
may contain breaking changes. Version 1.0.0 will mark the first stable release, at
which point the regular rules of semver will apply and backwards-incompatible changes
will only be introduced in major versions.

## Description

linearmoney was created to make calculations and formatting with multiple currencies
in modern international applications easier and more reliable.

Key Features:

- Full support for arithmetic with monetary amounts in different currencies.
- Full support for non-destructive currency conversion.
- Full support for fractional currency rounding and fixed-point rounding.
- Full support for currency formatting and localization.
- No dependencies other than Python itself.
- Completely thread-safe.
- 100% Test and API Documentation coverage.
- Database/ORM integrations.

The linearmoney library takes a non-traditional approach to financial applications
by using linear algebra internally to ensure the correctness of monetary calculations
involving multiple currencies without passing this burden onto the programmer.
Understanding of linear algebra is not needed to use and understand the linearmoney
library, but an understanding of basic arithmetic with vectors is helpful for
understanding how the library works under the hood.

For a technical explanation of the motivation and philosophy behind linearmoney
as well as the complete pure-math model that defines the behaviors of the library, see
the [Linear Money Model](https://grammacc.github.io/linearmoney/linear_money_model.html) article.

linearmoney uses the amazing [Unicode CLDR-JSON](https://github.com/unicode-org/cldr-json)
data to provide data-driven interfaces for currency rounding, formatting, and localization.

## Installation

linearmoney requires Python >= 3.10

From PyPi:

```bash
pip install linearmoney
```

From source:

```bash
git clone https://github.com/GrammAcc/linearmoney
cd linearmoney
python -m build .
```

Then to install (virtual environment recommended):

```bash
pip install path/to/cloned/repo
```

## Basic Usage

```pycon
>>> import linearmoney as lm
>>> fo = lm.vector.forex({"base": "usd", "rates": {"jpy": 100}})  # 1 USD -> 100 JPY
>>> sp = lm.vector.space(fo)
>>> cart = []
>>> local_milk_price = lm.vector.asset(4.32, "usd", sp)
>>> cart.append(local_milk_price)
>>> foreign_eggs_price = lm.vector.asset(545, "jpy", sp)
>>> cart.append(foreign_eggs_price)
>>> sales_tax = 0.095
>>> subtotal = sum(cart)
>>> total = subtotal + (subtotal * sales_tax)
>>> total_usd = lm.vector.evaluate(total, "usd", fo)
>>> total_jpy = lm.vector.evaluate(total, "jpy", fo)
>>> usd = lm.data.currency("usd")
>>> jpy = lm.data.currency("jpy")
>>> rounded_total_usd = lm.scalar.roundas(total_usd, usd)
>>> rounded_total_jpy = lm.scalar.roundas(total_jpy, jpy)
>>> en_US = lm.data.locale("en", "us")
>>> localized_total_usd = lm.scalar.l10n(rounded_total_usd, usd, en_US)
>>> localized_total_jpy = lm.scalar.l10n(rounded_total_jpy, jpy, en_US)
>>> print(localized_total_usd)
$10.70
>>> print(localized_total_jpy)
¥1,070

```

linearymoney uses a functional/procedural style where all objects are immutable, so
the code can become verbose compared to more idiomatic Python, but this also makes
the code more explicit and easier to test.

See the [Recipes](https://grammacc.github.io/linearmoney/recipes.html)
section of the user guide for
some examples of how to mitigate the verbosity of the library and other helpful patterns.

## Optional Extensions

The `linearmoney.ext` sub-package provides optional integrations with other libraries/tools.

Most tools shouldn't need any kind of adapter layer for you to use linearmoney with
them since you would normally evaluate a money vector whenever you need to do something
with its value outside of linearmoney's functions or math between vectors. The exceptions
to this are ORMs and similar tools that need some kind of serialization step to be
performed.

[SQLAlchemy](https://grammacc.github.io/linearmoney/api_reference/linearmoney/ext/sqlalchemy.html)
integrations are implemented, and Django ORM is planned.

If there is a tool that you want better integration with or simply some kind of
extra functionality that requires additional dependencies, please
[open an issue](https://github.com/GrammAcc/linearmoney/issues/new/choose) and
we will evaluate if it is within the scope of the project to support as an extension.

## Contributing

Contributions are greatly appreciated!

See the [contributing guidelines](/CONTRIBUTING.md) to get started.

## Roadmap

Version 1.0.0:
- [ ] Redesign locale/formatting data structure
  - [#15](https://github.com/GrammAcc/linearmoney/issues/15)
- [ ] Redesign caching system
- [ ] Higher-order serialization interface
  - [ ] Serialization/deserialization of forex vectors
- [ ] Recipes to add
  - [ ] Use-cases without vectors
- [x] Refactor CLDR data processing script
  - [#11](https://github.com/GrammAcc/linearmoney/issues/11)
- [x] Add contributing guidelines and setup CI
  - [x] Contributing guidelines
  - [x] CI workflow
