"""Number ↔ words, digit conversion, currency, and date verbalization for Odia.

Examples:
    >>> from openodia import numbers
    >>> numbers.to_words(1234)
    'ଏକ ହଜାର ଦୁଇ ଶହ ଚଉତିରିଶ'
    >>> numbers.ascii_to_odia("2026")
    '୨୦୨୬'
    >>> numbers.to_ordinal(3)
    'ତୃତୀୟ'
"""

from openodia.numbers._currency import to_words_currency
from openodia.numbers._dates import to_words_date
from openodia.numbers._digits import ascii_to_odia, odia_to_ascii
from openodia.numbers._ordinals import to_ordinal
from openodia.numbers._words import NumberingScale, from_words, to_words

__all__ = [
    "NumberingScale",
    "ascii_to_odia",
    "from_words",
    "odia_to_ascii",
    "to_ordinal",
    "to_words",
    "to_words_currency",
    "to_words_date",
]
