# linearmoney Frequently Asked Questions

---

## What is the meaning of life, the universe, and everything?

42

---

## What are the recommended import conventions?

- The top-level package should be imported using a numpy-style short alias.
    - `import linearmoney as lm`
- Functions should not be imported directly, and instead should be called as
members of the containing module's namespace.
    - `lm.vector.dot()`
    - `lm.data.currency()`
- Identifiers that are primarily used as a type (Classes, Exceptions, etc...)
should be imported and used directly.
    - `from linearmoney.exceptions import IntegrityError`
    - `from linearmoney.vectors import ForexVector`

