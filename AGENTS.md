# AGENTS.md

`openodia` is a Python library and command-line tool for Odia (ଓଡ଼ିଆ) text: tokenize, normalize, clean, translate, detect language, generate names, summarize, remove stopwords, n-grams, word frequency and PII masking. Docs: https://openodia.soumendrak.com. Skill file: [skills/openodia/SKILL.md](skills/openodia/SKILL.md).

## Install

```bash
pip install openodia
uvx openodia --help
```

Requires Python 3.11 or newer.

## Use the CLI

- Text is a literal argument, `-` for UTF-8 stdin, or a file path with `--file`. A text argument is never treated as a path without `--file`.
- Every subcommand takes `--json`: one UTF-8 JSON document on stdout (Odia is not escaped), nothing else. Without it the output is plain text. `--json` on every subcommand needs a release newer than 0.1.14; 0.1.14 has it on `detect-language` only.
- Prefer `--json` when parsing. Line-based text output cannot represent tokens that contain spaces or newlines.

```console
$ openodia tokenize 'ରାମ ସୀତା ଘରକୁ ଯାଏ ।'
ରାମ
ସୀତା
ଘରକୁ
ଯାଏ
।
$ openodia tokenize --json 'ରାମ ସୀତା ଘରକୁ ଯାଏ ।'
{"tokens": ["ରାମ", "ସୀତା", "ଘରକୁ", "ଯାଏ", "।"]}
$ printf 'ରାମ ସୀତା ଘରକୁ ଯାଏ ।' | openodia tokenize - --json
{"tokens": ["ରାମ", "ସୀତା", "ଘରକୁ", "ଯାଏ", "।"]}
$ printf 'ରାମ ସୀତା ଘରକୁ ଯାଏ ।\n' > input.txt
$ openodia tokenize --file input.txt --json
{"tokens": ["ରାମ", "ସୀତା", "ଘରକୁ", "ଯାଏ", "।"]}
```

One example per subcommand:

```console
$ openodia tokenize --sentences --json 'ରାମ ସୀତା ଘରକୁ ଯାଏ । ସେ ଭଲ ଲୋକ ।'
{"tokens": ["ରାମ ସୀତା ଘରକୁ ଯାଏ", " ସେ ଭଲ ଲୋକ", ""]}
$ openodia normalize --form NFC --json 'ଡ଼'
{"text": "ଡ଼"}
$ openodia clean --odia-to-latin --json 'ଓଡ଼ିଶା  ୧୨୩'
{"text": "ଓଡ଼ିଶା 123"}
$ openodia translate --json 'good morning'
{"text": "ଶୁଭ ସକାଳ"}
$ openodia detect-language --json 'ରାମ ସୀତା ଘରକୁ ଯାଏ । ସେ ଭଲ ଲୋକ ।'
{"language": "odia", "confidence_score": 0.91}
$ openodia detect-language --json 'hello world'
{"language": "non-odia", "confidence_score": 1.0}
$ openodia detect-language --json ''
{}
$ openodia name --kind surname --count 2 --json
$ openodia summarize --json 'ରାମ ସୀତା ଘରକୁ ଯାଏ । ସେ ଭଲ ଲୋକ । ରାମ ଭଲ ପିଲା । ଓଡ଼ିଶା ଏକ ସୁନ୍ଦର ରାଜ୍ୟ । ପୁରୀରେ ଜଗନ୍ନାଥ ମନ୍ଦିର ଅଛି । ରାମ ପୁରୀକୁ ଯାଏ ।'
{"summary": "ରାମ ସୀତା ଘରକୁ ଯାଏ  ସେ ଭଲ ଲୋକ  ରାମ ଭଲ ପିଲା  ରାମ ପୁରୀକୁ ଯାଏ"}
$ openodia remove-stopwords --json 'ରାମ ସୀତା ଘରକୁ ଯାଏ । ସେ ଭଲ ଲୋକ ।'
{"tokens": ["ରାମ", "ସୀତା", "ଘରକୁ", "ଯାଏ", "ସେ", "ଭଲ", "ଲୋକ"]}
$ openodia remove-stopwords --get-str --json 'ରାମ ସୀତା ଘରକୁ ଯାଏ । ସେ ଭଲ ଲୋକ ।'
{"text": "ରାମ ସୀତା ଘରକୁ ଯାଏ ସେ ଭଲ ଲୋକ"}
$ openodia ngrams -n 2 --json 'ରାମ ସୀତା ଘରକୁ'
{"ngrams": [["ରାମ", "ସୀତା"], ["ସୀତା", "ଘରକୁ"]]}
$ openodia freq --top 2 --json 'ରାମ ସୀତା ରାମ'
{"counts": [{"token": "ରାମ", "count": 2}, {"token": "ସୀତା", "count": 1}]}
$ openodia pii --json 'ମୋ ଫୋନ ୯୮୭୬୫୪୩୨୧୦ ।'
{"entities": [{"type": "PHONE", "text": "୯୮୭୬୫୪୩୨୧୦", "start": 7, "end": 17, "confidence": 0.9}]}
$ openodia pii --mask --json 'ମୋ ଫୋନ ୯୮୭୬୫୪୩୨୧୦ ।'
{"text": "ମୋ ଫୋନ <PHONE> ।"}
```

`name` output is random, so only its shape is fixed: `{"names": ["...", "..."]}`.

`translate` answers English to Odia from an offline dictionary when it can. Every other pair calls Google Translate over the network, which can be rate limited (exit code 1) and refuses text over 5,000 characters. Language codes: `en`, `or` (Odia), and any code Google supports. `summarize` returns an empty summary for text with too few sentences.

`pii` finds Indian mobile numbers, emails, URLs, Aadhaar numbers, PAN and PIN codes, in Odia or ASCII digits, offline. `pii` needs a release newer than 0.1.14: `openodia pii` exits 2 on 0.1.14 and `import openodia.pii` fails there. It does not find names, street addresses, dates or amounts, so `pii --mask` output is not anonymised. Offsets count characters of the text the command read: `--file` drops a leading BOM and turns CRLF into LF; `-` (stdin) drops a leading BOM only and keeps any `\r` (a Linux or macOS pipe delivers `\r\n` unchanged, so offsets from `-` can differ from `--file` by one per line break); a literal argument is used as given. `http(s)://` and `www.` match in any letter case, so `HTTPS://` and `WWW.` are found. Matches that overlap merge into one span, typed by the longest match (a tie goes to the earlier of `EMAIL`, `URL`, `AADHAAR`, `PAN`, `PHONE`, `PINCODE`), so `--mask` never leaves half of a value visible. It repeats until nothing new appears (at most 10 passes), so masking its own output changes nothing unless the input chains more than 10 values glued together; past that, `mask` can still contain raw PII in its result. Expect false positives: any 10-digit number starting 6-9 is a `PHONE`, and any 12-digit number starting 2-9 is an `AADHAAR` at confidence 0.5. A local part over 64 characters, a bare domain without `http(s)://` or `www.`, and digits in other scripts are not found. A PIN code is only reported after `PIN`, `Pincode` or `ପିନ`. An Aadhaar-shaped number that fails its checksum is reported with confidence 0.5 (0.95 when it passes); `--min-confidence 0.9` drops it. `--type` (repeatable) limits the types: `PHONE`, `EMAIL`, `URL`, `AADHAAR`, `PAN`, `PINCODE`.

## JSON shapes

| Subcommand | stdout with `--json` |
| --- | --- |
| `tokenize` | `{"tokens": [string]}`; with `--sentences` segments may have leading spaces or be `""` |
| `normalize`, `clean`, `translate` | `{"text": string}` |
| `detect-language` | `{"language": "odia" or "non-odia", "confidence_score": number}`, or `{}` for empty input |
| `name` | `{"names": [string]}` |
| `summarize` | `{"summary": string}` |
| `remove-stopwords` | `{"tokens": [string]}`; with `--get-str` `{"text": string}` |
| `ngrams` | `{"ngrams": [[string]]}`, each inner list has `n` tokens |
| `freq` | `{"counts": [{"token": string, "count": integer}]}`, most frequent first |
| `pii` | `{"entities": [{"type": string, "text": string, "start": integer, "end": integer, "confidence": number}]}`, by position; `text` is the raw matched value, so plain `--json` output contains the PII itself. With `--mask`, `{"text": string}` holds only the masked text |

Without `--json`, `pii` prints `TYPE<TAB>START<TAB>END<TAB>TEXT` lines (or the masked text with `--mask`), `freq` prints `COUNT<TAB>TOKEN` lines, `ngrams` prints space-joined n-grams, and `detect-language` prints `odia (confidence: 0.91)` or `(empty input)`.

## Exit codes and errors

| Code | Meaning | stderr |
| --- | --- | --- |
| 0 | Success | empty |
| 1 | Runtime error: unreadable or non-UTF-8 file, non-UTF-8 stdin or text argument with `--json`, closed stdin, unsupported language code, Google Translate failure | `openodia: error: <message>` (at most 200 characters) |
| 2 | Usage error: unknown subcommand, missing text, bad option value | argparse usage, then `openodia <subcommand>: error: <message>`; `summarize --threshold 0` prints only `error: --threshold must be a positive number` |
| 141 | Output pipe closed early | empty |

With `--json`, errors still go to stderr and stdout stays empty. Without `--json`, how invalid UTF-8 in stdin or in the text argument is handled depends on the locale, so only `--json` guarantees valid UTF-8 output.

```console
$ openodia tokenize --file missing.txt 2>&1; echo "rc=$?"
openodia: error: [Errno 2] No such file or directory: 'missing.txt'
rc=1
$ openodia freq x --top -1 2>&1 >/dev/null | tail -n 1
openodia freq: error: argument --top: must be >= 0, got -1
```

## Output stability

Tests pin the JSON keys listed above for each subcommand, the exit codes 0, 1, 2 and 141 above, and the default text output of each subcommand for the inputs in `tests/test_cli.py` and `tests/test_cli_json.py`. Every `console` example in this file is run by `tests/test_agent_docs.py`. Nothing else is promised: error message wording, `name` output, Google Translate results and the exact scores or summaries the library computes can change.

## Develop

```bash
uv sync --all-extras
uv run ruff check
uv run ruff format --check
uv run bandit -r -lll ./openodia ./tests
uv run pytest --cov=openodia
uv lock --check
```

Conventions:

- Do not change `version` in `pyproject.toml` or `openodia/__init__.py`. A merge to `main` with a version PyPI does not have yet publishes a release.
- Write the failing test first; a behavior change without a test is incomplete.
- No new code comments, `# type: ignore` or `# pragma: no cover`. Name things so the code reads on its own.
- Put new features in their own module and keep a PR under about 400 changed lines.
- Do not change default CLI output; add a flag instead.
- Add a line to the Unreleased section of `CHANGELOG.md` for user-visible changes.
