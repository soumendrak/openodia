---
name: openodia
description: Process Odia (ଓଡ଼ିଆ) text with the openodia command-line tool. Use when a task needs to tokenize, normalize, clean, translate, detect the language of, summarize, remove stopwords from, count words or n-grams in, or generate names from Odia text, and you want machine-readable output.
---

# openodia

Run it without installing: `uvx openodia <subcommand> ...`, or `pip install openodia` and run `openodia`. Python 3.11+.

Subcommands: `tokenize`, `normalize`, `clean`, `translate`, `detect-language`, `name`, `summarize`, `remove-stopwords`, `ngrams`, `freq`.

Rules:

- Text is a literal argument, `-` for stdin, or a path with `--file`. Input is UTF-8.
- Add `--json` and parse stdout as one JSON document. Errors go to stderr and stdout stays empty. `--json` on every subcommand needs a release newer than 0.1.14.
- Exit codes: 0 success, 1 runtime error (`openodia: error: ...` on stderr), 2 usage error.
- `translate` works offline only for English to Odia dictionary hits; other pairs need the network and can be rate limited.

```console
$ openodia tokenize --json 'ରାମ ସୀତା ଘରକୁ ଯାଏ ।'
{"tokens": ["ରାମ", "ସୀତା", "ଘରକୁ", "ଯାଏ", "।"]}
$ printf 'ରାମ ସୀତା ଘରକୁ ଯାଏ ।' | openodia tokenize - --json
{"tokens": ["ରାମ", "ସୀତା", "ଘରକୁ", "ଯାଏ", "।"]}
$ printf 'ରାମ ସୀତା ଘରକୁ ଯାଏ ।\n' > input.txt
$ openodia detect-language --file input.txt --json
{"language": "odia", "confidence_score": 0.88}
$ openodia clean --odia-to-latin --json 'ଓଡ଼ିଶା  ୧୨୩'
{"text": "ଓଡ଼ିଶା 123"}
$ openodia translate --json 'good morning'
{"text": "ଶୁଭ ସକାଳ"}
$ openodia ngrams -n 2 --json 'ରାମ ସୀତା ଘରକୁ'
{"ngrams": [["ରାମ", "ସୀତା"], ["ସୀତା", "ଘରକୁ"]]}
$ openodia freq --top 2 --json 'ରାମ ସୀତା ରାମ'
{"counts": [{"token": "ରାମ", "count": 2}, {"token": "ସୀତା", "count": 1}]}
```

JSON keys by subcommand: `tokenize` and `remove-stopwords` give `tokens` (`text` with `remove-stopwords --get-str`); `normalize`, `clean` and `translate` give `text`; `detect-language` gives `language` and `confidence_score` (`{}` for empty input); `name` gives `names`; `summarize` gives `summary`; `ngrams` gives `ngrams`; `freq` gives `counts`. Full reference with every subcommand's example: [AGENTS.md](https://github.com/soumendrak/openodia/blob/main/AGENTS.md).
