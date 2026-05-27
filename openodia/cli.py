"""Command-line interface for the openodia package.

Run ``openodia --help`` to see all subcommands.

The CLI is intentionally thin: each subcommand maps to an existing
Python entry point in the package. New subcommands can be added in
:func:`build_parser` and :func:`main` without touching anything else.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------


def _read_input(value: str) -> str:
    """Return text from one of:

    * ``"-"`` → stdin
    * an existing file path → file contents
    * anything else → the literal string
    """
    if value == "-":
        return sys.stdin.read()
    path = Path(value)
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return value


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------


def _cmd_tokenize(args: argparse.Namespace) -> int:
    from openodia import ud

    text = _read_input(args.text)
    tokens = ud.sentence_tokenizer(text) if args.sentences else ud.word_tokenizer(text)
    for token in tokens:
        print(token)
    return 0


def _cmd_normalize(args: argparse.Namespace) -> int:
    from openodia import normalize

    text = _read_input(args.text)
    print(normalize(text, form=args.form))
    return 0


def _cmd_clean(args: argparse.Namespace) -> int:
    from openodia import clean
    from openodia.text import CleanOptions

    text = _read_input(args.text)
    options = CleanOptions(
        strip_zwj=not args.keep_zwj,
        strip_zwnj=not args.keep_zwnj,
        collapse_whitespace=not args.keep_whitespace,
        latin_to_odia_digits=args.latin_to_odia,
        odia_to_latin_digits=args.odia_to_latin,
    )
    print(clean(text, options=options))
    return 0


def _cmd_translate(args: argparse.Namespace) -> int:
    from openodia import odia_to_other_lang, other_lang_to_odia, universal_translation

    text = _read_input(args.text)
    if args.from_lang == "or":
        print(odia_to_other_lang(text, dest_language_code=args.to))
    elif args.to == "or":
        print(other_lang_to_odia(text, source_language_code=args.from_lang))
    else:
        print(
            universal_translation(
                text,
                source_language_code=args.from_lang,
                dest_language_code=args.to,
            )
        )
    return 0


def _cmd_detect_language(args: argparse.Namespace) -> int:
    from openodia import ud

    text = _read_input(args.text)
    result: dict[str, Any] = ud.detect_language(text, threshold=args.threshold)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
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
        names = name.generate_prefixes(args.count) if args.count else name.generate_prefixes()
    else:  # pragma: no cover  — argparse already validates ``--kind``
        raise ValueError(f"unknown name kind: {args.kind}")
    for n in names:
        print(n)
    return 0


def _cmd_summarize(args: argparse.Namespace) -> int:
    from openodia import WordFrequency

    text = _read_input(args.text)
    wf = WordFrequency(text=text)
    if args.threshold is None:
        print(wf.get_summary())
    else:
        print(wf.get_summary(threshold=args.threshold))
    return 0


def _cmd_remove_stopwords(args: argparse.Namespace) -> int:
    from openodia import ud

    text = _read_input(args.text)
    result = ud.remove_stopwords(text, get_str=args.get_str)
    if isinstance(result, list):
        for token in result:
            print(token)
    else:
        print(result)
    return 0


def _cmd_ngrams(args: argparse.Namespace) -> int:
    from openodia import ngrams

    text = _read_input(args.text)
    for tup in ngrams(text, args.n):
        print(" ".join(tup))
    return 0


def _cmd_freq(args: argparse.Namespace) -> int:
    from openodia import FreqDist

    text = _read_input(args.text)
    fd = FreqDist(text)
    for token, count in fd.most_common(args.top):
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
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    # tokenize
    p = sub.add_parser("tokenize", help="Word or sentence tokenisation")
    p.add_argument("text", help="Inline text, file path, or '-' for stdin")
    p.add_argument(
        "--sentences",
        action="store_true",
        help="Sentence tokenisation instead of word tokenisation",
    )
    p.set_defaults(func=_cmd_tokenize)

    # normalize
    p = sub.add_parser("normalize", help="Unicode normalisation (NFC by default)")
    p.add_argument("text", help="Inline text, file path, or '-' for stdin")
    p.add_argument(
        "--form",
        choices=["NFC", "NFD", "NFKC", "NFKD"],
        default="NFC",
        help="Normalisation form (default: NFC)",
    )
    p.set_defaults(func=_cmd_normalize)

    # clean
    p = sub.add_parser("clean", help="Strip ZWJ/ZWNJ and normalise whitespace")
    p.add_argument("text", help="Inline text, file path, or '-' for stdin")
    p.add_argument("--keep-zwj", action="store_true", help="Do not strip ZWJ")
    p.add_argument("--keep-zwnj", action="store_true", help="Do not strip ZWNJ")
    p.add_argument(
        "--keep-whitespace",
        action="store_true",
        help="Do not collapse internal whitespace",
    )
    p.add_argument(
        "--latin-to-odia",
        action="store_true",
        help="Convert ASCII digits to Odia digits",
    )
    p.add_argument(
        "--odia-to-latin",
        action="store_true",
        help="Convert Odia digits to ASCII digits",
    )
    p.set_defaults(func=_cmd_clean)

    # translate
    p = sub.add_parser("translate", help="Translate between Odia and another language")
    p.add_argument("text", help="Inline text, file path, or '-' for stdin")
    p.add_argument("--from", dest="from_lang", default="en", help="Source language code (default: en)")
    p.add_argument("--to", default="or", help="Destination language code (default: or)")
    p.set_defaults(func=_cmd_translate)

    # detect-language
    p = sub.add_parser("detect-language", help="Detect whether input is Odia")
    p.add_argument("text", help="Inline text, file path, or '-' for stdin")
    p.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Confidence threshold for classifying as Odia (default: 0.5)",
    )
    p.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    p.set_defaults(func=_cmd_detect_language)

    # name
    p = sub.add_parser("name", help="Generate random Odia names")
    p.add_argument(
        "--kind",
        choices=["full", "first", "middle", "surname", "prefix"],
        default="full",
        help="Which name part to generate (default: full)",
    )
    p.add_argument("--count", type=int, default=10, help="Number of names to generate (default: 10)")
    p.set_defaults(func=_cmd_name)

    # summarize
    p = sub.add_parser("summarize", help="Extractive summary of Odia text")
    p.add_argument("text", help="Inline text, file path, or '-' for stdin")
    p.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Sentence-score threshold; higher = shorter summary",
    )
    p.set_defaults(func=_cmd_summarize)

    # remove-stopwords
    p = sub.add_parser("remove-stopwords", help="Strip stopwords from input")
    p.add_argument("text", help="Inline text, file path, or '-' for stdin")
    p.add_argument(
        "--get-str",
        action="store_true",
        help="Emit a single line instead of one token per line",
    )
    p.set_defaults(func=_cmd_remove_stopwords)

    # ngrams
    p = sub.add_parser("ngrams", help="Emit overlapping n-grams")
    p.add_argument("text", help="Inline text, file path, or '-' for stdin")
    p.add_argument("-n", type=int, default=2, help="N-gram size (default: 2)")
    p.set_defaults(func=_cmd_ngrams)

    # freq
    p = sub.add_parser("freq", help="Frequency distribution of tokens")
    p.add_argument("text", help="Inline text, file path, or '-' for stdin")
    p.add_argument(
        "--top",
        type=int,
        default=20,
        help="How many top tokens to emit (default: 20)",
    )
    p.set_defaults(func=_cmd_freq)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Argument list. ``None`` uses ``sys.argv[1:]``.

    Returns:
        Process exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
