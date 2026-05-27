from math import isclose, log2

import pytest

from openodia import FreqDist, collocations, cooccurrence, ngrams


class TestNgrams:
    def test_unigrams(self) -> None:
        assert list(ngrams(["a", "b", "c"], 1)) == [("a",), ("b",), ("c",)]

    def test_bigrams(self) -> None:
        assert list(ngrams(["a", "b", "c"], 2)) == [("a", "b"), ("b", "c")]

    def test_trigrams(self) -> None:
        assert list(ngrams(["a", "b", "c", "d"], 3)) == [
            ("a", "b", "c"),
            ("b", "c", "d"),
        ]

    def test_n_equals_token_count(self) -> None:
        assert list(ngrams(["a", "b"], 2)) == [("a", "b")]

    def test_n_larger_than_token_count_yields_nothing(self) -> None:
        assert list(ngrams(["a"], 2)) == []

    def test_empty_input(self) -> None:
        assert list(ngrams([], 2)) == []

    def test_accepts_text_input(self) -> None:
        # Tokenized via UnderstandData.word_tokenizer.
        result = list(ngrams("ରାମ ସୀତା ଲକ୍ଷ୍ମଣ", 2))
        assert result == [("ରାମ", "ସୀତା"), ("ସୀତା", "ଲକ୍ଷ୍ମଣ")]

    def test_invalid_n_raises(self) -> None:
        with pytest.raises(ValueError, match="n must be >= 1"):
            list(ngrams(["a"], 0))


class TestFreqDist:
    def test_construction_from_tokens(self) -> None:
        fd = FreqDist(["a", "b", "a"])
        assert fd["a"] == 2
        assert fd["b"] == 1

    def test_construction_from_text(self) -> None:
        fd = FreqDist("ରାମ ସୀତା ରାମ")
        assert fd["ରାମ"] == 2
        assert fd["ସୀତା"] == 1

    def test_empty_construction(self) -> None:
        fd = FreqDist()
        assert len(fd) == 0
        assert fd.total_count == 0

    def test_most_common(self) -> None:
        fd = FreqDist(["a", "b", "a", "c", "a", "b"])
        assert fd.most_common(2) == [("a", 3), ("b", 2)]

    def test_hapaxes(self) -> None:
        fd = FreqDist(["a", "b", "a", "c"])
        assert sorted(fd.hapaxes()) == ["b", "c"]

    def test_hapaxes_empty(self) -> None:
        assert FreqDist().hapaxes() == []

    def test_total_count(self) -> None:
        assert FreqDist(["a", "b", "a"]).total_count == 3

    def test_ttr_empty_is_zero(self) -> None:
        assert FreqDist().ttr == 0.0

    def test_ttr_all_unique(self) -> None:
        assert FreqDist(["a", "b", "c"]).ttr == 1.0

    def test_ttr_partial(self) -> None:
        assert FreqDist(["a", "a", "b", "b"]).ttr == 0.5

    def test_entropy_empty_is_zero(self) -> None:
        assert FreqDist().entropy() == 0.0

    def test_entropy_uniform(self) -> None:
        # Two equally-likely outcomes -> 1 bit.
        assert isclose(FreqDist(["a", "b"]).entropy(), 1.0)

    def test_entropy_known_distribution(self) -> None:
        # P(a) = 1/2, P(b) = 1/4, P(c) = 1/4 -> H = 1.5 bits.
        fd = FreqDist(["a", "a", "b", "c"])
        assert isclose(fd.entropy(), 1.5)

    def test_entropy_single_outcome_is_zero(self) -> None:
        assert FreqDist(["a", "a", "a"]).entropy() == 0.0

    def test_inherits_counter_arithmetic(self) -> None:
        fd1 = FreqDist(["a", "b"])
        fd2 = FreqDist(["b", "c"])
        combined = fd1 + fd2
        assert combined["a"] == 1
        assert combined["b"] == 2
        assert combined["c"] == 1


class TestCollocations:
    def test_returns_sorted_descending_by_score(self) -> None:
        # "the cat" appears 3 times, "cat sat" twice; PMI ranks both
        # but "the cat" should win on co-occurrence count.
        tokens = "the cat the cat the cat sat sat".split()
        result = collocations(tokens, top_k=5, min_count=1)
        assert result, "expected non-empty result"
        scores = [score for _, score in result]
        assert scores == sorted(scores, reverse=True)

    def test_min_count_filters(self) -> None:
        tokens = ["a", "b", "a", "b", "c", "d"]
        with_low = collocations(tokens, top_k=10, min_count=1)
        with_high = collocations(tokens, top_k=10, min_count=2)
        assert len(with_high) <= len(with_low)

    def test_short_input_returns_empty(self) -> None:
        assert collocations(["a"], top_k=5) == []
        assert collocations([], top_k=5) == []

    def test_top_k_caps_result(self) -> None:
        tokens = ["a", "b", "c", "d", "a", "b", "c", "d"]
        result = collocations(tokens, top_k=2, min_count=1)
        assert len(result) <= 2

    def test_pmi_value(self) -> None:
        # Each pair occurs exactly twice in a 4-token corpus: ["a", "b", "a", "b"]
        # Bigrams: ("a","b"), ("b","a"), ("a","b") -> c("a","b") = 2, c("b","a") = 1
        # total tokens = 4, bigram_total = 3
        # For ("a", "b"): P(a,b) = 2/3, P(a) = 1/2, P(b) = 1/2 -> PMI = log2((2/3)/(1/4))
        tokens = ["a", "b", "a", "b"]
        result = collocations(tokens, top_k=10, min_count=1)
        ab_score = dict(result).get(("a", "b"))
        assert ab_score is not None
        expected = log2((2 / 3) / (0.5 * 0.5))
        assert isclose(ab_score, expected)

    def test_invalid_top_k_raises(self) -> None:
        with pytest.raises(ValueError, match="top_k must be >= 1"):
            collocations(["a", "b"], top_k=0)

    def test_invalid_min_count_raises(self) -> None:
        with pytest.raises(ValueError, match="min_count must be >= 1"):
            collocations(["a", "b"], min_count=0)

    def test_unknown_score_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown score"):
            collocations(["a", "b"], score="loglik")  # type: ignore[arg-type]

    def test_accepts_text_input(self) -> None:
        result = collocations("ରାମ ସୀତା ରାମ ସୀତା", top_k=5, min_count=1)
        assert any(pair == ("ରାମ", "ସୀତା") for pair, _ in result)


class TestCooccurrence:
    def test_symmetric_basic(self) -> None:
        # Window 1: pairs are (a,b), (b,c), (c,d).
        result = cooccurrence(["a", "b", "c", "d"], window=1)
        assert result[("a", "b")] == 1
        assert result[("b", "c")] == 1
        assert result[("c", "d")] == 1
        assert len(result) == 3

    def test_symmetric_uses_sorted_keys(self) -> None:
        # The pair appears as (b, a) in the source but should normalise to (a, b).
        result = cooccurrence(["b", "a"], window=1)
        assert ("a", "b") in result
        assert ("b", "a") not in result

    def test_asymmetric_preserves_order(self) -> None:
        result = cooccurrence(["b", "a"], window=1, symmetric=False)
        assert ("b", "a") in result
        assert ("a", "b") not in result

    def test_window_size(self) -> None:
        # Window 2 pulls in (a,c) too.
        result = cooccurrence(["a", "b", "c"], window=2)
        assert result[("a", "c")] == 1

    def test_window_larger_than_corpus(self) -> None:
        result = cooccurrence(["a", "b"], window=100)
        assert result == {("a", "b"): 1}

    def test_repeated_pair_accumulates(self) -> None:
        result = cooccurrence(["a", "b", "a", "b"], window=1)
        assert result[("a", "b")] == 3

    def test_invalid_window_raises(self) -> None:
        with pytest.raises(ValueError, match="window must be >= 1"):
            cooccurrence(["a"], window=0)

    def test_empty_input(self) -> None:
        assert cooccurrence([], window=5) == {}

    def test_accepts_text_input(self) -> None:
        result = cooccurrence("ରାମ ସୀତା ଲକ୍ଷ୍ମଣ", window=1)
        assert result[("ରାମ", "ସୀତା")] == 1


class TestPublicAPI:
    def test_top_level_exports(self) -> None:
        import openodia

        assert openodia.ngrams is ngrams
        assert openodia.FreqDist is FreqDist
        assert openodia.collocations is collocations
        assert openodia.cooccurrence is cooccurrence
