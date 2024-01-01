# Useful Recipes

This document gives examples of patterns for solving common problems with the
linearmoney library that may not be obvious to a programmer who is not familiar with
all of the library's features.

---

## Reducing Verbosity with Partial Application

The linearmoney library has a functional/procedural API that makes all operations
explicit, which makes programs easier to read and test, but it is very verbose when
compared with more idiomatic OO Python, so some users may want to reduce this
verbosity where possible.

Partial application can help us here. Most explanations of partial application are
very confusing, but practically speaking, it just means that we bind
a specific value to a specific argument of a function and return a new function that
has the same signature without the bound argument. You can think of it like setting
a new default value for an argument and not allowing it to be changed from that point
forward.

The most obvious use of partial application for the linearmoney library is to eliminate
the need to provide a currency space whenever we create an Asset Vector. This is
generally safe for most applications since even if the forex rates change over
time, the currencies the application supports generally don't, but if the supported
currencies are determined dynamically, this technique should not be used.

Here's what it looks like:

```pycon
>>> import functools
>>> import linearmoney as lm
>>> fo = lm.vector.forex({"base": "usd", "rates": {}})
>>> sp = lm.vector.space(fo)
>>> mkasset = functools.partial(lm.vector.asset, currency_space=sp)

```

Now, we can just import `mkasset`, and use it like so:

```pycon
>>> mkasset(10, "usd")
MoneyVector('10',)

```

The `functools.partial` function takes a function and args/kwargs for that function
and binds the values provided to those args/kwargs, so the new `mkasset` function is
the same as calling `lm.vector.asset` with `currency_space=sp`, but we can't specify
the currency space.

This has advantages and drawbacks. On the one hand, it eliminates the possibility
of passing in the wrong currency space to an asset, which would result in vector
calculations between two different currency spaces at runtime, which is an exception.
On the other hand, it means that we can't specify the currency space for different
assets, so in more complex applications that need to deal with different sets of
currencies or dynamic currencies, this won't work.

One nice thing about FP as opposed to OOP is that we're working with immutable
types, so even if we use this pattern to simplify the creation of Asset Vectors
in the common case, we can still call the `lm.vector.asset` function directly
to get vectors in different currency spaces.

Also, if the requirements of our application are such that we need to support multiple
distinct currency spaces, we can use this pattern to create separate functions for
easily creating Asset Vectors in specific currency spaces without having to worry about
passing the actual currency space around:

```pycon
>>> fo_europe = lm.vector.forex({"base": "eur", "rates": {"gbp": 0.8, "usd": 0.4}})
>>> sp_europe = lm.vector.space(fo_europe)
>>> euasset = functools.partial(lm.vector.asset, currency_space=sp_europe)
>>> fo_asia = lm.vector.forex({"base": "jpy", "rates": {"cny": 0.05, "krw": 10, "inr": 0.5}})
>>> sp_asia = lm.vector.space(fo_asia)
>>> asiaasset = functools.partial(lm.vector.asset, currency_space=sp_asia)
>>> euasset(10, "usd")
MoneyVector('0', '0', '10')
>>> euasset(10, "usd") + euasset(10, "eur")
MoneyVector('10', '0', '10')
>>> asiaasset(100, "jpy")
MoneyVector('0', '0', '100', '0')
>>> asiaasset(100, "jpy") + asiaasset(100, "krw")
MoneyVector('0', '0', '100', '100')
>>> euasset(10, "usd") + asiaasset(100, "jpy")
Traceback (most recent call last):
    ...
linearmoney.exceptions.SpaceError: MoneyVectors must be in the same space.

```

This gives us good error handling when we mix currencies that violate our application
requirements with a lighter syntax at the callsite.

Because all of the data types returned by functions in the linearmoney library
are immutable, we can use partial application pretty much anywhere to create
semantic interfaces without complicated dependencies or internal state.

---

## Single-Currency Application

With most libraries/frameworks for working with money, multi-currency amounts are not
supported, so a monetary value is created like this:

```python
Money(10, "usd")
```

However, with linearymoney, multi-currency is built-in, so to create a strictly
single-currency application, we need to explicitly specify that
our application only supports one currency.

We do that by using a one-dimensional currency space.

The standard way to create a single-currency amount is:

```pycon
>>> import linearmoney as lm
>>> fo = lm.vector.forex({"base": "usd", "rates": {}})
>>> sp = lm.vector.space(fo)
>>> lm.vector.asset(10, "usd", sp)
MoneyVector('10',)

```

This is actually much safer and easier to work with in complex multi-currency
applications, but in the simple case where the application is single-currency and just
needs access to currency formatting and a simple `Money` type, this can be very
unpleasant to use.

See the [Reducing Verbosity](#reducing-verbosity-with-partial-application) section
for ideas on how to simplify this syntax for single-currency applications.

