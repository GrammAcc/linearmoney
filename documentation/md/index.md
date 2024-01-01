# Welcome to the linearmoney library's documentation!

linearmoney is a library for working with multiple currencies that uses a
non-traditional model based on linear algebra to allow lossless currency conversion
and calculations with multiple currencies simultaneously.

Understanding of linear algebra is not required to use the linearmoney library, and the
library is designed in such a way that the same code can be used for single and
multi-currency calculations, so the programmer no longer has to worry about keeping
track of individual currencies, and in most cases, doesn't even need to know which
currency a particular value is in. This makes developing modern international
applications much simpler.

Currencies can be easily converted based on exchange rates, and full localization
support is built-in.

The linearmoney library uses a completely thread-safe functional/procedural style
that is verbose but very clear in its behavior with no mutable data or side effects.

This makes it ideal for other library/framework authors to use for core currency
functionalities while providing a higher level API for use by end-users, but
application developers can still use the library directly if they prefer as all of the
core functionalities of a monetary application are provided
(conversion, localization/formatting, rates/data management).

## Basic Usage

```bash
pip install linearmoney
```

```pycon
>>> import linearmoney as lm
>>> fo = lm.vector.forex({"base": "usd", "rates": {"jpy": 100}})
>>> sp = lm.vector.space(fo)
>>> cart = []
>>> milk_price = lm.vector.asset(4.32, 'usd', sp)
>>> cart.append(milk_price)
>>> eggs_price = lm.vector.asset(5.45, 'usd', sp)
>>> cart.append(eggs_price)
>>> sales_tax = 0.095
>>> subtotal = sum(cart)
>>> total = subtotal + (subtotal * sales_tax)
>>> total_usd = lm.vector.evaluate(total, "usd", fo)
>>> total_jpy = lm.vector.evaluate(total, "jpy", fo)
>>> usd = lm.data.currency("usd")
>>> jpy = lm.data.currency("jpy")
>>> en_US = lm.data.locale("en", "us")
>>> localized_total_usd = lm.scalar.l10n(total_usd, usd, en_US)
>>> localized_total_jpy = lm.scalar.l10n(total_jpy, jpy, en_US)
>>> print(localized_total_usd)
$10.70
>>> print(localized_total_jpy)
¥1,070

```
