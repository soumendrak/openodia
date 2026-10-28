# Script, syllables and names

The Odia character inventory, a syllable splitter, and a generator of Odia names. Every example on this page is run by the test suite.

## Alphabet

`alphabet` exposes the Odia Unicode block as plain `list` objects of single characters: `all_letters`, `vowels`, `consonants`, `matras` (vowel signs and other combining marks), `numbers` and `punctuations`.

```pycon
>>> from openodia import alphabet
>>> alphabet.vowels
['ଅ', 'ଆ', 'ଇ', 'ଈ', 'ଉ', 'ଊ', 'ଋ', 'ଌ', 'ଏ', 'ଐ', 'ଓ', 'ଔ']
>>> len(alphabet.consonants), len(alphabet.numbers)
(34, 10)
>>> "କ" in alphabet.consonants, "କ" in alphabet.vowels
(True, False)
>>> alphabet.matras[:6]
['ଁ', 'ଂ', 'ଃ', '଼', 'ଽ', 'ା']
```

!!! note "Gotcha: `matras` includes more than vowel signs"
    The list also holds the candrabindu, anusvara, visarga, nukta, avagraha and virama, plus the ai length mark `ୖ`, the au length mark `ୗ`, the isshar `୰`, the letter wa `ୱ` and the fraction sign `୲`. It is the set of combining marks and signs, not only the matras of the textbook chart.

!!! note "Gotcha: the lists are shared"
    Each attribute is one list object for the whole process. Copy it with `list(alphabet.vowels)` before you sort or mutate it.

A common use is counting how much of a string is Odia script:

```pycon
>>> odia = set(alphabet.all_letters)
>>> sum(ch in odia for ch in "ଓଡ଼ିଆ ଭାଷା abc")
9
```

## Syllables

`syllable.split` breaks a word into orthographic syllables: a consonant with its vowel sign, or a conjunct (consonant + virama + consonant) with its vowel sign. `count` returns how many there are and `hyphenate` joins them with a separator.

```pycon
>>> from openodia import syllable
>>> syllable.split("ନମସ୍କାର")
['ନ', 'ମ', 'ସ୍କା', 'ର']
>>> syllable.split("ପ୍ରଥମ")
['ପ୍ର', 'ଥ', 'ମ']
>>> syllable.count("ବିଦ୍ୟାଳୟ")
4
>>> syllable.hyphenate("ବିଦ୍ୟାଳୟ")
'ବି-ଦ୍ୟା-ଳ-ୟ'
>>> syllable.hyphenate("ଓଡ଼ିଆ ଭାଷା", separator="·")
'ଓ·ଡ଼ି·ଆ ଭା·ଷା'
>>> syllable.split("")
[]
```

!!! note "Gotcha: the split is orthographic"
    `split` follows the written script, so it does not model schwa deletion or pronunciation. Characters that are not Odia are returned one by one, and spaces are returned as their own item.

## Names

`name` produces random Odia names. Part generators sample without replacement, and asking for more than the list holds returns the whole list.

```pycon
>>> from openodia import name
>>> len(name.generate_firstnames(count=3))
3
>>> len(name.generate_surnames(count=4))
4
>>> len(name.generate_prefixes(count=2)), len(name.generate_middlenames(count=2))
(2, 2)
>>> set(name.generate_firstnames(count=3, name_type="male")) <= set(name.generate_firstnames(count=10**6, name_type="male"))
True
>>> len(name.generate_names(count=5))
5
```

`name_type` accepts `"male"`, `"female"` or `"unisex"` (case-insensitive). An empty value mixes all first names. Anything else raises `ValueError`:

```pycon
>>> name.generate_firstnames(name_type="robot")
Traceback (most recent call last):
  ...
ValueError: Invalid name_type provided
```

!!! note "Gotcha: two sources, two behaviours"
    The part generators (`generate_firstnames`, `generate_surnames`, ...) sample from lists shipped in the package with `random.sample`. `generate_names` instead calls the `or_IN` locale of [Faker](https://faker.readthedocs.io/) once per name and does not de-duplicate.

For use cases such as masking and anonymizing names in a text, see [Applications](../application.md).

## Next

- [Numbers guide](numbers.md) for digits and number words.
- [API reference: alphabet](../api/alphabet.md), [syllables](../api/syllable.md) and [names](../api/names.md).
