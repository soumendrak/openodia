# Getting started

Install openodia, split a sentence into words, and normalize a character. The [guides](guides/text-processing.md) cover each task. The [API reference](api/text.md) lists the signatures. Every example on this page is run by the test suite.

## Install

Python 3.11 or newer is required.

```bash
pip install openodia
```

To work from a clone of this repository:

```bash
git clone https://github.com/soumendrak/openodia.git
cd openodia
uv sync --all-extras
uv run python
```

## Tokenize a sentence

`ud.word_tokenizer` splits on whitespace, on ASCII punctuation, and on `୲` and `—`. The Odia full stop `।` is not a separator. A space before `।` makes it its own token. With no space, `।` stays on the word.

```pycon
>>> from openodia import ud
>>> ud.word_tokenizer("ରାମ ସୀତା ଘରକୁ ଯାଏ ।")
['ରାମ', 'ସୀତା', 'ଘରକୁ', 'ଯାଏ', '।']
>>> ud.word_tokenizer("ରାମ ସୀତା ଘରକୁ ଯାଏ।")
['ରାମ', 'ସୀତା', 'ଘରକୁ', 'ଯାଏ।']
>>> ud.word_tokenizer("ରାମ।ସୀତା")
['ରାମ।ସୀତା']
>>> ud.word_tokenizer("a୲b")
['a', 'b']
>>> ud.word_tokenizer("a—b")
['a', 'b']
```

## Normalize text

The same letters can be stored as one code point or as a base letter plus a nukta. `normalize` returns one Unicode form. `NFC` is the default.

```pycon
>>> from openodia import normalize
>>> normalize("ଡ" + "଼")
'ଡ଼'
>>> normalize("ଡ଼", form="NFD") == "ଡ" + "଼"
True
```

## Next

- [Text processing](guides/text-processing.md) for sentences, stopwords, and language detection.
- [Command line](guides/cli.md) for the `openodia` command.
- [Transliteration](guides/transliteration.md) and [personal identifiers](guides/pii.md).
