"""Console interface for :mod:`openodia`."""

from __future__ import annotations

import argparse
import sys


def _tokenize(mode: str, text: str) -> None:
    """Tokenize *text* either as words or sentences and print the result."""
    from openodia._understandData import UnderstandData as ud

    if mode == "words":
        tokens = ud.word_tokenizer(text)
    else:
        tokens = ud.sentence_tokenizer(text)
    print(" ".join(tokens))


def _translate(text: str, src: str, dest: str) -> None:
    """Translate *text* from ``src`` language to ``dest`` language."""
    from openodia._translate import universal_translation

    result = universal_translation(text, source_language_code=src, dest_language_code=dest)
    print(result)


def _summarize(text: str, threshold: float | None) -> None:
    """Summarize *text* using the word frequency method."""
    from openodia._summarization import WordFrequency

    wf = WordFrequency(text=text)
    print(wf.get_summary(threshold))


def _dataset(command: str) -> None:
    """Handle dataset related commands."""
    if command == "info":
        print("Available datasets: dictionary (En-Or_word_pairs_v3.json)")
    else:
        print("Datasets are bundled with the package and do not require download.")


def main(args: list[str] | None = None) -> int:
    """Entry point for the ``openodia`` command."""

    parser = argparse.ArgumentParser(prog="openodia", description="OpenOdia command line utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    tok = subparsers.add_parser("tokenize", help="Tokenize text")
    tok.add_argument("mode", choices=["words", "sentences"], help="Tokenization mode")
    tok.add_argument("text", help="Text to tokenize")

    trans = subparsers.add_parser("translate", help="Translate text between languages")
    trans.add_argument("text", help="Text to translate")
    trans.add_argument("--src", default="en", help="Source language code")
    trans.add_argument("--dest", default="or", help="Destination language code")

    summ = subparsers.add_parser("summarize", help="Summarize text")
    summ.add_argument("text", help="Text to summarize")
    summ.add_argument("--threshold", type=float, help="Frequency threshold")

    ds = subparsers.add_parser("dataset", help="Dataset utilities")
    ds_sub = ds.add_subparsers(dest="dataset_cmd", required=True)
    ds_sub.add_parser("download", help="Download datasets (no-op)")
    ds_sub.add_parser("info", help="Show information about datasets")

    ns = parser.parse_args(args)

    if ns.command == "tokenize":
        _tokenize(ns.mode, ns.text)
    elif ns.command == "translate":
        _translate(ns.text, ns.src, ns.dest)
    elif ns.command == "summarize":
        _summarize(ns.text, ns.threshold)
    elif ns.command == "dataset":
        _dataset(ns.dataset_cmd)

    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation
    sys.exit(main())
