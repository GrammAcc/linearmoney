# Glossary of Terms


This is a quick reference for terms used throughout the linearmoney source and docs.
[documentation](index.md) and 
[source code](https://github.com/GrammAcc/linearmoney/).

---

## Money Vector

Used to refer to *any* vector used in linear money calculations. Includes both asset
and forex vectors.

---

## Asset Vector

An asset vector is a vector that represents a monetary amount in one or more currencies
simultaneously.

This is the closest thing to the traditional *Money* type in most currency frameworks.

Asset vectors should be constructed via the
[`asset`](api_reference/linearmoney/vector.html#asset) function of the
[`vector`](api_reference/linearmoney/vector.html) module.

This is simply a conceptual distinction. Technically, there is no `AssetVector`
type in the linearmoney library, and all *Asset Vectors* are actually of the
[`MoneyVector`](api_reference/linearmoney/vector.html#MoneyVector) type.

---

## Rudimentary Asset

An asset vector that contains a value for only one currency. In other words, all
components of the vector except for one are 0, and evaluating the asset is equivalent
to converting a traditional single-currency value.

Rudimentary assets behave similarly to the traditional model of money that most
people are used to, but being vectors, they still obey the same mathematical rules as
more complex monetary amounts.

---

## Composite Asset

An asset vector that contains a value for more than one currency.

By representing these values as a vector, we are able to do arithmetic with other
monetary values without losing any information about which currencies are involved.

---

## Forex Vector

A forex vector is a vector that represents the foreign exchange rates ***from*** every
currency in its currency space ***to*** a specific currency in the same space.

It does not matter which currency the rates in the forex vector correspond to as long
as the vector contains ***all*** of the rates for its currency space.

The [`gamma`](api_reference/linearmoney/vector.html#gamma) function is used to obtain
a forex vector with the rates to a specific currency from ***any*** valid forex vector.

Forex vectors should be constructed via the
[`forex`](api_reference/linearmoney/vector.html#forex) function of the
[`vector`](api_reference/linearmoney/vector.html) module.

---

## Evaluation

*Evaluation* refers to the process of calculating the numeric value of a monetary
amount in a specific currency. The amount can be in multiple different currencies and
the evaluation will calculate the total value of *all* of the amount's currencies in
the target currency.

This process takes a vector and produces a number representing the total value of the
vector in the target currency.

---

## Conversion

*Conversion* refers to the process of converting a monetary amount from one currency
to another and corresponds to the real-world process of exchanging a currency for
another currency. The amount can be in multiple different currencies and the conversion
will calculate the total value of *all* of the amount's currencies and convert to the
target currency.

This process takes a vector and produces another vector representing the total value
of the original vector in the target currency only.

---

## Precision Truncated

Due to how python's [decimal](https://docs.python.org/3/library/decimal.html) 
module handles precision in certain operations, especially multiplication, 
some calculations will result in cumulative rounding error even if the inputs 
are simple monetary amounts already rounded to two decimal places (or whatever 
is appropriate for the currency involved), so in these situations, linearmoney
will discard a certain number of digits from the result starting at 
the least significant bit in order to ensure that the result is consistent 
accross multiple runs of the same calculation without losing any actual 
precision, and this process is referred to in the documentation as *precision 
truncation*.

Also, it should be noted that this is done to ensure that common 
operations such as equality comparisons give the correct results, in order to 
uphold the principle of least astonishment, but this does not have any effect 
on the correctness of any calculations.

---

## Locale Tag

Locales in the linearmoney library are identified by the language and territory portion
of the
[posix format](https://en.wikipedia.org/wiki/Locale_(computer_software)#POSIX_platforms),
but do not include any encodings or other modifiers.

Example: en_US for United States English.

---

## Producer Function

Producer functions are functions in the [`data`](api_reference/linearmoney/data.html)
module that return [`Datasources`](#datasource) and are essential to the
linearmoney library's state model.

---

## Datasource

Datasources are Frozen dataclasses that define a store of data used by the
linearmoney library for data-driven functional APIs. For example, formatting
data used for localization.

Datasources are created by
[producer functions](#producer-function), and they contain
all of the information needed to be recreated exactly by another call to
the producer function as follows:

```python
producer(*datasource.id, **datasource.data)
```

This might seem useless, and being able to recreate an instance that we already
hold a reference to isn't useful in itself, but the point is that all of the
information needed for input is contained in the function's output. For immutable
data-driven interfaces, this means that we have access to the entire program
state in the return value of a function, which greatly simplifies state
management in complex applications since we don't actually have to manage
state, it's just there.

