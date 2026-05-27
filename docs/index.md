![image](cover-pic.png)

<h4 align="center">
  <a href="https://img.shields.io/badge/Python-3.10+-blue"><img alt="python 3.10+" src="https://img.shields.io/badge/Python-3.10+-blue"></a>
  <a href="https://github.com/soumendrak/openodia/actions/workflows/codecov.yml"><img alt="Code coverage" src="https://github.com/soumendrak/openodia/actions/workflows/codecov.yml/badge.svg"></a>
  <a href="https://github.com/soumendrak/openodia/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
  <a href="https://codecov.io/gh/soumendrak/openodia"><img alt="code coverage" src="https://codecov.io/gh/soumendrak/openodia/branch/main/graph/badge.svg?token=1TOQIKGDQ2"/></a>
  <a href="https://app.fossa.com/projects/git%2Bgithub.com%2Fsoumendrak%2Fopenodia?ref=badge_shield" alt="FOSSA Status"><img src="https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsoumendrak%2Fopenodia.svg?type=shield" alt="license"/></a>
  <a href="https://pepy.tech/project/openodia" alt="downloads"><img src="https://static.pepy.tech/personalized-badge/openodia?period=total&units=none&left_color=black&right_color=orange&left_text=Downloads"/></a>
</h4>

## About

- This documentation is about an open source Python programming language package built for Odia language.
- `openodia` is a Python package which contains various tools on Odia language.
- The short term goal of this package is to not make state-of-the-art methods, but to make tools which work.
- The documentation has been written to help you easily copy the code snippets and try out in your Python IDLE or iPython or Jupyter Notebook.

## Installation

- Set up the library from PyPI using the following command in your terminal or command prompt.
- Requires **Python 3.10 or higher**.
- The library is tested on Python 3.10, 3.11, 3.12, 3.13, and 3.14.
    
    ??? hint "Python Installation instruction"
        You can download Python from [Python official website](https://www.python.org/downloads/) and install on your system. 

### Using pip

```sh
pip install openodia
```

### Using uv (recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package installer and resolver.

```sh
# Install uv if you haven't already
pip install uv

# Install openodia
uv pip install openodia

# Or add to your project
uv add openodia
```

### From source

If you want to install from the source with latest changes:

```sh
git clone https://github.com/soumendrak/openodia.git
cd openodia
uv sync  # or: pip install -e .
```

## Features

The tools are available in Odia language.

- [x] [Odia Alphabets](#odia-alphabets)
- [x] [Generate random Odia names](#odia-names)
- [x] [Detect Odia Language](#detect-odia-language)
- [x] [Word Tokenizer](#word-tokenizer)
- [x] [Remove stopwords](#remove-stopwords)
- [x] [Google Translate](#translation)
- [x] [Automatic extractive text summarization](#automatic-extractive-text-summarization)
- [x] [Add Dictionary corpus](#offline-dictionary)
- [x] [Unicode normalization & clean](#unicode-normalization)
- [x] [Corpus statistics](#corpus-statistics)
- [x] [Syllabifier (akshara)](#syllabifier)
- [x] [Translation cache configuration](#translation-cache)
- [x] [Numbers, dates, and currency in words](#numbers-and-words)
- [x] [Sentence segmenter](#sentence-segmenter)


### :material-broom: Unicode normalization

- The same visible Odia string can be encoded in many byte sequences (e.g. precomposed vs decomposed nukta `ଡ଼`, stray ZWJ/ZWNJ from copy-paste, Latin digits mixed in with Odia).
- Normalize text before tokenizing, indexing, hashing, or comparing.

```python
from openodia import normalize, clean

# Pure Unicode normalization (NFC / NFD / NFKC / NFKD)
normalize("ଡ" + "଼")           # "ଡ଼"  (composed)
normalize("ଡ଼", form="NFD")    # "ଡ" + "଼"  (decomposed)

# Opinionated cleanup: NFC + strip ZWJ/ZWNJ + collapse whitespace
clean("  ନମ‌ସ୍କାର   ଓଡ଼ିଆ  ")
# "ନମସ୍କାର ଓଡ଼ିଆ"

# Optional digit conversion (off by default)
from openodia.text import CleanOptions
clean("ଆଜି 123 ବର୍ଷ", options=CleanOptions(latin_to_odia_digits=True))
# "ଆଜି ୧୨୩ ବର୍ଷ"

clean("ଆଜି ୧୨୩ ବର୍ଷ", options=CleanOptions(odia_to_latin_digits=True))
# "ଆଜି 123 ବର୍ଷ"
```

??? hint "`clean()` is idempotent"
    `clean(clean(x)) == clean(x)` always holds, so it is safe to apply repeatedly
    or sprinkle through a pipeline without compounding side-effects.


### :material-chart-bar: Corpus statistics

- N-grams, frequency distribution, collocations, and co-occurrence — pure-stdlib utilities for corpus exploration.
- All functions accept either a pre-tokenised `list[str]` or a raw string (auto-tokenised via `ud.word_tokenizer`).

```python
from openodia import FreqDist, ngrams, collocations, cooccurrence

tokens = "ରାମ ସୀତା ରାମ ଲକ୍ଷ୍ମଣ".split()

# N-grams (generator)
list(ngrams(tokens, 2))
# [('ରାମ', 'ସୀତା'), ('ସୀତା', 'ରାମ'), ('ରାମ', 'ଲକ୍ଷ୍ମଣ')]

# Frequency distribution — a Counter subclass with hapaxes / entropy / TTR.
fd = FreqDist(tokens)
fd.most_common(2)        # [('ରାମ', 2), ('ସୀତା', 1)]
fd.hapaxes()             # ['ସୀତା', 'ଲକ୍ଷ୍ମଣ']
fd.entropy()             # Shannon entropy (bits)
fd.ttr                   # type-token ratio

# PMI-scored bigram collocations.
collocations(tokens, top_k=5, min_count=1)
# [(('ରାମ', 'ଲକ୍ଷ୍ମଣ'), 1.0), ...]

# Co-occurrence within a window (symmetric by default).
cooccurrence(tokens, window=2)
# Counter({('ରାମ', 'ସୀତା'): 2, ...})
```

??? note "v1 scope"
    - `collocations` ships PMI scoring only. Log-likelihood and chi-square are easy follow-ups.
    - Plot helpers are intentionally out of scope to keep the base install free of matplotlib.

### :material-format-text-variant: Syllabifier

- Splits a word into **aksharas** (orthographic syllables) using the Odia Unicode block rules: independent vowels, consonant clusters joined by halant (`୍`), matras, modifiers, and nukta.
- Useful for TTS frontends, hyphenation/typography, character-level ML, and readability scoring.

```python
from openodia import syllable

syllable.split("ନମସ୍କାର")        # ['ନ', 'ମ', 'ସ୍କା', 'ର']
syllable.split("ଓଡ଼ିଆ")            # ['ଓ', 'ଡ଼ି', 'ଆ']
syllable.split("ବିଦ୍ୟାଳୟ")        # ['ବି', 'ଦ୍ୟା', 'ଳ', 'ୟ']

syllable.count("ବିଦ୍ୟାଳୟ")        # 4

syllable.hyphenate("ବିଦ୍ୟାଳୟ")    # 'ବି-ଦ୍ୟା-ଳ-ୟ'
syllable.hyphenate("ନମସ୍କାର ଓଡ଼ିଆ", separator="·")
# 'ନ·ମ·ସ୍କା·ର ଓ·ଡ଼ି·ଆ'
```

??? note "Round-trip property"
    `"".join(syllable.split(word)) == word` for any input — the splitter
    is a strict tokeniser, never modifying or normalising characters.


### :material-database-cog: Translation cache

- Translations are memoised in an LRU. Defaults to 10,000 entries in memory.
- Resize the cache, plug in a persistent disk backend, or inspect hit/miss counters.
- Environment variables `OPENODIA_CACHE_MAX_SIZE` and `OPENODIA_CACHE_DISK` set defaults at process start.

```python
from openodia import cache

cache.stats()
# {'hits': 0, 'misses': 0, 'size': 0, 'max_size': 10000, 'disk_size': 0}

# Resize the in-memory LRU.
cache.configure(max_size=50_000)

# Persist across runs (requires the [cache] extra: pip install openodia[cache]).
cache.configure(max_size=50_000, disk_path="~/.cache/openodia/translate")

cache.clear()
```

??? note "Disk persistence is opt-in"
    Disk persistence is gated behind the `[cache]` extra, which pulls in
    [`diskcache`](https://pypi.org/project/diskcache/). Calling
    `cache.configure(disk_path=...)` without the extra raises a clear
    `ImportError`. The base install has no new dependency.
### :material-numeric: Numbers and words

- Convert between integers and Odia words, in both **Indian** (lakh / crore) and **short** (million / billion / trillion) numbering scales.
- Verbalise dates, currency amounts, and ordinals.
- Bidirectional Odia ↔ ASCII digit conversion.

```python
from openodia import numbers

# Cardinal numbers
numbers.to_words(1234)
# 'ଏକ ହଜାର ଦୁଇ ଶହ ଚଉତିରିଶ'

numbers.to_words(12_34_567)            # Indian: lakh / crore
# 'ବାର ଲକ୍ଷ ଚଉତିରିଶ ହଜାର ପାଞ୍ଚ ଶହ ସତଷଠି'

numbers.to_words(1_000_000, scale="short")
# 'ଏକ ମିଲିୟନ'

numbers.to_words(-100)
# 'ଋଣାତ୍ମକ ଏକ ଶହ'

# Reverse direction
numbers.from_words("ଏକ ହଜାର ଦୁଇ ଶହ ଚଉତିରିଶ")  # 1234

# Ordinals (1..10 irregular, 11+ uses 'ତମ' suffix)
numbers.to_ordinal(3)          # 'ତୃତୀୟ'
numbers.to_ordinal(11)         # 'ଏଗାରତମ'

# Currency
numbers.to_words_currency(1500.50)
# 'ଏକ ହଜାର ପାଞ୍ଚ ଶହ ଟଙ୍କା ପଚାଶ ପଇସା'

# Date verbalisation
from datetime import date
numbers.to_words_date(date(2026, 5, 27))
# '<day ordinal> ମଇ, ଦୁଇ ହଜାର ଛବିଶ'

# Digit conversion
numbers.ascii_to_odia("2026")   # '୨୦୨୬'
numbers.odia_to_ascii("୨୦୨୬")   # '2026'
```

??? note "Number words 0..99"
    The Odia counting table below 100 lives at `openodia/numbers/_tables.py`
    as a single tuple of length 100. Native-speaker corrections land there
    and are picked up by every API in this module automatically.

### :material-call-split: Sentence segmenter

- Splits text into sentences on Odia (`।`, `॥`) and Latin (`.`, `?`, `!`, `…`) terminators.
- Decimal numbers (`୨.୫`, `2.5`) and common abbreviations (`ଡଃ`, `Dr.`, `e.g.`) do **not** trigger a split.
- Each sentence keeps its terminator by default.

```python
from openodia import sentences

sentences("ଆଜି ୨.୫ କୋଟି। ଆଗକୁ କଣ? ଭଲ ଦିନ!")
# ['ଆଜି ୨.୫ କୋଟି।', 'ଆଗକୁ କଣ?', 'ଭଲ ଦିନ!']

sentences("ଡଃ ସୁନୀତା ଆସିଲେ। ସେ କଲେଜରେ ପଢ଼ାନ୍ତି।")
# ['ଡଃ ସୁନୀତା ଆସିଲେ।', 'ସେ କଲେଜରେ ପଢ଼ାନ୍ତି।']

# Strict mode: only Odia terminators trigger splits.
sentences("Hi. ତୁମେ କେମିତି।", mode="strict")
# ['Hi. ତୁମେ କେମିତି।']

# Strip terminators
sentences("Hello. World!", keep_terminators=False)
# ['Hello', 'World']
```

??? hint "Extending the abbreviations list"
    `openodia.segment.ABBREVIATIONS` is a public tuple. Project-specific
    vocabulary (e.g. trade names, place abbreviations) can be added by
    extending it in a wrapper module.

??? note "Existing `ud.sentence_tokenizer` is unchanged"
    The pre-existing helper continues to behave exactly as before (splits
    on `" ।"` only). Adopt `openodia.sentences()` for new code.

### :material-format-letter-case: Odia alphabets 

- To get the Odia alphabets use the `alphabet` module

```python
from openodia import alphabet
alphabet.all_letters
'''
['ଁ', 'ଂ', 'ଃ', 'ଅ', 'ଆ', 'ଇ', 'ଈ', 'ଉ', 'ଊ', 'ଋ', 'ଌ', 'ଏ', 'ଐ', 'ଓ', 'ଔ', 
 'କ', 'ଖ', 'ଗ', 'ଘ', 'ଙ', 
 'ଚ', 'ଛ', 'ଜ', 'ଝ', 'ଞ', 
 'ଟ', 'ଠ', 'ଡ', 'ଢ', 'ଣ', 
 'ତ', 'ଥ', 'ଦ', 'ଧ', 'ନ', 
 'ପ', 'ଫ', 'ବ', 'ଭ', 'ମ', 
 'ଯ', 'ର', 'ଲ', 'ଳ', 'ଵ', 'ଶ', 'ଷ', 'ସ', 'ହ', 
 'ଡ଼', 'ଢ଼', 'ୟ', 'ୠ', 'ୡ', 
 '଼', 'ଽ', 'ା', 'ି', 'ୀ', 'ୁ', 'ୂ', 
 'ୃ', 'ୄ', 'େ', 'ୈ', 'ୋ', 'ୌ', '୍', 'ୖ', 'ୗ', 
 'ୢ', 'ୣ', '୦', '୧', '୨', '୩', '୪', '୫', '୬', '୭', '୮', '୯', 
 '୰', 'ୱ', '୲']
'''

alphabet.consonants
'''
['କ', 'ଖ', 'ଗ', 'ଘ', 'ଙ', 
 'ଚ', 'ଛ', 'ଜ', 'ଝ', 'ଞ', 
 'ଟ', 'ଠ', 'ଡ', 'ଢ', 'ଣ', 
 'ତ', 'ଥ', 'ଦ', 'ଧ', 'ନ', 
 'ପ', 'ଫ', 'ବ', 'ଭ', 'ମ', 
 'ଯ', 'ର', 'ଲ', 'ଳ', 'ଵ', 
 'ଶ', 'ଷ', 'ସ', 'ହ']
'''

alphabet.vowels

'''
['ଅ', 'ଆ', 'ଇ', 'ଈ', 'ଉ', 'ଊ', 'ଋ', 'ଌ', 'ଏ', 'ଐ', 'ଓ', 'ଔ']
'''

alphabet.numbers
'''
['୦', '୧', '୨', '୩', '୪', '୫', '୬', '୭', '୮', '୯']
'''

alphabet.matra
'''
['ଁ', 'ଂ', 'ଃ', '଼', 'ଽ', 'ା', 'ି', 'ୀ', 'ୁ', 'ୂ', 
 'ୃ', 'ୄ', 'େ', 'ୈ', 'ୋ', 'ୌ', '୍', 'ୖ', 'ୗ', '୰', 'ୱ', '୲']
'''
```

### :people_holding_hands_tone1: Odia names

- You can generate Odia names using the `name` module with the following syntax:

```python
from openodia import name
name.generate_names()
'''
['ଯଦୁମଣୀ ମାଢ଼ୀ', 'ବାସନ୍ତି ବ୍ରହ୍ମା', 'ପ୍ରବୀଣ ସିଂହ ମୁକ୍କିମ', 'ବୃନ୍ଦାବନ ଧଳ', 'ଅଶ୍ୱିନୀ କିଶୋର ଜଗଦେବ', 
 'ଶ୍ରୀଯୁକ୍ତ ଇରାଶିଷ ସେଠୀ', 'କୁମାରୀ ସୁମନ ସିଂଦେଓ', 'ସଲିଲ ଅଲ୍ଲୀ ଛତ୍ରିଆ', 'ଦିବାକରନାଥ ରାଧାରାଣୀ ଆଚାର୍ଯ୍ୟ', 'ଦୁର୍ଗା ସୁନ୍ଦରସୁର୍ଯ୍ୟା ପୁଟୀ']
'''

```
- By default, it will return ten randomly generated names. 
- If you want, you can generate more names by providing the number of names needed in the first argument.

```python
from openodia import name
name.generate_names(20)
'''
['ସାବିତ୍ରୀ ଧଳ', 'ଶ୍ରୀଯୁକ୍ତ ଉତ୍କଳ ପାଳ', 'ଯଦୁମଣି ସୁବାହୁ', 'ପ୍ରେମଲତା ପମ', 'ଗୁରୁ ପୃଷ୍ଟି', 
 'ଗୀତା ଦାସବର୍ମା', 'କୁମାରୀ ଦୁର୍ଗା ବ୍ରହ୍ମା', 'କୁମାରୀ ପୁପୁଲ ହେମ୍ବ୍ରମ', 'ମକର ସାଇ', 'ଲକ୍ଷ୍ମୀକାନ୍ତ ନନ୍ଦି', 
 'ଶ୍ରୀ ଦୀନବନ୍ଧୁ ଲୋକ', 'କୁମାରୀ ଜିନା ଗଜପତି', 'ମୃଣାଳ ଭୂଷଣ ଛତ୍ରିଆ', 'ସୁଧାଂଶୁମାଳିନୀ ସିଂହ ସାଲୁଜା', 'ସୁଧାଂଶୁମାଳିନୀ ମହାନନ୍ଦ', 
 'ସୁମନୀ ନାଥ', 'କୁମାରୀ ନୀତୁ ହିକ୍କା', 'ଶ୍ରୀମତୀ ଲୀଳା କାଡାମ୍', 'ସନାତନ କୁଅଁର', 'କୁମାରୀ କବି ଦାସନାୟକ']
'''

```
- In addition to this, you can create specific name parts like prefix, first name, middle name, surname, etc.
- By default you will get ten names. However, to get more number of results you can specify the number of names in the first argument.

```python
from openodia import name
name.generate_firstnames()
'''
['ଅନିରୁଦ୍ଧ', 'ଦେବରାଜ', 'ଆଶ୍ରିତ', 'ବଦ୍ରି', 'ସଦାଶିବ', 
 'ପ୍ରଦିପ୍ତ', 'ଧୃବ', 'ଶ୍ରୀନାଥ', 'ସ୍ନିତି', 'ପ୍ରକୃତି']
'''

name.generate_prefixes()
'''
['ଶ୍ରୀଯୁକ୍ତ', 'ଶ୍ରୀମତୀ', 'କୁମାରୀ', 'ଶ୍ରୀମାନ', 'ସୁଶ୍ରୀ', 'ଶ୍ରୀ']
'''

name.generate_middlenames()
'''
['ଲେଖା', 'ଶ୍ରୀ', 'ମାଧବ', 'କେତନ', 'ଯୋଶେଫ୍', 
 'କେଶରୀ', 'ଭୂଷଣ', 'ରାଧାରାଣୀ', 'ମାନସିଂହ', 'କିଶୋର']
'''

name.generate_surnames()
'''
['ପରିଜା', 'ରଣସିଂହ', 'ମହାପାତ୍ର', 'ରଥ', 'ମହନ୍ତ', 
 'ବେହେରା', 'ଦେଓ', 'ଧଳ', 'ଦିଆନ', 'ହିମିରିକା']
'''
```

### :material-text-box-search-outline: Detect Odia Language

- A binary language classification method used which will return if the input text is in Odia language or in any other non-Odia language. 
- Along with this a confidence score also returned. The score provides how confident the library is that it is Odia or Non-Odia.
- There is a `threshold` parameter to the method which can be configured to tune the confidence score threshold after which it will be regarded as Odia. The default value is 0.5.

```python
from openodia import ud
ud.detect_language("hey how are you?")
'''
{'language': 'non-odia', 'confidence_score': 1.0}
'''

ud.detect_language("hey how are you? ନ୍ୟାଚୁରାଲ ଲାଙ୍ଗୁଏଜ ପ୍ରୋସେସିଂ")
'''
{'language': 'odia', 'confidence_score': 0.66666}
'''

ud.detect_language(
    "hey how are you? ନ୍ୟାଚୁରାଲ ଲାଙ୍ଗୁଏଜ ପ୍ରୋସେସିଂ", 
    threshold=0.7)
'''
{'language': 'non-odia', 'confidence_score': 0.333333}
'''

ud.detect_language(
    "ନ୍ୟାଚୁରାଲ ଲାଙ୍ଗୁଏଜ ପ୍ରୋସେସିଂ ବା ପ୍ରାକୃତିକ ଭାଷା ପ୍ରକ୍ରିୟାକରଣ କଂପ୍ୟୁଟର ବିଜ୍ଞାନ ଏବଂ "\
    "ଆର୍ଟିଫିସିଆଲ ଇଣ୍ଟେଲିଜେନ୍ସର ସେହି ବିଭାଗକୁ କୁହାଯ ାଏ ଯାହା" \ 
    "ମନୁଷ୍ୟର ଭାଷାଗୁଡ଼ିକ ସହ କମ୍ପ୍ୟୁଟରର କଥାବାର୍ତ୍ତାକୁ ବୁଝାଇଥାଏ।")
'''
{'language': 'odia', 'confidence_score': 0.99404}
'''
```
- For more info on Odia language detection, please visit the blog post on this at [blog.soumendrak.com](https://blog.soumendrak.com/odia-language-detection).

### :material-set-split: Word Tokenizer

- To tokenize odia text into multiple words or tokens `word_tokenizer` module can be used.

```python
from openodia import ud
ud.word_tokenizer(
    "କ୍ୱାଣ୍ଟମ କମ୍ପ୍ୟୁଟିଙ୍ଗ, ହେଉଛି ଏକ ଉଦୀୟମାନ ହାର୍ଡ଼ୱେର ଏବଂ ସଫ୍ଟୱେରର ପ୍ରଯୁକ୍ତିବିଦ୍ୟା," \ 
    "ଯାହା କଠିନ ଗାଣିତିକ ସମସ୍ୟାଗୁଡ଼ିକର ସମାଧାନ ପାଇଁ ଉପ-ପାରମାଣବିକ ଘଟଣାଗୁଡ଼ିକର ଉପଯୋଗ କରିଥାଏ ।[୧]")
'''
['କ୍ୱାଣ୍ଟମ', 'କମ୍ପ୍ୟୁଟିଙ୍ଗ', 'ହେଉଛି', 'ଏକ', 'ଉଦୀୟମାନ', 'ହାର୍ଡ଼ୱେର', 'ଏବଂ', 
 'ସଫ୍ଟୱେରର', 'ପ୍ରଯୁକ୍ତିବିଦ୍ୟା', 'ଯାହା', 'କଠିନ', 'ଗାଣିତିକ', 'ସମସ୍ୟାଗୁଡ଼ିକର', 
 'ସମାଧାନ', 'ପାଇଁ', 'ଉପ', 'ପାରମାଣବିକ', 'ଘଟଣାଗୁଡ଼ିକର', 'ଉପଯୋଗ', 
 'କରିଥାଏ', '।', '୧']
'''
```

### :material-call-split: Sentence Tokenizer

- Tokenize a paragraph into multiple sentences.
- Only working on full stop.

```python
from openodia import ud
ud.sentence_tokenizer()
```

### :material-eye-remove: Remove stopwords

- Frequently occurring words in a language are called as _stopwords_. Using the below function you can remove the stopwords.
- Internally this method calls the `word_tokenize` method to get tokens from the text.
- As most of the time processing happens in list by default a list of strings will be returned.

```python
from openodia import ud
ud.remove_stopwords("ରାମ ଓ ସୀତା ଆମକୁ ଆଶୀର୍ବାଦ ଦେଇଛନ୍ତି")
'''
['ରାମ', 'ସୀତା', 'ଆମକୁ', 'ଆଶୀର୍ବାଦ']
'''

ud.remove_stopwords("ରାମ ଓ ସୀତା ଆମକୁ ଆଶୀର୍ବାଦ ଦେଇଛନ୍ତି ", get_str=True)
'''
'ରାମ ସୀତା ଆମକୁ ଆଶୀର୍ବାଦ'
'''
```
Here the stopwords `ଓ` and `ଦେଇଛନ୍ତି` are removed from the text.

#### Customising the stopword list

`STOPWORDS` is a `frozenset` you can extend or replace per call. For richer
workflows use the `Stopwords` class, which supports add / remove,
loading from a file, deriving from a corpus, and saving back to disk.

```python
from openodia import Stopwords, ud

# Start from the bundled list and tweak it.
sw = Stopwords.default().add("ପ୍ରାୟ").remove("ଓ")
ud.remove_stopwords("ରାମ ଓ ସୀତା", stopwords=sw)
# ['ରାମ', 'ଓ', 'ସୀତା']  — 'ଓ' kept because we removed it from the list

# Load a domain-specific list from disk.
legal = Stopwords.from_file("legal_stopwords.txt")
ud.remove_stopwords(article, stopwords=legal)

# Derive a list from corpus frequency.
auto = Stopwords.from_corpus(tokens, top_n=100)
auto.save("derived_stopwords.txt")
```

Any container supporting `token in stopwords` works — `Stopwords`,
`frozenset[str]`, `set[str]`, or `list[str]`. The bundled `STOPWORDS`
constant remains the default when the kwarg is omitted, so existing code
keeps working unchanged.

### :material-translate: Translation

- The translation module is a wrapper on top of Google Translate API.
- There are two translation methods provided:
    1. `odia_to_other_lang` and
    2. `other_lang_to_odia`

#### other_lang_to_odia

- As the name suggests this function can be used to translate from any other language to Odia language.
- If you are translating from any other language other than English, please provide the language code of it.

```python
from openodia import other_lang_to_odia
other_lang_to_odia("hello! feeling good?")
'''
'ନମସ୍କାର!ଭଲ ଲାଗୁଛି?'
'''

other_lang_to_odia("शेयर बाज़ार एक ऐसा बाज़ार है जहाँ कंपनियों के शेयर खरीदे-बेचे जा सकते हैं।", source_language_code="hi")
'''
'ଷ୍ଟକ୍ ମାର୍କେଟ୍ ହେଉଛି ଏକ ବଜାର ଯେଉଁଠାରେ କମ୍ପାନୀଗୁଡିକ କିଣାଯାଇପାରିବ |'
'''
```

#### odia_to_other_lang

- This function can be used to translate an Odia text into another language.
- The same language code you can choose from as provided above.
- By default, the function will translate to English language.

```python
from openodia import odia_to_other_lang
odia_to_other_lang("ନମସ୍କାର!ଭଲ ଲାଗୁଛି?")
'''
'Hello! Sounds good?'
'''
```
### :material-shovel: Automatic extractive text summarization

Extracts the important summary snippet of a given text.

```python
from openodia import WordFrequency
wf = WordFrequency(
        text="ଭାରତୀୟ ସର୍ବୋଚ୍ଚ ନ୍ୟାୟାଳୟ, ଭାରତର ଉଚ୍ଚତମ ନ୍ୟାୟିକ ଅନୁଷ୍ଠାନ ଅଟେ ଏବଂ ଭାରତୀୟ ସମ୍ବିଧାନ ଅଧୀନସ୍ଥ "
        "ସର୍ବୋଚ୍ଚ ନ୍ୟାୟାଳୟ ଅଟେ । "
        "ଏହା ସର୍ବ ବରିଷ୍ଠ ସାମ୍ବିଧାନିକ ନ୍ୟାୟାଳୟ ଅଟେ ଏବଂ ଏହି ନ୍ୟାୟିକ ପୁନରାବଲୋକନର କ୍ଷମତା ରହିଛି । "
        "ଭାରତର ମୁଖ୍ୟ ବିଚାରପତି ଏହାର ମୁଖ୍ୟ ଅଟନ୍ତି । ତତ୍ସହିତ ଏଥିରେ ସର୍ବାଧିକ ୩୪ ଜଣ ବିଚାରପତି ଅଛନ୍ତି । "
        "ମୁଖ୍ୟ, ଅପିଲୀୟ ତଥା ପରାମର୍ଶିକ ଆଦି ଅଧିକାରକ୍ଷେତ୍ର ମାଧ୍ୟମରେ ଏହାର ବିସ୍ତୃତ କ୍ଷମତା ରହିଛି । "
        "ଏହା ଭାରତରେ ସବୁଠାରୁ ଶକ୍ତିଶାଳୀ ଲୋକାନୁଷ୍ଠାନ ବୋଲି ଧରାଯାଇଅଛି । "
        "ଦେଶର ସାମ୍ବିଧାନିକ ନ୍ୟାୟାଳୟ ହୋଇଥିବାରୁ, ଏହା ମୁଖ୍ୟତଃ ସଙ୍ଘର ବିଭିନ୍ନ ଉଚ୍ଚ ନ୍ୟାୟାଳୟ ତଥା "
        "ଅନ୍ୟାନ୍ୟ ନ୍ୟାୟାଳୟ ଓ "
        "ଟ୍ରିବ୍ୟୁନାଲମାନଙ୍କର ରାୟ ବିରୁଦ୍ଧରେ ଅପିଲ୍ ନିଏ । "
        "ଏହା ନାଗରିକମାନଙ୍କର ମୌଳିକ ଅଧିକାରର ରକ୍ଷାକରେ ଏବଂ ବିଭିନ୍ନ ସରକାରୀ ଅଧିକାରୀ ତଥା "
        "ଦେଶରେ କେନ୍ଦ୍ର ସରକାର ବନାମ ରାଜ୍ୟ ସରକାର କିମ୍ବା ଗୋଟିଏ ରାଜ୍ୟ ସରକାର ବନାମ ଅନ୍ୟ ରାଜ୍ୟ ସରକାର "
        "ମଧ୍ୟରେ ବିବାଦର ସମାଧାନ କରେ । "
        "ଏକ ପରାମର୍ଶଦାତା ହିସାବରେ, ଏହା ଭାରତୀୟ ସମ୍ବିଧାନ ଅନୁସାରେ ରାଷ୍ଟ୍ରପତିଙ୍କଦ୍ୱାରା ସୂଚୀତ ବିଭିନ୍ନ ବିଷୟବସ୍ତୁ "
        "ଉପରେ ଶୁଣାଣି କରିଥାଏ । ")

wf.get_summary() # Auto threshold calculation
'''
'ଭାରତୀୟ ସର୍ବୋଚ୍ଚ ନ୍ୟାୟାଳୟ, ଭାରତର ଉଚ୍ଚତମ ନ୍ୟାୟିକ ଅନୁଷ୍ଠାନ ଅଟେ ଏବଂ ଭାରତୀୟ ସମ୍ବିଧାନ ଅଧୀନସ୍ଥ ସର୍ବୋଚ୍ଚ ନ୍ୟାୟାଳୟ ଅଟେ
ଏହା ସର୍ବ ବରିଷ୍ଠ ସାମ୍ବିଧାନିକ ନ୍ୟାୟାଳୟ ଅଟେ ଏବଂ ଏହି ନ୍ୟାୟିକ ପୁନରାବଲୋକନର କ୍ଷମତା ରହିଛି 
ଭାରତର ମୁଖ୍ୟ ବିଚାରପତି ଏହାର ମୁଖ୍ୟ ଅଟନ୍ତି  ତତ୍ସହିତ ଏଥିରେ ସର୍ବାଧିକ ୩୪ ଜଣ ବିଚାରପତି ଅଛନ୍ତି 
ମୁଖ୍ୟ, ଅପିଲୀୟ ତଥା ପରାମର୍ଶିକ ଆଦି ଅଧିକାରକ୍ଷେତ୍ର ମାଧ୍ୟମରେ ଏହାର ବିସ୍ତୃତ କ୍ଷମତା ରହିଛି  
ଏହା ଭାରତରେ ସବୁଠାରୁ ଶକ୍ତିଶାଳୀ ଲୋକାନୁଷ୍ଠାନ ବୋଲି ଧରାଯାଇଅଛି  
ଦେଶର ସାମ୍ବିଧାନିକ ନ୍ୟାୟାଳୟ ହୋଇଥିବାରୁ, ଏହା ମୁଖ୍ୟତଃ ସଙ୍ଘର ବିଭିନ୍ନ ଉଚ୍ଚ ନ୍ୟାୟାଳୟ ତଥା ଅନ୍ୟାନ୍ୟ ନ୍ୟାୟାଳୟ ଓ 
ଟ୍ରିବ୍ୟୁନାଲମାନଙ୍କର ରାୟ ବିରୁଦ୍ଧରେ ଅପିଲ୍ ନିଏ  
ଏହା ନାଗରିକମାନଙ୍କର ମୌଳିକ ଅଧିକାରର ରକ୍ଷାକରେ ଏବଂ ବିଭିନ୍ନ ସରକାରୀ ଅଧିକାରୀ ତଥା ଦେଶରେ କେନ୍ଦ୍ର ସରକାର ବନାମ 
ରାଜ୍ୟ ସରକାର କିମ୍ବା ଗୋଟିଏ ରାଜ୍ୟ ସରକାର ବନାମ ଅନ୍ୟ ରାଜ୍ୟ ସରକାର ମଧ୍ୟରେ ବିବାଦର ସମାଧାନ କରେ  
ଏକ ପରାମର୍ଶଦାତା ହିସାବରେ, ଏହା ଭାରତୀୟ ସମ୍ବିଧାନ ଅନୁସାରେ ରାଷ୍ଟ୍ରପତିଙ୍କଦ୍ୱାରା ସୂଚୀତ ବିଭିନ୍ନ ବିଷୟବସ୍ତୁ ଉପରେ ଶୁଣାଣି କରିଥାଏ'
'''

wf.get_summary(threshold=3.0) # higher the threshold lesser the summary text
'''
'ଭାରତୀୟ ସର୍ବୋଚ୍ଚ ନ୍ୟାୟାଳୟ, ଭାରତର ଉଚ୍ଚତମ ନ୍ୟାୟିକ ଅନୁଷ୍ଠାନ ଅଟେ ଏବଂ ଭାରତୀୟ ସମ୍ବିଧାନ ଅଧୀନସ୍ଥ ସର୍ବୋଚ୍ଚ ନ୍ୟାୟାଳୟ ଅଟେ  
ଏହା ସର୍ବ ବରିଷ୍ଠ ସାମ୍ବିଧାନିକ ନ୍ୟାୟାଳୟ ଅଟେ ଏବଂ ଏହି ନ୍ୟାୟିକ ପୁନରାବଲୋକନର କ୍ଷମତା ରହିଛି  
ଦେଶର ସାମ୍ବିଧାନିକ ନ୍ୟାୟାଳୟ ହୋଇଥିବାରୁ, ଏହା ମୁଖ୍ୟତଃ ସଙ୍ଘର ବିଭିନ୍ନ ଉଚ୍ଚ ନ୍ୟାୟାଳୟ ତଥା ଅନ୍ୟାନ୍ୟ ନ୍ୟାୟାଳୟ ଓ 
ଟ୍ରିବ୍ୟୁନାଲମାନଙ୍କର ରାୟ ବିରୁଦ୍ଧରେ ଅପିଲ୍ ନିଏ  
ଏହା ନାଗରିକମାନଙ୍କର ମୌଳିକ ଅଧିକାରର ରକ୍ଷାକରେ ଏବଂ ବିଭିନ୍ନ ସରକାରୀ ଅଧିକାରୀ ତଥା ଦେଶରେ କେନ୍ଦ୍ର ସରକାର ବନାମ 
ରାଜ୍ୟ ସରକାର କିମ୍ବା ଗୋଟିଏ ରାଜ୍ୟ ସରକାର ବନାମ ଅନ୍ୟ ରାଜ୍ୟ ସରକାର ମଧ୍ୟରେ ବିବାଦର ସମାଧାନ କରେ'
'''

```

### :book: Offline Dictionary

- An offline dictionary will be downloaded as soon as you install this library.
- Therefore, when you translate from English to Odia words/phrases it will hit the offline dictionary first, if not found it will go for the Google translate API.
- Google Translate API responses have been cached, therefore from the 2nd call onwards on the same term(s) it will fetch fast from the local in-memory cache.
- We have used [LRU (Least Recently Used) cache](https://realpython.com/lru-cache-python/) with a maximum size of 10000.

???+note "English to Odia translation Workflow"
    Therefore, we have three flows on English to Odia dictionary translation:
    
    1. English text --> Check in Offline dictionary --> Found --> Return result
    2. English text --> Check in Offline dictionary --> Not Found --> Check in Cache --> Found --> Return result from Cache
    3. English text --> Check in Offline dictionary --> Not Found --> Check in Cache --> Not Found --> Hit Google Translate API --> Update the Cache --> Return result


## :bug: Known Issues

- There are few issues in the code an be found [here](https://github.com/soumendrak/openodia/issues).
- Contributions are highly welcomed. :pray_tone2:

## Roadmap

In the upcoming future the following features will be implemented in the package.

- [ ] Add English-Odia Parallel corpus
- [ ] Add Odia Monolingual corpus
- [ ] Add NER dataset of places, actors, etc. 
- [ ] Robust paragraph to sentence tokenizer covering edge cases
- [ ] Stemming tool
- [ ] Customized stopword support
- [ ] Add OdiaBert
- [ ] Improve the CI/CD pipeline

???+quote
    "In my dream of the 21st century for the State, I would have young men and women who put the interest of the State before them. They will have pride in themselves, confidence in themselves. They will not be at anybody’s mercy, except their own selves. By their brains, intelligence and capacity, they will recapture the history of Kalinga." - [Biju Pattnaik](https://en.wikipedia.org/wiki/Biju_Patnaik)

<!-- Citation -->
<hr>
To cite this page, please use:

```bibtex
@misc{OpenOdia,
    author       = {Soumendra Kumar Sahoo},
    title        = {OpenOdia Documentation},
    howpublished = {\url{https://www.openodia.soumendrak.com/}},
    year         = {2021}
}
```
