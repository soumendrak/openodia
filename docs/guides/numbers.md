# Numbers, dates and currency

Convert integers to Odia words and back, verbalize dates and rupee amounts, and switch between Odia and ASCII digits. Every example on this page is run by the test suite.

## Cardinals

`to_words` takes an `int`. The default `scale="indian"` uses ଲକ୍ଷ (lakh) and କୋଟି (crore); `scale="short"` uses ମିଲିୟନ (million) and larger units.

```pycon
>>> from openodia import numbers
>>> numbers.to_words(0)
'ଶୂନ୍ୟ'
>>> numbers.to_words(101)
'ଏକ ଶହ ଏକ'
>>> numbers.to_words(1234567)
'ବାର ଲକ୍ଷ ଚଉତିରିଶ ହଜାର ପାଞ୍ଚ ଶହ ସତଷଠି'
>>> numbers.to_words(12345678)
'ଏକ କୋଟି ତେଇଶ ଲକ୍ଷ ପଞ୍ଚଚାଳିଶ ହଜାର ଛଅ ଶହ ଅଠସତୁରୀ'
>>> numbers.to_words(1234567, scale="short")
'ଏକ ମିଲିୟନ ଦୁଇ ଶହ ଚଉତିରିଶ ହଜାର ପାଞ୍ଚ ଶହ ସତଷଠି'
>>> numbers.to_words(-100)
'ଋଣାତ୍ମକ ଏକ ଶହ'
```

`from_words` reverses it. It must be given the same scale that produced the words:

```pycon
>>> numbers.from_words("ଏକ ହଜାର ଦୁଇ ଶହ")
1200
>>> numbers.from_words(numbers.to_words(987654321))
987654321
>>> numbers.from_words("ଏକ ମିଲିୟନ", scale="short")
1000000
>>> numbers.from_words("ଏକ ମିଲିୟନ")
Traceback (most recent call last):
  ...
ValueError: unrecognised token: 'ମିଲିୟନ'
```

!!! note "Gotcha: errors for bad input"
    `from_words` raises `ValueError` for a word it does not know, which includes short-scale words read with the default Indian scale (as above). `to_words(1.5)` raises `TypeError` because only integers are supported. `bool` is an `int` in Python, so `to_words(True)` returns `ଏକ`.

## Ordinals

Ordinals from 1 to 10 are irregular. From 11 on, the suffix ତମ is added to the cardinal.

```pycon
>>> numbers.to_ordinal(1), numbers.to_ordinal(2), numbers.to_ordinal(10)
('ପ୍ରଥମ', 'ଦ୍ୱିତୀୟ', 'ଦଶମ')
>>> numbers.to_ordinal(11), numbers.to_ordinal(21)
('ଏଗାରତମ', 'ଏକୋଇଶତମ')
>>> numbers.to_ordinal(0)
Traceback (most recent call last):
  ...
ValueError: ordinals are defined for n >= 1, got 0
```

## Dates

`to_words_date` accepts a `date` or `datetime` (the time part is ignored). The day is an ordinal and the year is spelled out.

```pycon
>>> from datetime import date, datetime
>>> numbers.to_words_date(date(2000, 1, 1))
'ପ୍ରଥମ ଜାନୁଆରୀ, ଦୁଇ ହଜାର'
>>> numbers.to_words_date(datetime(2026, 10, 27, 5, 30))
'ସତାଇଶତମ ଅକ୍ଟୋବର, ଦୁଇ ହଜାର ଛବିଶ'
```

## Currency

Only rupees (`"INR"`) are supported. The fractional part is rounded half-up to two places and spoken as ପଇସା (paisa). A zero part is left out.

```pycon
>>> numbers.to_words_currency(1500.50)
'ଏକ ହଜାର ପାଞ୍ଚ ଶହ ଟଙ୍କା ପଚାଶ ପଇସା'
>>> numbers.to_words_currency(1)
'ଏକ ଟଙ୍କା'
>>> numbers.to_words_currency(0.05)
'ପାଞ୍ଚ ପଇସା'
>>> numbers.to_words_currency(0)
'ଶୂନ୍ୟ ଟଙ୍କା'
>>> numbers.to_words_currency(1234.5, scale="short")
'ଏକ ହଜାର ଦୁଇ ଶହ ଚଉତିରିଶ ଟଙ୍କା ପଚାଶ ପଇସା'
>>> from decimal import Decimal
>>> numbers.to_words_currency(Decimal("10.25"))
'ଦଶ ଟଙ୍କା ପଚିଶ ପଇସା'
>>> numbers.to_words_currency(5, currency="USD")
Traceback (most recent call last):
  ...
ValueError: unsupported currency 'USD'; supported: 'INR'
>>> numbers.to_words_currency(-5)
Traceback (most recent call last):
  ...
ValueError: amount must be >= 0, got -5
```

!!! note "Gotcha: prefer `Decimal` for money"
    A `float` is converted with `Decimal(str(amount))`, so `1500.50` is exact. Values you computed with float arithmetic can still carry rounding error before they get here.

## Digits

`ascii_to_odia` and `odia_to_ascii` convert digits inside a longer string and leave every other character as it is.

```pycon
>>> numbers.ascii_to_odia("Call 100 ଆଜି 2026")
'Call ୧୦୦ ଆଜି ୨୦୨୬'
>>> numbers.odia_to_ascii("୧୨୩ abc")
'123 abc'
```

## Next

- [Text processing](text-processing.md) for `clean`, which can also convert digits.
- [API reference: numbers](../api/numbers.md).
