"""Command-line interface for the openodia package.

Run ``openodia --help`` to see all subcommands.

The CLI is intentionally thin: each subcommand maps to an existing
Python entry point in the package. New subcommands can be added in
:func:`build_parser` and :func:`main` without touching anything else.
"""

from __future__ import annotations

import argparse
import errno
import math
import json
import os
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------


def _read_input(value: str, *, file: bool = False) -> str:
    """Read an explicit UTF-8 file, stdin (``-``), or literal text."""
    if file:
        return Path(value).read_text(encoding="utf-8-sig")
    if value == "-":
        if sys.stdin is None:
            raise OSError("standard input is closed")
        return sys.stdin.read().removeprefix("\ufeff")
    return value


def _int_at_least(minimum: int) -> Callable[[str], int]:
    """argparse ``type`` for integers >= ``minimum``."""

    def parse(raw: str) -> int:
        try:
            value = int(raw)
        except ValueError:
            raise argparse.ArgumentTypeError(f"must be an integer, got {raw!r}") from None
        if value < minimum:
            raise argparse.ArgumentTypeError(f"must be >= {minimum}, got {value}")
        return value

    return parse


def _unit_float(raw: str) -> float:
    """argparse ``type`` for a finite float in [0, 1]."""
    try:
        value = float(raw)
    except ValueError:
        raise argparse.ArgumentTypeError(f"must be a number between 0 and 1, got {raw!r}") from None
    if not 0.0 <= value <= 1.0:  # also rejects NaN
        raise argparse.ArgumentTypeError(f"must be between 0 and 1, got {raw}")
    return value


_MAX_ERROR_LENGTH = 200


def _fail(message: str) -> int:
    if len(message) > _MAX_ERROR_LENGTH:
        message = message[: _MAX_ERROR_LENGTH - 3] + "..."
    print(f"openodia: error: {message}", file=sys.stderr)
    return 1


def _emit_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def _utf8_stdio() -> None:
    """Use UTF-8 even when a redirected stream defaults to a legacy codec."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        encoding = (getattr(stream, "encoding", None) or "").lower().replace("-", "")
        reconfigure = getattr(stream, "reconfigure", None)
        if encoding != "utf8" and reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):  # pragma: no cover - exotic streams
                pass


def _utf8_text(text: str) -> str:
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        return os.fsencode(text).decode("utf-8")
    return text


def _require_utf8_input(args: argparse.Namespace) -> None:
    reconfigure = getattr(sys.stdin, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(errors="strict")
    if not getattr(args, "file", False):
        try:
            args.text = _utf8_text(getattr(args, "text", ""))
        except UnicodeError:
            raise ValueError("text argument is not valid UTF-8") from None


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------


def _cmd_tokenize(args: argparse.Namespace) -> int:
    from openodia import ud

    text = _read_input(args.text, file=args.file)
    tokens = ud.sentence_tokenizer(text) if args.sentences else ud.word_tokenizer(text)
    if args.json:
        _emit_json({"tokens": list(tokens)})
        return 0
    for token in tokens:
        print(token)
    return 0


def _cmd_normalize(args: argparse.Namespace) -> int:
    from openodia import normalize

    text = _read_input(args.text, file=args.file)
    normalized = normalize(text, form=args.form)
    if args.json:
        _emit_json({"text": normalized})
    else:
        print(normalized)
    return 0


def _cmd_clean(args: argparse.Namespace) -> int:
    from openodia import clean
    from openodia.text import CleanOptions

    text = _read_input(args.text, file=args.file)
    options = CleanOptions(
        strip_zwj=not args.keep_zwj,
        strip_zwnj=not args.keep_zwnj,
        collapse_whitespace=not args.keep_whitespace,
        latin_to_odia_digits=args.latin_to_odia,
        odia_to_latin_digits=args.odia_to_latin,
    )
    cleaned = clean(text, options=options)
    if args.json:
        _emit_json({"text": cleaned})
    else:
        print(cleaned)
    return 0


def _cmd_translate(args: argparse.Namespace) -> int:
    from openodia import odia_to_other_lang, other_lang_to_odia, universal_translation

    text = _read_input(args.text, file=args.file)
    if args.from_lang == "or":
        translated = odia_to_other_lang(text, dest_language_code=args.to)
    elif args.to == "or":
        translated = other_lang_to_odia(text, source_language_code=args.from_lang)
    else:
        translated = universal_translation(
            text,
            source_language_code=args.from_lang,
            dest_language_code=args.to,
        )
    if args.json:
        _emit_json({"text": translated})
    else:
        print(translated)
    return 0


def _cmd_detect_language(args: argparse.Namespace) -> int:
    from openodia import ud

    text = _read_input(args.text, file=args.file)
    # Whitespace-only input would divide by zero inside detect_language.
    result: dict[str, Any] = ud.detect_language(text, threshold=args.threshold) if text.strip() else {}
    if args.json:
        _emit_json(result)
    else:
        if not result:
            print("(empty input)")
        else:
            print(f"{result['language']} (confidence: {result['confidence_score']})")
    return 0


def _cmd_name(args: argparse.Namespace) -> int:
    from openodia import name

    if args.kind == "full":
        names = name.generate_names(args.count)
    elif args.kind == "first":
        names = name.generate_firstnames(args.count)
    elif args.kind == "middle":
        names = name.generate_middlenames(args.count)
    elif args.kind == "surname":
        names = name.generate_surnames(args.count)
    elif args.kind == "prefix":
        names = name.generate_prefixes(args.count)
    else:  # pragma: no cover  — argparse already validates ``--kind``
        raise ValueError(f"unknown name kind: {args.kind}")
    if args.json:
        _emit_json({"names": list(names)})
        return 0
    for n in names:
        print(n)
    return 0


def _cmd_summarize(args: argparse.Namespace) -> int:
    from openodia import WordFrequency

    text = _read_input(args.text, file=args.file)
    wf = WordFrequency(text=text)
    if args.threshold is None:
        summary = wf.get_summary()
    elif not math.isfinite(args.threshold) or args.threshold <= 0:
        # WordFrequency treats a falsy threshold as "auto", so 0 would
        # silently act like the default; reject it instead.
        print("error: --threshold must be a positive number", file=sys.stderr)
        return 2
    else:
        summary = wf.get_summary(threshold=args.threshold)
    if args.json:
        _emit_json({"summary": summary})
    else:
        print(summary)
    return 0


def _cmd_remove_stopwords(args: argparse.Namespace) -> int:
    from openodia import ud

    text = _read_input(args.text, file=args.file)
    result = ud.remove_stopwords(text, get_str=args.get_str)
    if args.json:
        _emit_json({"tokens": result} if isinstance(result, list) else {"text": result})
    elif isinstance(result, list):
        for token in result:
            print(token)
    else:
        print(result)
    return 0


def _cmd_ngrams(args: argparse.Namespace) -> int:
    from openodia import ngrams

    text = _read_input(args.text, file=args.file)
    grams = ngrams(text, args.n)
    if args.json:
        _emit_json({"ngrams": [list(gram) for gram in grams]})
        return 0
    for tup in grams:
        print(" ".join(tup))
    return 0


def _cmd_freq(args: argparse.Namespace) -> int:
    from openodia import FreqDist

    text = _read_input(args.text, file=args.file)
    fd = FreqDist(text)
    top = fd.most_common(args.top)
    if args.json:
        _emit_json({"counts": [{"token": token, "count": count} for token, count in top]})
        return 0
    for token, count in top:
        print(f"{count}\t{token}")
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level :class:`argparse.ArgumentParser`."""
    parser = argparse.ArgumentParser(
        prog="openodia",
        description=(
            "Command-line interface for the openodia Python package. "
            "Each subcommand wraps a function from the library. "
            'Pass "-" as the text argument to read from stdin.'
        ),
    )
    from openodia import __version__

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    # tokenize
    p = sub.add_parser("tokenize", help="Word or sentence tokenisation")
    p.add_argument("text", help="Inline text, or '-' for stdin; a path with --file")
    p.add_argument("--file", action="store_true", help="Read the text argument as a UTF-8 file path")
    p.add_argument(
        "--sentences",
        action="store_true",
        help="Sentence tokenisation instead of word tokenisation",
    )
    p.set_defaults(func=_cmd_tokenize)

    # normalize
    p = sub.add_parser("normalize", help="Unicode normalisation (NFC by default)")
    p.add_argument("text", help="Inline text, or '-' for stdin; a path with --file")
    p.add_argument("--file", action="store_true", help="Read the text argument as a UTF-8 file path")
    p.add_argument(
        "--form",
        choices=["NFC", "NFD", "NFKC", "NFKD"],
        default="NFC",
        help="Normalisation form (default: NFC)",
    )
    p.set_defaults(func=_cmd_normalize)

    # clean
    p = sub.add_parser("clean", help="Strip ZWJ/ZWNJ and normalise whitespace")
    p.add_argument("text", help="Inline text, or '-' for stdin; a path with --file")
    p.add_argument("--file", action="store_true", help="Read the text argument as a UTF-8 file path")
    p.add_argument("--keep-zwj", action="store_true", help="Do not strip ZWJ")
    p.add_argument("--keep-zwnj", action="store_true", help="Do not strip ZWNJ")
    p.add_argument(
        "--keep-whitespace",
        action="store_true",
        help="Do not collapse internal whitespace",
    )
    digits = p.add_mutually_exclusive_group()
    digits.add_argument(
        "--latin-to-odia",
        action="store_true",
        help="Convert ASCII digits to Odia digits",
    )
    digits.add_argument(
        "--odia-to-latin",
        action="store_true",
        help="Convert Odia digits to ASCII digits",
    )
    p.set_defaults(func=_cmd_clean)

    # translate
    p = sub.add_parser("translate", help="Translate between Odia and another language")
    p.add_argument("text", help="Inline text, or '-' for stdin; a path with --file")
    p.add_argument("--file", action="store_true", help="Read the text argument as a UTF-8 file path")
    p.add_argument("--from", dest="from_lang", default="en", help="Source language code (default: en)")
    p.add_argument("--to", default="or", help="Destination language code (default: or)")
    p.set_defaults(func=_cmd_translate)

    # detect-language
    p = sub.add_parser("detect-language", help="Detect whether input is Odia")
    p.add_argument("text", help="Inline text, or '-' for stdin; a path with --file")
    p.add_argument("--file", action="store_true", help="Read the text argument as a UTF-8 file path")
    p.add_argument(
        "--threshold",
        type=_unit_float,
        default=0.5,
        help="Confidence threshold for classifying as Odia (default: 0.5)",
    )
    p.set_defaults(func=_cmd_detect_language)

    # name
    p = sub.add_parser("name", help="Generate random Odia names")
    p.add_argument(
        "--kind",
        choices=["full", "first", "middle", "surname", "prefix"],
        default="full",
        help="Which name part to generate (default: full)",
    )
    p.add_argument("--count", type=_int_at_least(0), default=10, help="Number of names to generate (default: 10)")
    p.set_defaults(func=_cmd_name)

    # summarize
    p = sub.add_parser("summarize", help="Extractive summary of Odia text")
    p.add_argument("text", help="Inline text, or '-' for stdin; a path with --file")
    p.add_argument("--file", action="store_true", help="Read the text argument as a UTF-8 file path")
    p.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Sentence-score threshold; higher = shorter summary",
    )
    p.set_defaults(func=_cmd_summarize)

    # remove-stopwords
    p = sub.add_parser("remove-stopwords", help="Strip stopwords from input")
    p.add_argument("text", help="Inline text, or '-' for stdin; a path with --file")
    p.add_argument("--file", action="store_true", help="Read the text argument as a UTF-8 file path")
    p.add_argument(
        "--get-str",
        action="store_true",
        help="Emit a single line instead of one token per line",
    )
    p.set_defaults(func=_cmd_remove_stopwords)

    # ngrams
    p = sub.add_parser("ngrams", help="Emit overlapping n-grams")
    p.add_argument("text", help="Inline text, or '-' for stdin; a path with --file")
    p.add_argument("--file", action="store_true", help="Read the text argument as a UTF-8 file path")
    p.add_argument("-n", type=_int_at_least(1), default=2, help="N-gram size (default: 2)")
    p.set_defaults(func=_cmd_ngrams)

    # freq
    p = sub.add_parser("freq", help="Frequency distribution of tokens")
    p.add_argument("text", help="Inline text, or '-' for stdin; a path with --file")
    p.add_argument("--file", action="store_true", help="Read the text argument as a UTF-8 file path")
    p.add_argument(
        "--top",
        type=_int_at_least(0),
        default=20,
        help="How many top tokens to emit (default: 20)",
    )
    p.set_defaults(func=_cmd_freq)

    for subparser in sub.choices.values():
        subparser.add_argument("--json", action="store_true", help="Emit JSON instead of text")

    return parser


def _translation_failure(exc: Exception) -> str | None:
    """Describe a deep-translator error, or return ``None`` if ``exc`` is something else."""
    from deep_translator.exceptions import BaseError, LanguageNotSupportedException, RequestError, TooManyRequests

    if isinstance(exc, TooManyRequests):
        return "Google Translate refused the request (rate limit or captcha); try again later"
    if isinstance(exc, LanguageNotSupportedException):
        return f"unsupported language code {exc.val!r}"
    if isinstance(exc, BaseError | RequestError):
        return exc.message
    return None


def _is_closed_pipe(exc: OSError) -> bool:
    """Whether ``exc`` is a write to a closed pipe; Windows reports it as a bare ``EINVAL``."""
    windows_write = sys.platform == "win32" and exc.errno == errno.EINVAL and exc.filename is None
    return isinstance(exc, BrokenPipeError) or windows_write


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Argument list. ``None`` uses ``sys.argv[1:]``.

    Returns:
        Process exit code.
    """
    _utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.json:
            _require_utf8_input(args)
        code = int(args.func(args))
        if sys.stdout is not None:
            sys.stdout.flush()
        return code
    except OSError as exc:
        if sys.stdout is None or not _is_closed_pipe(exc):
            return _fail(str(exc))
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 141
    except (ValueError, ImportError) as exc:
        return _fail(str(exc))
    except Exception as exc:
        message = _translation_failure(exc)
        if message is None:
            raise
        return _fail(message)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
