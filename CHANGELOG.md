# Changelog

## Unreleased

- `python -m openodia` now runs the CLI.
- Add CLI `--version`, UTF-8 stdin handling, and concise file/encoding errors.
- File input now requires `--file`; existing filenames passed without it are literal text.

### Added

- `openodia.roman`: Odia romanisation (`to_roman` / `from_roman`) with the
  ISO 15919, Hunterian and ITRANS schemes.

- Hunterian `from_roman` always reads `n` and `h` as the consonants `ନ` and `ହ`, so `ନ୍` endings and clusters such as `ନ୍ସ` and `ଙ୍କ` round-trip; anusvara and visarga round-trip through the explicit marks of ISO 15919 and ITRANS.

- `to_roman` writes a nukta after any consonant except ଡ and ଢ as `·` in ISO 15919 and a backtick in ITRANS, and drops it in Hunterian. ଡ଼ and ଢ଼ keep their own letters in all three schemes: `ṛ`/`ṛh` in ISO 15919, `.D`/`.Dh` in ITRANS, and `r`/`rh` in Hunterian (where plain ଡ and ଢ give `d`/`dh`). `from_roman` reads each scheme's mark back as the nukta, so `to_roman(..., reversible=True)` now quotes a literal `·` (ISO 15919) or backtick (ITRANS) instead of passing it through.

### Behaviour note

- By default, `to_roman` returns non-Odia text exactly as given, so its output
  no longer round-trips text that mixes Odia with other text (for example
  `to_roman("କi")` gives `kai`, which `from_roman` reads as `କୈ`). Callers
  who need an exact round trip should pass `reversible=True`
  (`to_roman("କi", reversible=True)` gives `ka:{i:}`).
