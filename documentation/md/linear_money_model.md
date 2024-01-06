# A Linear-Algebraic Model for Monetary Data

Published: 01-Jan-2024
<br/>
Update: 05-Jan-2024 - Style and Structure.

View the update history for this article on
[GitHub](https://github.com/GrammAcc/linearmoney/commits/main/documentation/md/linear_money_model.md).

## Author

Dalton Lang
<br/>
[@GrammAcc](https://github.com/GrammAcc)

## Abstract

Working with monetary data in a computer programming context is much more difficult
than it should be, particularly when developing modern multi-currency applications
for international users. The root cause of this is a fundamental misunderstanding
of the mathematical properties of money among programmers, which stems from a lack of a
formal mathematical definition of money itself. In this article, I will attempt to
extrapolate the mathematical properties of money from its functional properties in
order to make it easier to work with money programmatically and to be able to more
reliably prove the correctness of financial calculations in general.

I will gradually develop a purely mathematical model for working with monetary data
to communicate the purpose of each piece and make the final iteration more
intelligible. This will also serve to form an intuitive understanding
of the mathematical properties of money that will make it easier to avoid
pitfalls when performing monetary calculations.

I will start by discussing the current best practices for working with currency
programmatically and the difficulties that they present.
The current practices are based on the foundational work by Martin Fowler, which
I will use as a reference point and a foundation for the model to be
developed, but my intention is not to
discredit the work of Fowler and his colleagues at Thoughtworks or anyone
else who has made contributions to the collective knowledge of our field. Nor
is it to develop a pattern or framework to replace these ideas. My intention with
this article is simply to identify and resolve a lack of clarity
of the mathematical rules that underlie these patterns in order to simplify their
implementation and maintenance in modern applications.

## Introduction

Traditional financial applications treat money as a simple data structure consisting of
an amount and a currency. This is an intuitive representation of money, and it is
certainly possible to build large scale financial applications based on this kind of
structure since all modern financial infrastructure does so. However, this is a
deceptively
inaccurate representation of money with many pitfalls waiting for the unprepared.
The reason for this is that this model only considers the intrinsic properties of
money as an object, not its functional properties as, well, money.

In order for an object to be used as money, it must satisfy three functional properties:

1. Unit of account
2. Medium of exchange
3. Store of value

[Wikipedia](https://en.wikipedia.org/wiki/Money#Functions) has a lot of information on
these properties and their history, but I will summarize them as they relate to our
model.

*Medium of exchange* is simple. We have to be able to exchange the monetary object
for other arbitrary objects at some pre-determined rate.

*Store of value* simply means that the object will still have value at some arbitrary
point in the future. This might not seem like something that a mathematical model needs
to worry about since it's more of a property of the physical object, but we will see
later on that this is something we need to consider when creating a model that
guarantees mathematical correctness of monetary calculations.

*Unit of account* is also so simple it's not often thought about. It means that we
have to be able to use *units* of the object in order to value other objects.
This property is required in order for the object to be a *medium of exchange* or a
*store of value*. This is because we can't exchange the object for another arbitrary object
without valuing the other object in units of our medium. We also can't have value
stored into the future unless we can value the object in terms of what we can exchange
it for.

The standard approach of simply pairing an amount with a currency only satisfies
property #1. It ensures that we have a countable object, but it does nothing to
indicate that we can exchange this object for something else or that it somehow
retains value over time, and we are left to implement those details
on our own.

If we are to develop a mathematical model for working with monetary data, it must be
able to encode all three of these properties at the mathematical level without any
logical orchestration in code.

## The Dilemma

Defining a mathematical object that can satisfy the functional properties of money is
easier said than done. Martin Fowler's *Money* pattern<sup>[[1]](#1)</sup> is a
good starting place
considering it is effectively the original source of the current de facto money
implementation. The core concept of Fowler's *Money* pattern is that we have a class
that encapsulates
an amount and a currency together in one object that can be used in arithmetic
operations. This is a simple idea that seems obvious in hindsight, but it was a
foundational idea for application design, and most applications that do anything with
money are at least partially inspired by it. The difficulty with Fowler's
pattern and by consequence most, if not all, modern money frameworks, is that they
treat money as a collection of separate pieces of data. An amount, a currency, an
exchange rate, rounding rules, etc... This creates a fundamental problem when working
with money in applications because the math that we can do with them is limited to the
math that can be done with abstract numbers, but we need to do math with concrete
numbers (e.g. 10 USD, 15 EUR, etc...). To support modern applications, we need some
kind of mathematical model that can handle calculations with multiple different
currencies at once without having to encode the *concreteness* of our monies in
separate objects.

Most modern currency frameworks improve upon Fowler's original single-class pattern, but
they tend to focus on adding scaffolding around the original single-class pattern to
handle other things like formatting and exchange. This has created some very useful
frameworks that make life easier for the programmers that use them, but it ends up making
the resulting framework more useful in a specific context without solving the general
problem of working with monetary data programmatically, so not all applications benefit
from or are able to use these frameworks. There is nothing in place to make the work
of the framework authors easier, so improvements to existing frameworks and new, better
frameworks are few and far between.

The real issue we need to solve if we want a robust and language-agnostic pattern for
working with money is not how to structure all of the separate pieces of data that can
affect financial information, but how to actually do math with *money* instead of only
numbers. If we can figure that out, then implementing any kind of currency framework
will be much easier since we will have mathematically enforceable rules to guide our
design decisions.

The fundamental flaw in the current de facto standard money implementation is that it
attempts to do math on integers or decimals instead of concrete monies, which causes
the programmer (or pattern designer) to have to define their own rules of mathematics
for working with money. Fowler actually points out this dilemma in his book when he
discusses arithmetic between different currencies.
He mentions that the simplest solution
is to treat the addition/subtraction of two different currencies as an error, but it's
also possible to use a structure like Ward Cunningham's
*Money Bag*, an object that tracks values in multiple currencies
simultaneously<sup>[[1]](#1)</sup>, so this is a core issue of working with monetary
data that Fowler was aware of over 20 years ago but the broader programming community
has not paid much attention to, or at least has coped with instead of actively
searching for a solution. Of note, Fowler doesn't advise how
we *should* solve this particular problem in his book and instead, he leaves it as a
sort of implementation detail for the programmer to decide based on the requirements of
the application. This is understandable since the solution would be project-dependent
when using this pattern, but this design decision the programmer has to make is
deceptively problematic.

It might not seem like it at first, but when we make these kinds of decisions, we are
essentially redefining the rules of mathematics as they apply to money. This has
very far-reaching consequences when we start doing more complicated things like
integrating with third-party services or serializing monetary data since our
calculations with money affect the accuracy of our data which has a very
wide range of highly impactful uses.

This isn't something that a developer should have to think about or decide. Even
ignoring the additional design burden this places on the programmer, it also creates
less reliable software. For example, what would happen if I decided that
*2 + 2 = cheese*, and then you tried to integrate a service I was providing with your
application?

At the end of the day, no matter how much we want to, programmers don't get to redefine
the rules of the universe.

Of course, we've been doing things this way for over 20 years, and it works, so why
change it?

Unfortunately, this isn't only an "If it ain't broke, don't fix it." kind of issue.
When it comes to programming, once we get into the realm of software, barring resource
limitations, we can pretty much do whatever we want.

Continuing with the example above, if I really did decide that I wanted
*2 + 2* to equal *cheese*, I could do that:

```python
class FourCheeseBlend(int):
    """An especially zesty integer."""

    def __add__(self, other) -> int:
        """2 + 2 == cheese"""
        
        if self == 2 and other == 2:
            return hash("cheese")
        else:
            return super().__add__(other)
```

The above Python class will integrate properly with any Python 3 program, it's
type-safe, and the behavior will be correct until the program puts 2 and 2 together.

However, once we need to calculate *2 + 2*, the behavior of the program becomes
undefined, and we have no indication that anything went wrong.

The moral of this story is that just because we *can* make up our own rules doesn't mean
that we *should*, and it would save us time and effort if we didn't have to.

Of course, most reasonable programmers would think it's pretty obvious that the class
above should never be used, but the reason why that is obvious is because the rules of
basic arithmetic are obvious to us. However, when it comes to doing math with money, very
few programmers (or anyone for that matter) actually understand the rules for how to
calculate monetary amounts. In fact, at the time of writing, there don't seem to
be any established mathematical rules for this, so I would argue that without
mathematical truth to guide us, we have been including FourCheeseBlends in our
financial applications for as long as we've been building them. We just haven't
realized it yet.

---

## Developing the Model

As mentioned in the previous section, to the best of my knowledge, there are no
clearly defined mathematical properties of money in the current literature, so in
order to define a mathematical model, we first need to identify those properties
ourselves and decide on a purely mathematical object that is capable of encoding those
properties for us.

---

### Conceptual Properties of Money

To start with, we should elaborate a bit on the three properties of money defined
in the [introduction](#introduction):

1. Unit of account:
    - Object is countable, usually in the form of uniform physical objects or fungible
    non-physical tokens of some kind.
2. Medium of exchange:
    - Object can be exchanged for (almost) any kind of physical or non-physical good
    or service at some predetermined price in units of the monetary object.
3. Store of value:
    - Object can still be used as a *medium of exchange* at any time in the
    foreseeable future.

In order to satisfy #1, we need to encode the fact that our money is a concrete number
and do math with this concrete number without stripping away the *unit* that the number
corresponds to.

For #2, we have to satisfy #1 since we can't exchange an object or token for something
else unless we can value the other object in terms of a certain number of countable
units of our monetary object, but we also need to somehow show that a monetary object
is convertible to other arbitrary objects at a specified rate in order to mathematically
represent this property of money, so in order for our model to support #2, it
needs to support conversion of currencies with foreign exchange rates between them or
some other mathematical operation that corresponds to the exchange of a monetary
object for some other object.

For #3, we need to support #2 since the property of a *store of value*
simply means that we can still use the object as a *medium of exchange* at
some point in the future, but this is subtly difficult as it requires us to include some
means of calculating the temporal nature of money in our model, otherwise we can't
really prove that a *medium of exchange* used today is still a *medium of exchange*
tomorrow.

With this in mind, we need to ensure that our mathematical object has some way to
ensure that these three properties are not lost when we perform calculations on monetary
amounts, but we don't necessarily need to satisfy all three properties with a single
mathematical object. We can use functions and higher level mathematical constructs
in our model in order to satisfy all three properties for the model as a whole.

---

### A Mathematical Money Object

Let's start by looking at the traditional money implementation first and see how well
it satisfies our requirements.

For #1, the standard implementation based on Fowler's pattern associates a single
amount with a single currency inside an object to ensure we are always aware of the
concreteness of the numbers we are working with, but this is an incomplete data model
because a concrete number is still only a number mathematically, so using an
object-oriented approach to encapsulating the amount and currency together in one object
requires us to conceptually strip the currency away before and reattach it after any
calculation we perform on the monetary amount, which is additional logical overhead for
the class implementing the Money object and its maintainers. It would be best if we
could somehow encode the fact that we are dealing with a concrete number in the
mathematical object we use to represent monetary amounts numerically, so that these
calculations would be handled seamlessly and the class can focus on tracking the high
level data that matters to the user and abstracting away the mathematical
implementation.

For #2 and #3, the standard implementation offers no solution and Fowler's pattern
doesn't make any suggestions for how to handle this. Essentially, the standard
implementation only provides the properties of a *unit of account*, but does not satisfy
the other requirements of money. This is why it is deceptively difficult to build
applications to work with money. Even using an established pattern, we still
have to deal with the other two properties of money on our own, which is where most of
the functional behavior of money is actually determined since what really makes money
different from any other countable object is its properties as a
*medium of exchange*, so we really need a mathematical representation of money that
encodes all of that for us, so we as programmers no longer have to build the
scaffolding to support the other properties of money ourselves.


Since we know that we can't have a *store of value* unless it is also a
*medium of exchange*, and we can't have a *medium of exchange* unless it is also a
*unit of account*, we can start by identifying a mathematical object capable of
encoding and doing calculations with concrete numbers as that will ensure that our
mathematical object represents something that is countable.

### Countable Monies

If we're looking for a mathematical object to represent a concrete number, we can find
inspiration with mathematical representations of other units of measure. Just like
Length, Width, and Height can be represented as a 3-dimensional vector in Euclidean
space, we can represent a monetary amount of multiple currencies as an N-dimensional
vector of concrete numbers. Each component of the vector will represent one of the N
currencies we are working with in an N-dimensional vector space over the reals.

For example, if we have 6 EUR and 10 USD in our wallet, we can represent the monetary
value of our wallet as the vector $(6,10)$ assuming that we are only tracking EUR and
USD in our application. If we were to add JPY to our application, we would have the
vector $(6,0,10)$ assuming our vectors are represented in alphabetical order by
currency.

Of course, when working with vectors in practical applications, it's helpful to
specify a basis. To keep things simple while we develop our model, we can simply use
the standard Euclidean basis in N dimensions, so our basis vectors are all orthogonal
to each other and of magnitude 1.

We will follow a common convention and refer to this basis as $e$ and its basis
vectors via subscripts e.g. $e_1$, $e_2$, $e_n$. The vector space spanned by the
basis $e$ will be referred to as $V$.

---

### Doing Math with Money

With the definitions in the previous section, we have the foundation for how to do math
with multiple currencies simultaneously since we can encode the concreteness of our
monetary values in the definition of the vector space and simply apply the rules of
linear algebra to ensure the correctness of our monies without enforcing it in code.

For example, if we have two money vectors in an $(EUR, JPY, USD)$ vector space:

- $u = (6, 500, 20)$
- $v = (0, 250, 10)$

We can add and subtract like any other vector:

- $u + v = (6 + 0, 500 + 250, 20 + 10) = (6, 750, 30)$
- $u - v = (6 - 0, 500 - 250, 20 - 10) = (6, 250, 10)$

It is plain to see that this form of arithmetic is consistent with what would happen if
we performed these operations with cash in real life.

Multiplication and division of vectors by scalars also makes sense when thinking in
terms of cash:

- $2u = (6 \cdot 2,\ 500 \cdot 2,\ 20 \cdot 2) = (12, 1000, 40)$
- $u \div 2 = (6 \div 2,\ 500 \div 2,\ 20 \div 2) = (3, 250, 10)$

There isn't really any other way to interpret multiplication/division of our wallet
other than doubling/halving the contents, so this makes sense for real-world
applications.

Of course, in most real-world situations, multiplication would only be done against a
single currency, but it's good to have the rules for how to handle multiplication of
multiple currencies established so that we don't have to decide them for ourselves.

It's worth noting that these examples use cash to visualize the application of the
model to real-world use cases, but the same concepts that apply to cash apply to
digital currency as well. Even if there is no physical object, the same conceptual
properties that make money what it is still apply. For example, we could define
multiplication of two money vectors via the Hadamard product and the rules of linear
algebra would keep our math consistent, but this would not reflect the reality of money.
It doesn't make much sense to multiply an arbitrary object by another arbitrary object
whether it is a physical object or a conceptual token. The properties of a
*unit of account* as a quantity of some kind of object are universal whether the object
is physical or not, so the intuition we develop through this model holds for money in
general.

We have a vector space, we can define physical assets as vectors, and we
can use them in arithmetic, so we've mathematically satisfied the properties of a
*unit of account*, but we need to be able to convert those physical assets to different
currencies in order to satisfy the properties of a *store of value* and
*medium of exchange* and finally get past the limitations we've faced for two
decades, so how do we do that?

---

### Math with Forex Rates

In traditional applications we would use forex rates by multiplying our single-currency
numerical amount by the rate to convert a currency from one to another, but for our
purposes, we need to be able to convert ***all*** of the currencies in a money vector
simultaneously, so it stands to reason that our forex rates need to be represented as
a vector as well.

Let's assume we have the following exchange rates in $V^3$:

- EUR -> EUR = 1.0
- JPY -> EUR = 0.004
- USD -> EUR = 0.4

These rates correspond to the rates vector: $r = (1.0, 0.004, 0.4)$, which represents
the exchange rates ***from*** each of the currencies in $V$ ***to*** EUR.

Continuing with our asset vector from the previous sections $u = (6, 500, 20)$, in
order to convert this vector into a single specific currency, we need to somehow
multiply all components of the vector by the exchange rate ***from*** that component's
corresponding currency ***to*** the target currency and then sum the results in order
to get the full value of the money vector in the target currency only.

That sounds a lot like the dot product, doesn't it? Let's see what that looks like:

\[ \langle u,r \rangle = (6 \cdot 1.0 + 500 \cdot 0.004 + 20 \cdot 0.4) = (6 + 2 + 8) = 16 \]

This works, but now our result is only an abstract number, so we've lost our
ability to encode the fact that this is a concrete number that represents 16 EUR and
not only 16.

To solve that, we can multiply the result of the dot product calculation with the basis
vector $e_k$ that corresponds to the target currency since that vector is all 0s except
for the target currency, which will be 1:

\[ \langle u,r \rangle e_1 = 16 (1, 0, 0) = (16, 0, 0) = 16\ EUR \]

But what if we want to convert to JPY or any other currency, but we don't have
a rates vector for that currency? That is to say, what if the only rates vector we
have is the $r$ vector representing the rates ***to*** EUR, but we want to convert
to another currency in $V$?

We can calculate the rates vector to convert to any other currency in $V$ with a
linear transformation of $r$:

\[ r'_k = \frac{1}{\langle r,e_k \rangle}r \]


The calculation above divides 1 by the scalar rate ***from*** our target currency
***to*** whatever currency $r$ converts to, which in this case is EUR, in order to get
the rate ***to*** our target currency ***from*** the target currency of $r$.
This result is then multiplied by the original $r$ in order to convert all component
rates to the rate ***from*** the component currency ***to*** the target currency.

So, to convert our asset vector to JPY:

\[ jpy = \langle u,r'_2 \rangle e_2 \]


Or generally:

\[ c_k = \langle u,r'_k \rangle e_k \]

With this we can define a *Convert* function for converting any asset vector to any
currency in $V$:

\[ C(v)_k = \langle v,r'_k \rangle e_k \]


This works well, but $r'_k$ is a bit too implicit in what it is actually doing.
Essentially, the transformation $r'_k$ is taking the vector $r$ and transforming the
rates to whatever currency corresponds to the index $k$, but because these
transformations are all related to each other, it would make the structure of this
transformation clearer if we described it as a set of the vectors produced by
transforming the rates represented by $r$ to *all* of the different currencies
in $V$:

\[ \gamma = \{ v_1,...,v_n\ |\ v_k = \frac{1}{\langle r,e_k \rangle}r \land 1 \leq k \leq n \} \]

For the remainder of this article, I will refer to the set resulting from the
transformation above as the *gamma set*, and the vector representing the rates
***to*** currency $k$ in the gamma set will be denoted $\gamma_k$.

The set of vectors designated by $\gamma$ explicitly represents the exchange rates
***from*** each of the currencies in $V$ ***to*** the currency corresponding to each
index $k$, so our $C$ function remains the same, but we replace $r'_k$ with
$\gamma_k$, and the model is made clearer overall.

\[ C(v)_k = \langle v,\gamma_k \rangle e_k \]

The nice thing about this transformation is that it gives the same result regardless of
the choice of $r$, so as long as we have all of the rates ***from*** each of the
currencies in $V$ ***to*** any arbitrary currency in $V$, we can obtain the rates
***to*** any other arbitrary currency in $V$ with the $C$ function... sort of.

There is a problem with our definition of $\gamma$ above. Since we don't place any kind
of restriction on the value of $r$, it acts on *any* arbitrary vector in $V$, which
means that we could provide an $r$ that doesn't actually represent forex rates, which
would contaminate our model. We need to somehow restrict the possible structure of $r$
so that it can be guaranteed to actually represent a vector of forex rates.

The first restriction we need to apply presents itself in the transformation
originally given by $r'_k$ and reused in the earlier definition of $\gamma$:

\[ r'_k = \frac{1}{\langle r,e_k \rangle}r \]

This transformation includes a division of constant 1 by the result of the dot product.
This means that the components of $r$ can't be 0. If *any* of the components of $r$
are 0, then at least one of the results of the $\gamma$ transformation will result in
division by 0 when the dot product is taken with the basis vector of that index. If we
were using the definition given by $r'_k$, then we would only technically need to
restrict the value of the component at index $k$ to be non-zero since the $r'_k$
transformation can be taken in isolation based on its definition, but with the set
builder notation used for $\gamma$, all components of $r$ must be non-zero since we
apply this transformation to all components of $r$ in order to obtain the gamma set:

\[ \{ r \in V\ |\ (\forall r_k) r_k \not = 0 \} \]

This limitation is not simply a coincidence. Conceptually, forex rates represent the
values of currencies in relation to each other, and this transformation has the effect
of inverting this relationship for all of the currencies in $r$. It doesn't make sense
for any of the components of $r$ to be 0 because, by the conceptual definition of
money, a currency cannot have a value of 0. If it did, it would not be usable as a
*store of value* or a *medium of exchange*. To illustrate this further, take a
defunct currency that is no longer in circulation. It may have some value for
collectors that would be willing to pay money to obtain it, but this exchange is in
the form of the exchange of money for goods, not money for money, and you would not be
able to use the defunct currency at the grocery store or to pay your rent, so it does
not qualify as a general *medium of exchange*. If it can't be universally
exchanged, then it can't store universal value into the future, so it is also not
usable as a *store of value*. Any other situation that would result in an exchange rate
of 0 will also represent an object that does not qualify as a general medium of
exchange and thus does not qualify as a currency, so we can enforce a restriction that
all components of $r$ be non-zero, but to be more thorough, we should enforce that all
values be positive since a negative value logically corresponds to debt, which is not
a property of money itself and can be easily represented with negative quantities of
money in our model.

\[ \{ r \in V\ |\ (\forall r_k) r_k > 0 \} \]

The second restriction we need to apply to $r$ is less obvious. At least one component
of $r$ must be exactly 1:

\[ \{ r \in V\ |\ (\exists r_k) r_k = 1 \} \]

The reason for this is better illustrated by example:

let $r = (0.5, 0.004, 0.4)$

If we calculate our gamma set with this $r$, we get the following for
$\gamma_1$: $(1.0, 0.008, 0.8)$

This is problematic because in order for our model to remain consistent, we need the
equality: $\gamma_k \equiv r$ to hold when $k$ is the index of the currency that $r$
represents the rates ***to***. Otherwise, we can't trust that $\gamma_k$ represents
the rates ***to*** the target currency. In the example above, this currency is
EUR, and this equality does not hold. The reason is because $r$ does not correctly
represent the rates to *any* currency in $V$. This is proven because our vectors
always include *all* currencies in the space $V$, and any vector that represents the
rates ***to*** a currency in $V$ will have a value of 1 for the component corresponding
to the target currency since any currency has an exchange rate of 1 with itself.
It's possible that multiple currencies could have a value of 1 since many currencies
are pinned to the value of other currencies, but *at least one* component of the
vector must be exactly 1 in order for the vector to be capable of correctly
representing exchange rates in $V$. A vector that does not include at least one
component equal to 1 may technically be a set of forex rates, but only in a higher
dimensional vector space. This could happen if we took a member of a vector subspace
of $V^{n+x}$ with dimension n as our $r$ in $V^n$, so we need to restrict the valid
values of $r$ explicitly.

This gives us a definition for the set of all valid forex vectors in $V$:

\[ \tau = \{ r \in V\ |\ \forall r_k (r_k > 0) \land \exists r_k (r_k = 1) \} \]

So, our final definition for the gamma set is:

\[ \gamma = \{ v_1,...,v_n\ |\ v_k = \frac{1}{\langle r,e_k \rangle}r \land 1 \leq k \leq n \land r \in \tau \} \]

With this, we have everything we need to do math with money... right?

---

### Exploring Currency Space

We satisfied the properties of a *medium of exchange*, but there are some issues with
the methods for conversion employed in the previous section.

Particularly, this works well for a single point in time, but what if the exchange
rates change? How do we track those changes? Recall that in order for our model to
satisfy the properties of a *store of value*, we need to somehow encode the temporal
characteristics of money as well.

Fortunately, the concept of forex rates is inherently temporal since they change over
time, so our model is capable of encoding the temporal properties of money simply by
calculating a change in $\gamma$ within the same vector space. This is made trivial by
the fact that $\gamma$ defines a set of vectors in $V$, so all we have to do to track
the temporal changes in money is track the movement of the vectors contained in the
gamma set. For example:

- Let $\gamma'$ be the new forex rates, then

\[ \Delta = \{ v_1,...,v_n | v_k = \gamma'_k - \gamma_k \} \]

This also aligns well with the way that we deal with forex rates in real life since
forex rates are constantly fluctuating, but we actually use snapshots of them at
various points in time, so by representing them as vectors we are able to
mathematically model *movement* of forex rates over time in the same way that we can
model *movement* of objects in 3D space through vector transformations.

It's helpful to think of the vector space $V$ as a *Currency Space*, and the gamma set
as a set of linear transformations of the Currency Space.
This terminology is useful because it describes the actual mathematical behavior
of money. Within $V$, we can represent monetary values of the currencies
in $V$ as arbitrary vectors, and we can track the fluctuations of the values of those
currencies over time via $\gamma$.

In this way, we can model the *movement* of monetary values over time, which provides
us with the final piece needed to satisfy the properties of a *store of value*
mathematically. This model is technically sufficient for representing money
mathematically, but we can still improve the practical usability of it.

### Evaluation

The model we have defined so far technically satisfies the functional properties of
money, but there is another conceptual operation that we can add to our model to
simplify its use in practical applications that require lots of currency conversions.

Most of the situations that require currency conversion in financial applications
actually only need to evaluate the monetary amount in some target currency, but they
do not actually represent a transaction where currencies are exchanged.
For example, when purchasing goods in an international web store, the items may be
valued in the local currency of the retailer, but the cart may display the cost of the
total purchase in the user's local currency. There is no actual transaction associated
with the display of the total price in the website's UI, the actual conversion would
occur when the user makes the purchase and their local currency is converted to the
transaction currency for payment, but with a traditional model, we would convert the
currency to the user's local currency and then display a formatted amount to the user
before any actual transaction takes place.

If we separate the concepts of *conversion* and *evaluation* we can make it easier to
work with money programmatically by allowing the reduction of a monetary amount to an
abstract number representing its value in a specific currency. Similar to how the dot
product taking two vectors and producing a scalar allows more complex vector
operations to be defined on a vector space, this opens up additional possibilities for
how to apply the model in our applications without losing any of the provability that
the model is intended to provide.

The *Convert* and *Evaluate* operations can be summarized informally as follows:

- Convert:
    - Represents the transactional exchange of one currency for another.
    - Generally, anything that would be recorded as a transaction in a bookkeeping sense.
    - E.g. Trading on the forex market, exchanging cash at a customs office, making a
    purchase in a foreign currency (your money is converted to the transaction
    currency at the time of the transaction).
- Evaluate:
    - Represents the valuation of an amount of one currency in another currency but
    not an actual exchange of the currencies.
    - Pretty much anything that isn't an actual transaction would be an evaluation.
    - Most traditional uses of currency conversion in applications fall into this
    category.
    - E.g. Displaying an amount in the user's local currency. Doing a preliminary
    calculation before a transaction, "how much is this in xyz?".

Given the above description, how do we represent the *Evaluate* operation
mathematically?

*Evaluation* essentially boils down to checking the value of a conversion before
committing to the full transaction, and if we recall our definition of the *convert*
function:

\[ C(v)_k = \langle v,\gamma_k \rangle e_k \]

We noticed while we were developing that portion of the model that the intermediate
calculation $\langle v,r \rangle$ gives an abstract number, which was problematic for
our *convert* function, so we multiplied it by the basis vector $e_k$ to get an asset
vector representing the collapsed monetary amount, but as described above, for the
*evaluation* of a monetary amount, we actually want an abstract number since we don't
want to construct a new vector representing some physical currency. We actually want to
escape the vector space entirely, so our *evaluate* function is simply the intermediate
stage of the *convert* function:

\[ E(v)_k = \langle v,\gamma_k \rangle \]

And we can redefine our $C$ function to use this as well:

\[ C(v)_k = E(v)_k e_k \]

With these two functions and our definitions of $\tau$ and $\gamma$, we have
everything we need for our complete mathematical model of money and a little bit extra.

---

### Putting it all together

Here is the full model in its entirety:

- Assumptions:
    - Let $V$ be the n-dimensional Euclidean vector space over $\mathbb{R}$
    - Let $e$ be the standard basis in $V$

\[ \tau = \{ r \in V\ |\ \forall r_k (r_k > 0) \land \exists r_k (r_k = 1) \} \]

\[ \gamma = \{ v_1,...,v_n\ |\ v_k = \frac{1}{\langle r,e_k \rangle}r \land 1 \leq k \leq n \land r \in \tau \} \]

\[ E(v)_k = \langle v,\gamma_k \rangle \]

\[ C(v)_k = E(v)_k e_k \]

## Notes on Performance

Most programmers would have noticed that, with this model, monetary calculations
are in linear time. At first glance, it definitely seems like this would make
calculations much slower than a traditional model, but this is not necessarily true.

I won't make any assertions about the specific performance of the linear model
compared to the traditional model since I have not profiled them against each
other, and there are too many factors that contribute to performance to draw a
meaningful conclusion about the difference, but I want to clarify that the time
complexity of the linear model is not usually linear in practice.

Generally speaking, calculations in the linear model would run in O(n) time, where
*n* is the dimension of our currency space, but because most practical applications
will not change the currency space at run-time, we can consider the running time to be
constant.

For example, if you have an application that supports EUR, JPY, and USD as
in our previous examples, then the running time for calculations would be O(3) since
*n* is constant at run-time. This is not simply a pedantic difference because the running
time of calculations between two vectors really does remain constant with respect to
input. Of course, the constant multiplier of 3 means that even if we add two vectors
that only have one component with a value, such as two vectors of only USD where EUR and
JPY are both 0, then the running time will still be O(3) even though only one value of
each of the vectors is actually
relevant to the calculation. From this, we see that in some situations the
traditional model will be more
efficient, but in practice, if the application does need to do calculations with
multiple currencies, then the running time of the traditional model will still be
O(n), where *n* is the number of currencies involved. Additionally, in the traditional
model, each of those *n* calculations are between user-defined types, but in the linear
model, each of the *n* calculations are between primitive numeric types, so the constant
factor of each individual calculation should be lower in both CPU time and memory usage
in the linear model.

As a rule of thumb, performance will degrade in the linear money model compared
to the traditional model as the
difference between the number of components of the vector that have a value
and the dimension of the currency space grows. E.g. a vector with only one value
in a 20-dimension currency space will likely perform worse than a traditional
money type, but a calculation with 20 currencies will likely be faster and use
less memory in the linear model with a 20-dimensional currency space than in the
traditional model. Also, most practical applications only support a small number of
currencies, and most time complexity issues only come into play at fairly large
inputs, so it's likely that the usage of primitive types will make the linear model
more efficient in most practical applications regardless of the number of valued
components in the calculation.

Again, this is based on the time complexity and general assumptions about the
performance of primitive types vs user-defined types. Depending on the language and
implementations, either model could outperform the other. Always profile your code.

Lastly, when I say *most practical applications*, I'm referring to applications
that have complete control over the monetary calculations they perform.
Common examples include accounting software, point-of-sale systems, and ERP software.
However, this does not apply to many developer tools or resources that
provide services related to arbitrary currencies such as a currency library
implementing the linear money model.
In that kind of application, the time complexity would be linear due to the unknown
dimension of the currency space for the end-user. In other words, if you define the
currency space of the application explicitly, the running time is constant and can be
accounted for, but if you
let the user define the currency space or it is dynamically sized, then the time
complexity is linear. This should be kept in mind when creating services/libraries
that will be consumed by other applications.

## Conclusion

With the model developed in this article, we have a mathematical representation
of the functional properties of money and a clear definition of how arithmetic
with monetary values should work due to the mathematical rules of linear algebra:

- Addition and Subtraction of monies and other monies is allowed.
- Addition and Subtraction of monies and scalars is **not** allowed.
- Multiplication and Division of monies by scalars is allowed.
- Multiplication and Division of monies by other monies is **not** allowed.

Additionally, because of the rules of linear algebra, we can easily use
monetary values in calculations in other schools of math that have rules for
interpreting
vectors such as calculus and exterior algebra. This is likely useful for Economics
where linear algebra and calculus are already used frequently, but
it could also prove useful for developing complex models through dimensional
analysis since it provides a clear definition of the mathematical structure of
monetary values as units of currencies.

I hope that this article has provided some insight into the mathematical properties
of money and how we can leverage these properties to create more robust financial
applications.

---

## References

<a id="1">[1]</a>
M. Fowler, *Patterns of Enterprise Application Architecture*
Addison-Wesley Professional. 2002
ISBN-10: 0-321-12742-0
ISBN-13: 978-0-321-12742-6
