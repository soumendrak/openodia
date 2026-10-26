# Command line

Installing the package adds an `openodia` command. Each subcommand wraps one library function, reads its text from an argument, a file or stdin, and prints plain text or JSON. Every example on this page is run by the test suite.

Exit codes, error messages and the JSON shape of every subcommand are specified in [AGENTS.md](https://github.com/soumendrak/openodia/blob/main/AGENTS.md). This page covers how to use the commands.

## Where the text comes from

The `text` argument is literal text. Pass `-` to read stdin, or add `--file` to treat the argument as the path of a UTF-8 file.

```console
$ openodia tokenize "ରାମ ସୀତା ଘରକୁ ଯାଏ । ସେ ଭଲ"
ରାମ
ସୀତା
ଘରକୁ
ଯାଏ
।
ସେ
ଭଲ
$ echo "ରାମ ଓ ସୀତା" | openodia remove-stopwords -
ରାମ
ସୀତା
$ printf "ରାମ ସୀତା" > input.txt
$ openodia tokenize input.txt
input
txt
$ openodia tokenize input.txt --file
ରାମ
ସୀତା
```

!!! note "Gotcha: a file name without `--file` is just text"
    `openodia tokenize input.txt` tokenizes the string `input.txt`, as the third command above shows, even when that file exists.

## Text and JSON output

The default output is meant for reading and for `grep`, `sort` and `wc`. Add `--json` for one JSON document on stdout.

```console
$ openodia tokenize "ରାମ ସୀତା" --json
{"tokens": ["ରାମ", "ସୀତା"]}
$ openodia detect-language "ନମସ୍କାର"
odia (confidence: 1.0)
$ openodia detect-language "ନମସ୍କାର" --json
{"language": "odia", "confidence_score": 1.0}
```

## Subcommands

| Command | Library call | Useful options |
| --- | --- | --- |
| `tokenize` | `ud.word_tokenizer`, `ud.sentence_tokenizer` | `--sentences` |
| `normalize` | `normalize` | `--form {NFC,NFD,NFKC,NFKD}` |
| `clean` | `clean` | `--latin-to-odia`, `--odia-to-latin`, `--keep-zwj`, `--keep-zwnj`, `--keep-whitespace` |
| `translate` | `universal_translation` and the offline dictionary | `--from`, `--to` |
| `detect-language` | `ud.detect_language` | `--threshold` |
| `name` | `name.generate_*` | `--kind {full,first,middle,surname,prefix}`, `--count` |
| `summarize` | `WordFrequency` | `--threshold` |
| `remove-stopwords` | `ud.remove_stopwords` | `--get-str` |
| `ngrams` | `ngrams` | `-n` |
| `freq` | `FreqDist` | `--top` |

```console
$ openodia clean "ଆଜି 2026" --latin-to-odia
ଆଜି ୨୦୨୬
$ openodia remove-stopwords "ରାମ ଓ ସୀତା" --get-str
ରାମ ସୀତା
$ openodia ngrams "ରାମ ସୀତା ଲକ୍ଷ୍ମଣ" -n 2
ରାମ ସୀତା
ସୀତା ଲକ୍ଷ୍ମଣ
$ openodia freq "ରାମ ସୀତା ରାମ" --top 1
2	ରାମ
$ openodia translate "good morning"
ଶୁଭ ସକାଳ
```

`freq` prints the count, a tab, then the token. `translate` answers English to Odia from the [offline dictionary](translation.md) when it can and uses Google Translate for everything else, so it needs the network then.

## Errors

A usage error such as a missing argument, or two options that exclude each other, exits with code 2 and prints the usage text. A runtime error such as a missing file prints `openodia: error: ...` and exits with code 1.

```console
$ openodia clean "x" --latin-to-odia --odia-to-latin 2>&1 | tail -n 1
openodia clean: error: argument --odia-to-latin: not allowed with argument --latin-to-odia
$ openodia tokenize missing.txt --file 2>&1 || echo "exit code $?"
openodia: error: [Errno 2] No such file or directory: 'missing.txt'
exit code 1
```

## Next

- [Text processing](text-processing.md) for the same operations from Python.
- [Documentation](../index.md) for installing and a tour of every feature.
