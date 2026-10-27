# Changelog

## Unreleased

- Every CLI subcommand accepts `--json` and prints one UTF-8 JSON document on stdout; default text output is unchanged by `--json`. With `--json`, invalid UTF-8 in stdin or in the text argument is an `openodia: error:` with exit code 1; `detect-language --json` used to pass it through in 0.1.14.
- Docs for AI agents: `AGENTS.md`, `skills/openodia/SKILL.md` and `llms.txt` on the docs site.
- **Behaviour change, changes default output:** `ud.sentence_tokenizer` now splits after `।`, `॥`, `?` and `!`, with or without a space after them; it used to split only on `" ।"`. Each sentence is trimmed and keeps its terminator, a terminator with no words of its own joins its neighbour, and empty input gives `[]`. A `?` or `!` directly followed by an ASCII letter, digit or `=&%#/_` (`a?id=5`, `Yahoo!Mail`) is not a boundary. `["ଏକ ଦୁଇ", " ତିନି ଚାରି", ""]` becomes `["ଏକ ଦୁଇ ।", "ତିନି ଚାରି ।"]`. This changes the default text and `--json` output of `openodia tokenize --sentences` (no leading spaces, no empty last entry, `[]` for empty input; text mode prints no blank line for empty input) and of `openodia summarize` and `WordFrequency.get_summary` (sentences keep their `।` and are joined with one space, and text containing `?`, `!`, `॥` or a danda without a leading space is split into different sentences, so the chosen sentences can differ). This overrides the "output is unchanged" statement in the `--json` bullet above for these two subcommands.
- The package ships `py.typed` (PEP 561) and is fully type-annotated (mypy strict), so type checkers see the narrowed `remove_stopwords` return types.
- `import openodia` and `openodia --help` no longer import `faker`, `deep_translator`, `requests` or `bs4`; they load on first use of `name.generate_names` or a Google translation (a cached result or an offline-dictionary hit loads nothing). `import openodia` is about 2.5x faster in this repo's measurements. The public API is unchanged.
- `import openodia` no longer configures logging. It used to call `logging.basicConfig` with a Rich handler, which attached a root handler in the host application and printed log lines (with local variables in tracebacks) to stdout. Library logs now go to the `openodia` logger, which has a `NullHandler`; configure logging in your application to see them. The `openodia` CLI output is unchanged.
- An invalid `name_type` in `name.generate_firstnames` logs an error without the meaningless `NoneType: None` traceback line (the `ValueError` is unchanged).

## 0.1.14 (2026-10-26)

- `python -m openodia` now runs the CLI.
- Add CLI `--version`, UTF-8 stdin handling, and concise file/encoding errors.
- File input now requires `--file`; existing filenames passed without it are literal text.
- `openodia translate` reports Google rate limits, unsupported language codes and text over 5,000 characters as a single `openodia: error:` line instead of a traceback.
- UTF-8 byte order marks are ignored in `--file` input, stdin and `Stopwords.from_file`, which now defaults to `encoding="utf-8-sig"` (files without a BOM read as before).
- The CLI exits quietly on a closed pipe (status 141), reports closed stdin and invalid `OPENODIA_CACHE_*` values as one-line errors, and names argument types plainly in error messages.
- Docs: `alphabet.matras`, two-decimal confidence scores and a working `ud.sentence_tokenizer` example.
