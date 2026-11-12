# Changelog

## Unreleased

## 0.2.0 (2026-11-13)

### Highlights

- Phonetic matching in `openodia.phonetic` (`soundex`, `metaphone`, and `similarity`): https://github.com/soumendrak/openodia/pull/226
- Odia romanisation in `openodia.roman` (`to_roman` / `from_roman`) with the ISO 15919, Hunterian and ITRANS schemes: https://github.com/soumendrak/openodia/pull/227
- Cross-script Indic transliteration in `openodia.indic` (for example Odia to Devanagari): https://github.com/soumendrak/openodia/pull/228
- Sandhi split and join in `openodia.sandhi` (`split` and `join`): https://github.com/soumendrak/openodia/pull/299
- PII detection and masking in `openodia.pii` and `openodia pii`: https://github.com/soumendrak/openodia/pull/281
- `--json` on every CLI subcommand: https://github.com/soumendrak/openodia/pull/278
- Async translation and `translate_batch` with bounded concurrency: https://github.com/soumendrak/openodia/pull/284
- **Behaviour change, changes default output:** `ud.sentence_tokenizer` now splits after `।`, `॥`, `?` and `!`: https://github.com/soumendrak/openodia/pull/293
- `TranslationCache` and `openodia.cache.get_cache()` are thread-safe: https://github.com/soumendrak/openodia/pull/296
- `openodia translate` and `other_lang_to_odia` find offline-dictionary words when the text has leading or trailing whitespace: https://github.com/soumendrak/openodia/pull/294
- `import openodia` and `openodia --help` no longer import `faker`, `deep_translator`, `requests` or `bs4`: https://github.com/soumendrak/openodia/pull/292
- `import openodia` no longer configures logging: https://github.com/soumendrak/openodia/pull/290
- The package ships `py.typed` and is fully type-annotated (mypy strict): https://github.com/soumendrak/openodia/pull/280 and https://github.com/soumendrak/openodia/pull/283
- Docs: generated API reference and usage guides: https://github.com/soumendrak/openodia/pull/289 and https://github.com/soumendrak/openodia/pull/297
- Docs for AI agents: `AGENTS.md`, `skills/openodia/SKILL.md` and `llms.txt` on the docs site: https://github.com/soumendrak/openodia/pull/278

### Known limits

- Sandhi: the splitter knows 74 lemmas. `split` returns at most two known lemmas, so it does not unpack a longer compound (for example `join(["ଲୋକ", "ସଭା", "ଗୃହ"])` is `ଲୋକସଭାଗୃହ`, and `split` of that string does not return three parts). `split` takes one word; a spaced phrase such as `ବିଦ୍ୟା ଆଳୟ` is returned unchanged. `join` can still fold more than two parts.
- Hunterian is intentionally lossy (no diacritics) and ignores `reversible`. It drops vowel length, so `to_roman("ନମସ୍କାର", "Hunterian")` is `namaskara` and `from_roman` of that spelling is `ନମସ୍କର`, not `ନମସ୍କାର`. Odia digits become ASCII `0`-`9` even when `reversible=True`. Hunterian `from_roman` decodes no Roman spelling as anusvara, candrabindu or visarga. `ନ୍` endings and clusters such as `ନ୍ସ` and `ଙ୍କ` do round-trip. In ISO 15919 and ITRANS, `from_roman(to_roman(text, scheme, reversible=True), scheme)` gives back the text with each run of Odia characters in NFC.
- `pii` does not detect names, addresses, dates or amounts, so masked text can still identify a person.
- English to Odia is served from the bundled offline dictionary when the phrase is in it; every other translation pair calls Google Translate over the network, which can be rate limited and refuses text over 5,000 characters.

- Add `openodia.sandhi` to split an Odia compound into the words sandhi joined (`split`) and to join those parts (`join`). A known lemma, or a word that does not split into two known words, is returned unchanged. `split` and `join` NFC-normalize, so for a compound the splitter accepts `join(split(word))` equals the NFC form of that word. `openodia.sandhi` needs a release newer than 0.1.14: `import openodia.sandhi` fails on 0.1.14.
- Add `openodia.pii` and `openodia pii` to find or mask phone numbers, emails, URLs, Aadhaar (Verhoeff checksum), PAN and PIN codes in Odia or ASCII digits. Names, addresses, dates and amounts are not detected. Overlapping matches merge into one span, so for every detected value `mask` never leaves part of it visible (see the limits below), and `mask` repeats until stable so masking its output changes nothing (up to 10 glued values). Detection is linear in the input size.
- Every CLI subcommand accepts `--json` and prints one UTF-8 JSON document on stdout; default text output is unchanged by `--json`. With `--json`, invalid UTF-8 in stdin or in the text argument is an `openodia: error:` with exit code 1; `detect-language --json` used to pass it through in 0.1.14.
- Docs for AI agents: `AGENTS.md`, `skills/openodia/SKILL.md` and `llms.txt` on the docs site.
- Docs: generated API reference and six usage guides (text, script and names, numbers, analysis, translation, command line) on the docs site, with every guide example checked by the test suite. The `docs` and `dev` extras now include `mkdocstrings[python]`; the library's runtime dependencies are unchanged.
- Docs: a getting started page, guides for transliteration and PII, API pages for `pii`, `indic`, async translation, and `STOPWORDS`, plus a changelog page and a contributing page. Docs search suggests matches and highlights the terms. Getting started says `।` is its own token only when a space precedes it. The translation guide says a padded English phrase hits the offline dictionary only on a release newer than 0.1.14.
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
- `openodia.indic`: transliterate between Brahmic Indic scripts. A composition-excluded nukta letter is consonant + nukta when the target has those parts, except Gurmukhi flap RRA and a target LLA, SHA, or YYA, which stay one letter. Odia WA stays when the target has no WA. Bengali writes VA as BA. A Malayalam chillu expands to consonant + virama.

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
