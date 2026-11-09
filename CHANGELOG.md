# Changelog

## Unreleased

- Add `openodia.pii` and `openodia pii` to find or mask phone numbers, emails, URLs, Aadhaar (Verhoeff checksum), PAN and PIN codes in Odia or ASCII digits. Names, addresses, dates and amounts are not detected. Overlapping matches merge into one span, so for every detected value `mask` never leaves part of it visible (see the limits below), and `mask` repeats until stable so masking its output changes nothing (up to 10 glued values). Detection is linear in the input size.
- Every CLI subcommand accepts `--json` and prints one UTF-8 JSON document on stdout; default text output is unchanged by `--json`. With `--json`, invalid UTF-8 in stdin or in the text argument is an `openodia: error:` with exit code 1; `detect-language --json` used to pass it through in 0.1.14.
- Docs for AI agents: `AGENTS.md`, `skills/openodia/SKILL.md` and `llms.txt` on the docs site.
- Docs: generated API reference and six usage guides (text, script and names, numbers, analysis, translation, command line) on the docs site, with every guide example checked by the test suite. The `docs` and `dev` extras now include `mkdocstrings[python]`; the library's runtime dependencies are unchanged.
- **Behaviour change, changes default output:** `ud.sentence_tokenizer` now splits after `।`, `॥`, `?` and `!`, with or without a space after them; it used to split only on `" ।"`. Each sentence is trimmed and keeps its terminator, a terminator with no words of its own joins its neighbour, and empty input gives `[]`. A `?` or `!` directly followed by an ASCII letter, digit or `=&%#/_` (`a?id=5`, `Yahoo!Mail`) is not a boundary. `["ଏକ ଦୁଇ", " ତିନି ଚାରି", ""]` becomes `["ଏକ ଦୁଇ ।", "ତିନି ଚାରି ।"]`. This changes the default text and `--json` output of `openodia tokenize --sentences` (no leading spaces, no empty last entry, `[]` for empty input; text mode prints no blank line for empty input) and of `openodia summarize` and `WordFrequency.get_summary` (sentences keep their `।` and are joined with one space, and text containing `?`, `!`, `॥` or a danda without a leading space is split into different sentences, so the chosen sentences can differ). This overrides the "output is unchanged" statement in the `--json` bullet above for these two subcommands.
- Async translation: `odia_to_other_lang_async`, `other_lang_to_odia_async`, `universal_translation_async` and `translate_batch` with bounded concurrency, optional retries and `return_exceptions`.
- `TranslationCache` can be shared between threads (it can still be pickled and deep-copied). Concurrent `get`, `set` and `clear` calls no longer raise `KeyError` or lose hit and miss counts, and a `get` that reads the disk cache while a `set` or `clear` runs no longer puts the old or cleared value back in memory. A disk write or clear that raises leaves the cache usable. Pickling or copying a cache while another thread writes to it takes a consistent snapshot. Behaviour change: `copy.copy(cache)` now gets its own memory entries instead of sharing them with the original.
- `openodia.cache.get_cache()` builds its singleton under a lock, so threads making the first call together share one cache (before, `OPENODIA_CACHE_DISK` could give each its own, losing entries and counts).
- The package ships `py.typed` (PEP 561) and is fully type-annotated (mypy strict), so type checkers see the narrowed `remove_stopwords` return types.
- `import openodia` and `openodia --help` no longer import `faker`, `deep_translator`, `requests` or `bs4`; they load on first use of `name.generate_names` or a Google translation (a cached result or an offline-dictionary hit loads nothing). `import openodia` is about 2.5x faster in this repo's measurements. The public API is unchanged.
- `import openodia` no longer configures logging. It used to call `logging.basicConfig` with a Rich handler, which attached a root handler in the host application and printed log lines (with local variables in tracebacks) to stdout. Library logs now go to the `openodia` logger, which has a `NullHandler`; configure logging in your application to see them. The `openodia` CLI output is unchanged.
- An invalid `name_type` in `name.generate_firstnames` logs an error without the meaningless `NoneType: None` traceback line (the `ValueError` is unchanged).
- `openodia translate` and `other_lang_to_odia` find offline-dictionary words when the text has leading or trailing whitespace. Input from `--file` or stdin ends in a newline, so it used to miss the dictionary and call Google Translate, which failed whenever Google rate limited the request.

### Added

- `openodia.phonetic`: Odia-adapted phonetic matching (`soundex`, `metaphone`,
  and `similarity`).

- `openodia.roman`: Odia romanisation (`to_roman` / `from_roman`) with the
  ISO 15919, Hunterian and ITRANS schemes.

- Hunterian `from_roman` decodes no Roman spelling as anusvara, candrabindu or visarga: an `n` or `h` that is not part of a longer letter such as `ng` or `kh` decodes as the consonant `ନ` or `ହ`. Odia `ଂ`, `ଁ` and `ଃ` in the input pass through. `ନ୍` endings and clusters such as `ନ୍ସ` and `ଙ୍କ` round-trip; anusvara and visarga round-trip through the explicit marks of ISO 15919 and ITRANS.

- `to_roman` writes a nukta after any consonant except ଡ and ଢ as `·` in ISO 15919 and a backtick in ITRANS, and drops it in Hunterian. ଡ଼ and ଢ଼ keep their own letters in all three schemes: `ṛ`/`ṛh` in ISO 15919, `.D`/`.Dh` in ITRANS, and `r`/`rh` in Hunterian (where plain ଡ and ଢ give `d`/`dh`). `from_roman` reads each scheme's mark back as the nukta, so `to_roman(..., reversible=True)` now quotes a literal `·` (ISO 15919) or backtick (ITRANS) instead of passing it through.

### Behaviour note

- By default, `to_roman` returns non-Odia text exactly as given, so its output
  no longer round-trips text that mixes Odia with other text (for example
  `to_roman("କi")` gives `kai`, which `from_roman` reads as `କୈ`). Callers
  who need an exact round trip should pass `reversible=True`
  (`to_roman("କi", reversible=True)` gives `ka:{i:}`).
- In `ISO15919` and `ITRANS`, `from_roman(to_roman(text, scheme,
  reversible=True), scheme)` gives back `text` with each run of Odia characters
  (U+0B00-U+0B7F) in NFC and all other characters unchanged. NFC Odia therefore
  comes back with the same code points, including vowel signs, viramas and
  nuktas that follow no consonant or follow ZWJ/ZWNJ.
- In all three schemes, each run of Odia characters (U+0B00-U+0B7F) in the
  output of `from_roman` is in NFC, including Odia passed through or quoted in
  the input, so U+0B5C gives U+0B21 U+0B3C. Non-Odia characters that
  `from_roman` does not decode are left as given, except that `ISO15919` applies
  NFC to its input outside quotes.

## 0.1.14 (2026-10-26)

- `python -m openodia` now runs the CLI.
- Add CLI `--version`, UTF-8 stdin handling, and concise file/encoding errors.
- File input now requires `--file`; existing filenames passed without it are literal text.
- `openodia translate` reports Google rate limits, unsupported language codes and text over 5,000 characters as a single `openodia: error:` line instead of a traceback.
- UTF-8 byte order marks are ignored in `--file` input, stdin and `Stopwords.from_file`, which now defaults to `encoding="utf-8-sig"` (files without a BOM read as before).
- The CLI exits quietly on a closed pipe (status 141), reports closed stdin and invalid `OPENODIA_CACHE_*` values as one-line errors, and names argument types plainly in error messages.
- Docs: `alphabet.matras`, two-decimal confidence scores and a working `ud.sentence_tokenizer` example.
