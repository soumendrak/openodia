# Corpus statistics and summarization

Count and rank words, find word pairs that belong together, and pull the key sentences out of a text. Every example on this page is run by the test suite.

## N-grams

`ngrams` yields tuples of `n` consecutive tokens, lazily. It takes a list of tokens or a raw string, which is tokenized with `ud.word_tokenizer`.

```pycon
>>> from openodia import ngrams
>>> tokens = "ରାମ ସୀତା ରାମ ଲକ୍ଷ୍ମଣ".split()
>>> list(ngrams(tokens, 2))
[('ରାମ', 'ସୀତା'), ('ସୀତା', 'ରାମ'), ('ରାମ', 'ଲକ୍ଷ୍ମଣ')]
>>> list(ngrams("ରାମ ସୀତା ଘରକୁ", 2))
[('ରାମ', 'ସୀତା'), ('ସୀତା', 'ଘରକୁ')]
>>> list(ngrams(tokens, 5))
[]
>>> list(ngrams(tokens, 0))
Traceback (most recent call last):
  ...
ValueError: n must be >= 1, got 0
```

!!! note "Gotcha: errors appear when you iterate"
    `ngrams` is a generator, so the `ValueError` for `n < 1` is raised on the first `next()`, not when you call it. Wrap it in `list()` or loop over it to see the error.

## Frequency distribution

`FreqDist` is a `collections.Counter` with a few extras. An empty distribution reports `0.0` for `ttr` and `entropy()` instead of dividing by zero.

```pycon
>>> from openodia import FreqDist
>>> fd = FreqDist(tokens)
>>> fd.most_common(2)
[('ରାମ', 2), ('ସୀତା', 1)]
>>> fd.hapaxes()
['ସୀତା', 'ଲକ୍ଷ୍ମଣ']
>>> fd.total_count, fd.ttr
(4, 0.75)
>>> fd.entropy()
1.5
>>> FreqDist().ttr
0.0
```

`hapaxes()` are the tokens seen once, `ttr` is the type-token ratio (distinct tokens divided by all tokens) and `entropy()` is the Shannon entropy in bits.

## Collocations

`collocations` ranks bigrams by pointwise mutual information (PMI). Bigrams seen fewer than `min_count` times are skipped, and the default is 2.

```pycon
>>> from openodia import collocations
>>> [(pair, round(score, 3)) for pair, score in collocations(tokens, top_k=2, min_count=1)]
[(('ରାମ', 'ସୀତା'), 1.415), (('ସୀତା', 'ରାମ'), 1.415)]
>>> collocations(tokens)
[]
```

!!! note "Gotcha: a short text yields no results"
    The second call returns `[]` because no bigram in the four-token sample occurs twice. Lower `min_count` for small inputs. PMI also favors rare pairs, so keep `min_count` at 2 or more on real corpora.

## Co-occurrence

`cooccurrence` counts how often two tokens appear within `window` positions of each other. By default pairs are sorted so `(a, b)` and `(b, a)` count together. Pass `symmetric=False` to keep the order.

```pycon
>>> from openodia import cooccurrence
>>> cooccurrence(tokens, window=1)
Counter({('ରାମ', 'ସୀତା'): 2, ('ରାମ', 'ଲକ୍ଷ୍ମଣ'): 1})
>>> cooccurrence(tokens, window=1, symmetric=False)
Counter({('ରାମ', 'ସୀତା'): 1, ('ସୀତା', 'ରାମ'): 1, ('ରାମ', 'ଲକ୍ଷ୍ମଣ'): 1})
```

## Summarization

`WordFrequency` is an extractive summarizer. After stopwords are removed it keeps the words that occur **more than** `threshold` times, then returns every sentence that contains one of them. When you leave `threshold` out, it is the number of tokens divided by the number of distinct tokens.

```pycon
>>> from openodia import WordFrequency
>>> text = "ରାମ ସୀତା ଘରକୁ ଯାଏ । ସେ ଭଲ ଲୋକ । ରାମ ଭଲ ପିଲା । ଓଡ଼ିଶା ଏକ ସୁନ୍ଦର ରାଜ୍ୟ । ପୁରୀରେ ଜଗନ୍ନାଥ ମନ୍ଦିର ଅଛି । ରାମ ପୁରୀକୁ ଯାଏ ।"
>>> wf = WordFrequency(text)
>>> wf.get_summary()
'ରାମ ସୀତା ଘରକୁ ଯାଏ  ସେ ଭଲ ଲୋକ  ରାମ ଭଲ ପିଲା  ରାମ ପୁରୀକୁ ଯାଏ'
>>> wf.get_summary(threshold=2)
'ରାମ ସୀତା ଘରକୁ ଯାଏ  ରାମ ଭଲ ପିଲା  ରାମ ପୁରୀକୁ ଯାଏ'
>>> wf.get_summary(threshold=3)
''
```

A higher threshold gives a shorter summary, and a threshold above every word count gives an empty string.

!!! note "Gotchas"
    - The summary drops the `।` terminators and joins the kept sentences with two spaces.
    - A word matches a sentence by substring, so `ରାମ` also selects a sentence that only contains a longer word starting with `ରାମ`.
    - `threshold=0` means "not given" and falls back to the automatic value.
    - Sentences are split with `ud.sentence_tokenizer`, so the text must use ` ।` (a space, then the full stop) between sentences.

## Next

- [Translation and cache](translation.md).
- [API reference: statistics](../api/stats.md) and [summarization](../api/summarization.md).
