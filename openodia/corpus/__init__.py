"""Corpus utilities for loading packaged datasets."""

from __future__ import annotations

from pathlib import Path
from collections.abc import Iterable
import csv
import json


_DATA_DIR = Path(__file__).parent


def load_parallel_corpus(filename: str = "sample_en_or.csv") -> list[tuple[str, str]]:
    """Load an English-Odia parallel corpus.

    Parameters
    ----------
    filename:
        Name of the CSV file inside ``parallel_corpus`` directory.

    Returns
    -------
    list[tuple[str, str]]
        List of ``(english, odia)`` sentence tuples.
    """

    file_path = _DATA_DIR / "parallel_corpus" / filename
    corpus: list[tuple[str, str]] = []
    with file_path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            corpus.append((row["english"], row["odia"]))
    return corpus


def load_monolingual_corpus(filename: str = "sample_or_sentences.json") -> Iterable[str]:
    """Load an Odia monolingual corpus.

    Parameters
    ----------
    filename:
        Name of the JSON file inside ``monolingual`` directory.

    Returns
    -------
    Iterable[str]
        Iterable of Odia sentences.
    """

    file_path = _DATA_DIR / "monolingual" / filename
    with file_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("sentences", [])


__all__ = ["load_parallel_corpus", "load_monolingual_corpus"]
