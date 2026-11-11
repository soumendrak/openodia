# Find and mask personal identifiers

`pii` finds phone numbers, emails, URLs, Aadhaar numbers, PAN, PIN codes, dates, currency amounts, dictionary names, and a low-confidence address span. It reads Odia digits and ASCII digits, including text in NFD, and it runs offline. A lone name, a bare amount, and a street with no administrative word within 40 characters of a PIN stay visible, so masked text can still identify a person. `pseudonymize` records `<TYPE:n>` tokens in a `KeyStore` and `restore` puts them back, except a `<TYPE:n>` already in the input is rewritten when that token is in the store.

`pii` needs a release newer than 0.1.14. On PyPI 0.1.14, `import openodia.pii` fails and `openodia pii` exits with code 2. From a source checkout, `uv run python` can import it.

Every example on this page is run by the test suite.

## Find matches

`detect` returns one `PIIEntity` per match, in order. `start` and `end` are character offsets into the text you passed.

```pycon
>>> from openodia import pii
>>> pii.detect("ରାମ ସୀତା ଘରକୁ ଯାଏ ।")
[]
>>> text = "ମୋ ଫୋନ ୯୮୭୬୫୪୩୨୧୦ ଓ a@b.com"
>>> pii.detect(text)
[PIIEntity(type='PHONE', text='୯୮୭୬୫୪୩୨୧୦', start=7, end=17, confidence=0.9), PIIEntity(type='EMAIL', text='a@b.com', start=20, end=27, confidence=0.95)]
```

A 10-digit number that starts with 6, 7, 8, or 9 is a `PHONE`, including an order number that happens to have that shape. A PIN code is reported only after `PIN`, `Pincode`, or `ପିନ`.

```pycon
>>> pii.detect("PIN 751001")
[PIIEntity(type='PINCODE', text='751001', start=4, end=10, confidence=0.8)]
>>> pii.detect("751001")
[]
```

## Mask matches

`mask` replaces each match with `<TYPE>`. With those tags, masking the result again changes nothing, unless the input chains more than 10 values that were glued together.

```pycon
>>> pii.mask(text)
'ମୋ ଫୋନ <PHONE> ଓ <EMAIL>'
>>> pii.mask(pii.mask(text))
'ମୋ ଫୋନ <PHONE> ଓ <EMAIL>'
>>> pii.mask(text, types=["EMAIL"])
'ମୋ ଫୋନ ୯୮୭୬୫୪୩୨୧୦ ଓ <EMAIL>'
```

`types` is a list of `PHONE`, `EMAIL`, `URL`, `AADHAAR`, `PAN`, `PINCODE`, `DATE`, `MONEY`, `NAME`, and `ADDRESS`. A bare string raises `TypeError`.

```pycon
>>> pii.detect(text, types="EMAIL")
Traceback (most recent call last):
  ...
TypeError: types must be a list of PII type names, not a single string; wrap it in a list
```

## Drop a weak Aadhaar match

An Aadhaar-shaped number that passes the Verhoeff checksum has confidence 0.95. One that fails has confidence 0.5. `min_confidence` drops weaker matches before overlapping matches are merged.

```pycon
>>> pii.detect("234567890124")[0].confidence
0.95
>>> pii.detect("234567890125")[0].confidence
0.5
>>> pii.mask("234567890125", min_confidence=0.9)
'234567890125'
```

## Limits

Overlapping matches become one span. The type is the longest match. When the lengths are equal, the earlier of `EMAIL`, `URL`, `AADHAAR`, `PAN`, `PHONE`, `DATE`, `MONEY`, `NAME`, `ADDRESS`, and `PINCODE` wins, so `mask` does not leave part of a detected value visible.

`mask` repeats until the text stops changing, and it stops after 10 passes. After more than 10 glued values, the text it returns can still contain a raw value.

An email local part longer than 64 characters is not found. When that local part contains punctuation, only its last 64 characters may be masked. A local part that starts with Odia letters is masked from the first ASCII character, so the Odia letters stay visible.

`detect` and `mask` raise `ValueError` for an unknown type, or for a `min_confidence` outside 0 to 1.

The pattern for each type is in [PII detection and masking](../index.md#pii-detection-and-masking). The command is in [Command line](cli.md). `openodia pii --json` includes the raw matched text. Use `--mask` when the output should hold only the masked text.

## Next

- [API reference](../api/pii.md) for the signatures.
- [Applications](../application.md) for why masking a name is not the same as anonymising a person.
