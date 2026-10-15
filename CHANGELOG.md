# Changelog

## Unreleased

- `python -m openodia` now runs the CLI.
- Add CLI `--version`, UTF-8 stdin handling, and concise file/encoding errors.
- File input now requires `--file`; existing filenames passed without it are literal text.

### Added

- `openodia.roman`: Odia romanisation (`to_roman` / `from_roman`) with the
  ISO 15919, Hunterian and ITRANS schemes.

- Hunterian `from_roman` reads `n` and `h` after a finished vowel as anusvara and visarga (`an` → `ଅଂ`, `duh` → `ଦୁଃ`) when the next token is not a vowel.

### Behaviour note

- By default, `to_roman` returns non-Odia text exactly as given, so its output
  no longer round-trips text that mixes Odia with other text (for example
  `to_roman("କi")` gives `kai`, which `from_roman` reads as `କୈ`). Callers
  who need an exact round trip should pass `reversible=True`
  (`to_roman("କi", reversible=True)` gives `ka:{i:}`).
