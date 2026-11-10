# Transliterate Odia

Convert Odia to another Indic script, or to Latin letters. Both conversions run offline, and the same input always gives the same output.

`indic` and `roman` need a release newer than 0.1.14. From a source checkout, `uv run python` can import them. Every example on this page is run by the test suite.

## Convert between Indic scripts

`indic.transliterate` changes only characters that belong to `from_script`. Every other character stays. The names you can pass are `indic.SCRIPTS`.

```pycon
>>> from openodia import indic
>>> indic.SCRIPTS
('devanagari', 'bengali', 'assamese', 'gurmukhi', 'gujarati', 'odia', 'tamil', 'telugu', 'kannada', 'malayalam')
>>> indic.transliterate("ଓଡ଼ିଆ", from_script="odia", to_script="devanagari")
'ओड़िआ'
>>> indic.transliterate("नमस्ते", from_script="devanagari", to_script="odia")
'ନମସ୍ତେ'
>>> indic.transliterate("file କ", from_script="odia", to_script="devanagari")
'file क'
```

The same script on both sides returns the text unchanged. An unknown name raises `ValueError`.

```pycon
>>> indic.transliterate("ଓଡ଼ିଆ", from_script="odia", to_script="odia")
'ଓଡ଼ିଆ'
>>> indic.transliterate("କ", from_script="nope", to_script="odia")
Traceback (most recent call last):
  ...
ValueError: unknown from_script 'nope'; supported: ('devanagari', 'bengali', 'assamese', 'gurmukhi', 'gujarati', 'odia', 'tamil', 'telugu', 'kannada', 'malayalam')
```

A letter with no counterpart stays as it is, and some pairs do not round-trip.

```pycon
>>> indic.transliterate("ଖ", from_script="odia", to_script="tamil")
'ଖ'
>>> indic.transliterate("ୱ", from_script="odia", to_script="devanagari")
'ୱ'
>>> indic.transliterate("व", from_script="devanagari", to_script="bengali")
'ব'
>>> indic.transliterate("ব", from_script="bengali", to_script="devanagari")
'ब'
```

`ଖ` stays because Tamil has no letter for that Odia consonant. Odia `ୱ` (WA) stays because the other scripts have no WA. Devanagari `व` (VA) is written as Bengali BA, and that Bengali letter comes back as Devanagari BA.

## Write Latin letters

`roman.to_roman` writes Latin letters. `roman.from_roman` reads them back. The schemes are `ISO15919`, `Hunterian`, and `ITRANS`.

```pycon
>>> from openodia import roman
>>> roman.to_roman("ଓଡ଼ିଆ", "ISO15919")
'ōṛiā'
>>> roman.to_roman("ଓଡ଼ିଆ", "Hunterian")
'oria'
>>> roman.to_roman("ଓଡ଼ିଆ", "ITRANS")
'o.DiA'
>>> roman.from_roman(roman.to_roman("ଓଡ଼ିଆ", "ISO15919"), "ISO15919")
'ଓଡ଼ିଆ'
```

Hunterian drops vowel length, so reading a Hunterian spelling does not put that length back. Hunterian and ITRANS write Odia digits as ASCII digits. Hunterian still does that when `reversible=True`.

```pycon
>>> roman.from_roman("namaskara", "Hunterian")
'ନମସ୍କର'
>>> roman.to_roman("୨୦୨୬", "ITRANS")
'2026'
>>> roman.to_roman("୨୦୨୬", "Hunterian", reversible=True)
'2026'
```

Characters outside the Odia block are copied through, unless you pass `reversible=True`. `to_roman("କi")` returns `kai`, which is not a reversible spelling of that string. `reversible=True` quotes the non-Odia part so `from_roman` can return it. Hunterian ignores `reversible`. An unknown scheme raises `ValueError`.

```pycon
>>> roman.to_roman("କi")
'kai'
>>> roman.to_roman("କi", reversible=True)
'ka:{i:}'
>>> roman.from_roman(roman.to_roman("କi", reversible=True), "ISO15919")
'କi'
>>> roman.to_roman("କ", "nope")
Traceback (most recent call last):
  ...
ValueError: unknown scheme 'nope'; supported: ('ISO15919', 'Hunterian', 'ITRANS')
```

## Next

- [Indic API](../api/indic.md) and [Romanisation API](../api/roman.md).
- [Script, syllables and names](script-and-names.md) for the Odia character lists.
