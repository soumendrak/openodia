"""The :class:`Stopwords` container."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Iterator
from pathlib import Path


class Stopwords:
    """A mutable, per-pipeline stopword list.

    Internally backed by a ``set[str]`` so membership tests are O(1).

    Args:
        words: Initial words. Strings are added as-is (each as one stopword).
    """

    def __init__(self, words: Iterable[str] = ()) -> None:
        self._words: set[str] = set(words)

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def default(cls) -> Stopwords:
        """Return a new instance seeded with the package's bundled list."""
        # Imported lazily to avoid a circular import via ``openodia.__init__``.
        from openodia.common.constants import STOPWORDS

        return cls(STOPWORDS)

    @classmethod
    def from_file(cls, path: Path | str, encoding: str = "utf-8") -> Stopwords:
        """Load stopwords from a text file (one word per line).

        Blank lines and lines starting with ``#`` are skipped.

        Args:
            path: File to read.
            encoding: File encoding. Defaults to UTF-8.

        Raises:
            FileNotFoundError: If ``path`` does not exist.
        """
        words: list[str] = []
        for raw in Path(path).read_text(encoding=encoding).splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            words.append(line)
        return cls(words)

    @classmethod
    def from_corpus(cls, tokens: Iterable[str], top_n: int = 100) -> Stopwords:
        """Derive a stopword list from the highest-frequency tokens.

        Args:
            tokens: Pre-tokenized input.
            top_n: How many of the most common tokens to keep. Must be ≥ 1.

        Raises:
            ValueError: If ``top_n`` is not positive.
        """
        if top_n < 1:
            raise ValueError(f"top_n must be >= 1, got {top_n}")
        counts = Counter(tokens)
        return cls(word for word, _ in counts.most_common(top_n))

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, words: str | Iterable[str]) -> Stopwords:
        """Add one or more words. Returns ``self`` for chaining."""
        if isinstance(words, str):
            self._words.add(words)
        else:
            self._words.update(words)
        return self

    def remove(self, words: str | Iterable[str]) -> Stopwords:
        """Drop one or more words. Missing words are ignored.

        Returns ``self`` for chaining.
        """
        if isinstance(words, str):
            self._words.discard(words)
        else:
            for word in words:
                self._words.discard(word)
        return self

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Path | str, encoding: str = "utf-8") -> None:
        """Write stopwords to a file, sorted, one per line."""
        Path(path).write_text("\n".join(sorted(self._words)) + "\n", encoding=encoding)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def coverage(self, tokens: Iterable[str]) -> float:
        """Fraction of ``tokens`` that are stopwords.

        Returns ``0.0`` for an empty input.
        """
        total = 0
        hits = 0
        for token in tokens:
            total += 1
            if token in self._words:
                hits += 1
        return hits / total if total else 0.0

    # ------------------------------------------------------------------
    # Container / protocol methods
    # ------------------------------------------------------------------

    def __contains__(self, word: object) -> bool:
        return word in self._words

    def __iter__(self) -> Iterator[str]:
        return iter(self._words)

    def __len__(self) -> int:
        return len(self._words)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Stopwords):
            return self._words == other._words
        if isinstance(other, (set, frozenset)):
            return self._words == set(other)
        return NotImplemented

    def __repr__(self) -> str:
        return f"Stopwords({len(self._words)} words)"
