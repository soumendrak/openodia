"""N-gram, frequency, and co-occurrence primitives."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator, Sequence
from math import log2
from typing import Literal


def _as_tokens(tokens_or_text: Sequence[str] | str) -> list[str]:
    """Accept either pre-tokenized input or raw text."""
    if isinstance(tokens_or_text, str):
        # Imported lazily to keep this module decoupled from the tokenizer
        # in the rare case a user wants to use it in isolation.
        from openodia._understandData import UnderstandData

        return UnderstandData.word_tokenizer(tokens_or_text)
    return list(tokens_or_text)


def ngrams(tokens_or_text: Sequence[str] | str, n: int) -> Iterator[tuple[str, ...]]:
    """Yield overlapping n-grams from ``tokens_or_text``.

    Args:
        tokens_or_text: Pre-tokenized list/sequence, or a raw string (in which
            case the package's word tokenizer is applied).
        n: N-gram size. Must be ≥ 1.

    Yields:
        Tuples of length ``n``. Yields nothing if the token count is below
        ``n``.

    Raises:
        ValueError: If ``n < 1``.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    tokens = _as_tokens(tokens_or_text)
    for i in range(len(tokens) - n + 1):
        yield tuple(tokens[i : i + n])


class FreqDist(Counter):
    """Token frequency distribution backed by :class:`collections.Counter`.

    Adds three light convenience methods:

    * :meth:`hapaxes` — words occurring exactly once.
    * :meth:`entropy` — Shannon entropy of the distribution in bits.
    * :attr:`ttr` — type-token ratio (vocabulary / total count).

    All other ``Counter`` operations (``most_common``, ``+``, ``&``, ...) work
    unchanged.
    """

    def __init__(self, tokens_or_text: Sequence[str] | str | None = None) -> None:
        if tokens_or_text is None:
            super().__init__()
        else:
            super().__init__(_as_tokens(tokens_or_text))

    @property
    def total_count(self) -> int:
        """Sum of all counts (i.e. token count, not vocabulary size)."""
        return sum(self.values())

    @property
    def ttr(self) -> float:
        """Type-token ratio. ``0.0`` for an empty distribution."""
        total = self.total_count
        return len(self) / total if total else 0.0

    def hapaxes(self) -> list[str]:
        """Words occurring exactly once, in insertion order."""
        return [word for word, count in self.items() if count == 1]

    def entropy(self) -> float:
        """Shannon entropy of the distribution, in bits.

        Returns ``0.0`` for an empty distribution.
        """
        total = self.total_count
        if not total:
            return 0.0
        return -sum((c / total) * log2(c / total) for c in self.values() if c > 0)


CollocationScore = Literal["pmi"]


def collocations(
    tokens_or_text: Sequence[str] | str,
    top_k: int = 20,
    min_count: int = 2,
    score: CollocationScore = "pmi",
) -> list[tuple[tuple[str, str], float]]:
    """Top-scoring bigram collocations.

    Uses pointwise mutual information (PMI):

    .. math::

        \\mathrm{PMI}(w_1, w_2) = \\log_2 \\frac{P(w_1, w_2)}{P(w_1) \\, P(w_2)}

    Args:
        tokens_or_text: Pre-tokenized sequence or raw text.
        top_k: Maximum number of collocations to return.
        min_count: Bigrams occurring fewer than this many times are skipped
            — PMI is unstable on very rare pairs. Must be ≥ 1.
        score: Scoring method. Only ``"pmi"`` is supported in v1.

    Returns:
        List of ``((w1, w2), score)`` sorted descending by score.
        Empty when input is too short or no bigram meets ``min_count``.

    Raises:
        ValueError: If ``top_k < 1``, ``min_count < 1``, or ``score`` is
            unknown.
    """
    if top_k < 1:
        raise ValueError(f"top_k must be >= 1, got {top_k}")
    if min_count < 1:
        raise ValueError(f"min_count must be >= 1, got {min_count}")
    if score != "pmi":
        raise ValueError(f"unknown score {score!r}; supported: 'pmi'")

    tokens = _as_tokens(tokens_or_text)
    if len(tokens) < 2:
        return []

    total = len(tokens)
    bigram_total = total - 1
    unigrams = Counter(tokens)
    bigrams = Counter(zip(tokens, tokens[1:], strict=False))

    scored: list[tuple[tuple[str, str], float]] = []
    for (w1, w2), c12 in bigrams.items():
        if c12 < min_count:
            continue
        p12 = c12 / bigram_total
        p1 = unigrams[w1] / total
        p2 = unigrams[w2] / total
        scored.append(((w1, w2), log2(p12 / (p1 * p2))))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:top_k]


def cooccurrence(
    tokens_or_text: Sequence[str] | str,
    window: int = 5,
    symmetric: bool = True,
) -> Counter:
    """Count word co-occurrences within a sliding window.

    Args:
        tokens_or_text: Pre-tokenized sequence or raw text.
        window: Maximum number of positions between two tokens for them to
            be considered co-occurring. Must be ≥ 1.
        symmetric: If True (default), the returned keys are sorted tuples
            and order is ignored — ``("a", "b")`` and ``("b", "a")``
            collapse. If False, keys are ``(earlier, later)`` so direction
            is preserved.

    Returns:
        :class:`collections.Counter` mapping pair → co-occurrence count.

    Raises:
        ValueError: If ``window < 1``.
    """
    if window < 1:
        raise ValueError(f"window must be >= 1, got {window}")

    tokens = _as_tokens(tokens_or_text)
    counts: Counter = Counter()
    n = len(tokens)
    for i in range(n):
        end = min(n, i + window + 1)
        for j in range(i + 1, end):
            w1, w2 = tokens[i], tokens[j]
            key = tuple(sorted((w1, w2))) if symmetric else (w1, w2)
            counts[key] += 1
    return counts
