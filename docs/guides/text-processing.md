# Text processing

Tokenize, split into sentences, remove stopwords, normalize and detect the language of Odia text. Every example on this page is run by the test suite, so the output shown is what the current release prints.

## Tokenize words

`ud.word_tokenizer` splits on whitespace and ASCII punctuation. The Odia full stop `।` is kept as its own token because it is not in the separator set.

```pycon
>>> from openodia import ud
>>> text = "ରାମ ସୀତା ଘରକୁ ଯାଏ । ସେ ଭଲ ଲୋକ ।"
>>> ud.word_tokenizer(text)
['ରାମ', 'ସୀତା', 'ଘରକୁ', 'ଯାଏ', '।', 'ସେ', 'ଭଲ', 'ଲୋକ', '।']
>>> ud.word_tokenizer("")
[]
```

!!! note "Gotcha: the hyphen is a separator"
    `ud.word_tokenizer("ଉପ-ପାରମାଣବିକ")` returns two tokens. If you need hyphenated words kept whole, split on whitespace yourself with `str.split()`.

## Split into sentences

Two helpers exist and they behave differently.

`sentences` is the one to use for new code. It understands Odia (`।`, `॥`) and Latin (`.`, `?`, `!`) terminators and does not split on decimals or abbreviations.

```pycon
>>> from openodia import sentences
>>> sentences(text)
['ରାମ ସୀତା ଘରକୁ ଯାଏ।', 'ସେ ଭଲ ଲୋକ।']
>>> sentences("ଆଜି ୨.୫ କୋଟି ଟଙ୍କା। ଆଗକୁ କଣ?")
['ଆଜି ୨.୫ କୋଟି ଟଙ୍କା।', 'ଆଗକୁ କଣ?']
>>> sentences("ଡଃ ସୁନୀତା ଆସିଲେ। ସେ କଲେଜରେ ପଢ଼ାନ୍ତି।")
['ଡଃ ସୁନୀତା ଆସିଲେ।', 'ସେ କଲେଜରେ ପଢ଼ାନ୍ତି।']
>>> sentences("Hi. ତୁମେ କେମିତି।", mode="strict")
['Hi. ତୁମେ କେମିତି।']
>>> sentences("Hello. World!", keep_terminators=False)
['Hello', 'World']
```

`ud.sentence_tokenizer` splits after `।`, `॥`, `?` and `!`, with or without a space after them. It trims each sentence, keeps its terminator and returns `[]` for empty text. It does not split on `.`.

```pycon
>>> ud.sentence_tokenizer(text)
['ରାମ ସୀତା ଘରକୁ ଯାଏ ।', 'ସେ ଭଲ ଲୋକ ।']
```

!!! note "Gotcha: `sentences` removes the space before `।`"
    `sentences(text)` returns `'ରାମ ସୀତା ଘରକୁ ଯାଏ।'` for input `'ରାମ ସୀତା ଘରକୁ ଯାଏ ।'`. The terminator is attached to the sentence and the space before it is dropped.

## Remove stopwords

`ud.remove_stopwords` accepts raw text or a list of tokens. It returns a list of tokens, or one string when `get_str=True`. The default list is `openodia.STOPWORDS`, a `frozenset`.

```pycon
>>> ud.remove_stopwords("ଏହା ଏକ ସୁନ୍ଦର ଘର")
['ଏକ', 'ସୁନ୍ଦର', 'ଘର']
>>> ud.remove_stopwords(["ଏହା", "ଏକ", "ସୁନ୍ଦର", "ଘର"], get_str=True)
'ଏକ ସୁନ୍ଦର ଘର'
>>> from openodia import STOPWORDS
>>> type(STOPWORDS).__name__, len(STOPWORDS)
('frozenset', 63)
```

Passing a `str` tokenizes it first. The default list includes the full stop `।`, so the `।` tokens are dropped as well:

```pycon
>>> ud.remove_stopwords(text)
['ରାମ', 'ସୀତା', 'ଘରକୁ', 'ଯାଏ', 'ସେ', 'ଭଲ', 'ଲୋକ']
```

### Custom stopword lists

`Stopwords` is a mutable collection you can start from the default, a file, or a corpus. `add` and `remove` return the same object, so calls chain.

```pycon
>>> from openodia import Stopwords
>>> sw = Stopwords.default()
>>> "ଓ" in sw
True
>>> _ = sw.add("ରାମ").remove("ଓ")
>>> "ଓ" in sw, "ରାମ" in sw
(False, True)
>>> ud.remove_stopwords(text, stopwords=sw)
['ସୀତା', 'ଘରକୁ', 'ଯାଏ', 'ସେ', 'ଭଲ', 'ଲୋକ']
>>> small = Stopwords(["ରାମ"])
>>> ud.remove_stopwords(text, stopwords=small)
['ସୀତା', 'ଘରକୁ', 'ଯାଏ', '।', 'ସେ', 'ଭଲ', 'ଲୋକ', '।']
```

`stopwords=` also accepts a plain `set`, `frozenset` or `list`.

`Stopwords.from_corpus(tokens, top_n=100)` builds a list from the most frequent tokens of your own corpus, `Stopwords.from_file(path)` reads one word per line, and `save(path)` writes the list back. `coverage(tokens)` returns the fraction of tokens that are stopwords:

```pycon
>>> round(sw.coverage(ud.word_tokenizer(text)), 3)
0.333
```

## Normalize and clean

The same visible string can have several encodings. `normalize` applies a Unicode normalization form (NFC by default). `clean` applies NFC, removes zero-width joiners and collapses whitespace.

```pycon
>>> from openodia import normalize, clean
>>> normalize("ଡ" + "଼") == "ଡ଼"
True
>>> normalize("ଡ଼", form="NFD") == "ଡ" + "଼"
True
>>> clean("  ଓଡ଼ିଆ   ଭାଷା  ")
'ଓଡ଼ିଆ ଭାଷା'
>>> clean("ନମ" + "\u200c" + "ସ୍କାର") == "ନମସ୍କାର"
True
```

Digit conversion is off by default. Turn it on with `CleanOptions`:

```pycon
>>> from openodia.text import CleanOptions
>>> clean("ଆଜି 123 ବର୍ଷ", options=CleanOptions(latin_to_odia_digits=True))
'ଆଜି ୧୨୩ ବର୍ଷ'
>>> clean("ଆଜି ୧୨୩ ବର୍ଷ", options=CleanOptions(odia_to_latin_digits=True))
'ଆଜି 123 ବର୍ଷ'
>>> clean(clean("  ଓଡ଼ିଆ  ")) == clean("  ଓଡ଼ିଆ  ")
True
```

!!! note "Gotcha: the two digit options are mutually exclusive"
    Setting both `latin_to_odia_digits` and `odia_to_latin_digits` raises `ValueError`.

## Detect the language

`ud.detect_language` reports `odia` when more than `threshold` (default 0.5) of the non-space characters are in the Odia Unicode block, otherwise `non-odia`. The score is rounded to two decimals. Empty input returns `{}` and logs a warning.

```pycon
>>> ud.detect_language(text)
{'language': 'odia', 'confidence_score': 0.91}
>>> ud.detect_language("hello world")
{'language': 'non-odia', 'confidence_score': 1.0}
>>> ud.detect_language("ରାମ hello", threshold=0.9)
{'language': 'non-odia', 'confidence_score': 0.62}
```

!!! note "Gotcha: script, not language"
    This is a character-ratio check. Text in another language written in the Odia script scores `odia`, and Odia written in Latin letters scores `non-odia`.

## Next

- [Analysis guide](analysis.md) for summaries and corpus statistics.
- [API reference: tokenizing and stopwords](../api/tokenizing.md), [text](../api/text.md) and [sentence segmentation](../api/segment.md).
