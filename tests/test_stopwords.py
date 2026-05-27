from pathlib import Path

import pytest

from openodia import STOPWORDS, Stopwords, ud


class TestConstructor:
    def test_empty_default(self) -> None:
        sw = Stopwords()
        assert len(sw) == 0

    def test_from_iterable(self) -> None:
        sw = Stopwords(["a", "b", "c"])
        assert "a" in sw
        assert len(sw) == 3

    def test_dedupes_input(self) -> None:
        sw = Stopwords(["a", "a", "b"])
        assert len(sw) == 2


class TestDefault:
    def test_uses_bundled_list(self) -> None:
        sw = Stopwords.default()
        assert len(sw) == len(STOPWORDS)
        assert "ଓ" in sw

    def test_returns_independent_instance(self) -> None:
        """Mutating the returned instance must not affect the bundled list."""
        sw = Stopwords.default()
        sw.add("zzz")
        assert "zzz" not in STOPWORDS
        sw_again = Stopwords.default()
        assert "zzz" not in sw_again


class TestFromFile:
    def test_basic(self, tmp_path: Path) -> None:
        f = tmp_path / "sw.txt"
        f.write_text("ଆଉ\nଓ\n", encoding="utf-8")
        sw = Stopwords.from_file(f)
        assert "ଆଉ" in sw
        assert "ଓ" in sw
        assert len(sw) == 2

    def test_skips_blank_and_comment_lines(self, tmp_path: Path) -> None:
        f = tmp_path / "sw.txt"
        f.write_text("# header\nଓ\n\n# comment\nଆଉ\n", encoding="utf-8")
        sw = Stopwords.from_file(f)
        assert len(sw) == 2

    def test_accepts_path_as_string(self, tmp_path: Path) -> None:
        f = tmp_path / "sw.txt"
        f.write_text("ଓ\n", encoding="utf-8")
        sw = Stopwords.from_file(str(f))
        assert "ଓ" in sw

    def test_strips_whitespace(self, tmp_path: Path) -> None:
        f = tmp_path / "sw.txt"
        f.write_text("  ଓ  \n\tଆଉ\t\n", encoding="utf-8")
        sw = Stopwords.from_file(f)
        assert sw == {"ଓ", "ଆଉ"}

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            Stopwords.from_file(tmp_path / "does_not_exist.txt")


class TestFromCorpus:
    def test_picks_most_common(self) -> None:
        tokens = ["the", "the", "the", "a", "a", "b"]
        sw = Stopwords.from_corpus(tokens, top_n=2)
        assert "the" in sw
        assert "a" in sw
        assert "b" not in sw
        assert len(sw) == 2

    def test_top_n_larger_than_vocab(self) -> None:
        sw = Stopwords.from_corpus(["a", "b"], top_n=100)
        assert len(sw) == 2

    def test_invalid_top_n_raises(self) -> None:
        with pytest.raises(ValueError, match="top_n must be >= 1"):
            Stopwords.from_corpus(["a"], top_n=0)

    def test_works_with_generator(self) -> None:
        sw = Stopwords.from_corpus((tok for tok in ["a", "a", "b"]), top_n=1)
        assert "a" in sw


class TestAddRemove:
    def test_add_single(self) -> None:
        sw = Stopwords()
        sw.add("ଓ")
        assert "ଓ" in sw

    def test_add_iterable(self) -> None:
        sw = Stopwords()
        sw.add(["ଓ", "ଆଉ"])
        assert "ଓ" in sw
        assert "ଆଉ" in sw

    def test_add_returns_self_for_chaining(self) -> None:
        sw = Stopwords().add("ଓ").add(["ଆଉ"])
        assert len(sw) == 2

    def test_remove_single(self) -> None:
        sw = Stopwords(["ଓ", "ଆଉ"])
        sw.remove("ଓ")
        assert "ଓ" not in sw
        assert "ଆଉ" in sw

    def test_remove_iterable(self) -> None:
        sw = Stopwords(["a", "b", "c"])
        sw.remove(["a", "b"])
        assert sw == {"c"}

    def test_remove_missing_word_is_silent(self) -> None:
        sw = Stopwords(["ଓ"])
        sw.remove("not-present")
        assert sw == {"ଓ"}

    def test_remove_returns_self_for_chaining(self) -> None:
        sw = Stopwords(["a", "b"]).remove("a").remove(["b"])
        assert len(sw) == 0


class TestSave:
    def test_round_trip(self, tmp_path: Path) -> None:
        sw = Stopwords(["ଓ", "ଆଉ", "ଏବେ"])
        out = tmp_path / "out.txt"
        sw.save(out)
        loaded = Stopwords.from_file(out)
        assert loaded == sw

    def test_sorted_output(self, tmp_path: Path) -> None:
        sw = Stopwords(["c", "a", "b"])
        out = tmp_path / "out.txt"
        sw.save(out)
        assert out.read_text(encoding="utf-8") == "a\nb\nc\n"

    def test_accepts_path_as_string(self, tmp_path: Path) -> None:
        out = tmp_path / "out.txt"
        Stopwords(["x"]).save(str(out))
        assert out.read_text(encoding="utf-8") == "x\n"


class TestCoverage:
    def test_empty_tokens_returns_zero(self) -> None:
        sw = Stopwords(["a"])
        assert sw.coverage([]) == 0.0

    def test_all_stopwords(self) -> None:
        sw = Stopwords(["a", "b"])
        assert sw.coverage(["a", "b", "a"]) == 1.0

    def test_partial(self) -> None:
        sw = Stopwords(["a"])
        assert sw.coverage(["a", "b", "c", "a"]) == 0.5

    def test_no_overlap(self) -> None:
        assert Stopwords(["a"]).coverage(["x", "y"]) == 0.0


class TestProtocols:
    def test_contains(self) -> None:
        sw = Stopwords(["a"])
        assert "a" in sw
        assert "b" not in sw

    def test_iter(self) -> None:
        sw = Stopwords(["a", "b"])
        assert sorted(sw) == ["a", "b"]

    def test_len(self) -> None:
        assert len(Stopwords()) == 0
        assert len(Stopwords(["a", "b"])) == 2

    def test_equality_to_another_stopwords(self) -> None:
        assert Stopwords(["a", "b"]) == Stopwords(["b", "a"])
        assert Stopwords(["a"]) != Stopwords(["a", "b"])

    def test_equality_to_set(self) -> None:
        assert Stopwords(["a", "b"]) == {"a", "b"}

    def test_equality_to_frozenset(self) -> None:
        assert Stopwords(["a", "b"]) == frozenset({"a", "b"})

    def test_equality_to_unrelated_type_returns_not_implemented(self) -> None:
        # Falls back to ``object.__eq__`` which is False.
        assert (Stopwords(["a"]) == "a") is False

    def test_repr_includes_count(self) -> None:
        assert repr(Stopwords(["a", "b"])) == "Stopwords(2 words)"


class TestStopwordsConstant:
    def test_is_frozenset(self) -> None:
        assert isinstance(STOPWORDS, frozenset)

    def test_membership(self) -> None:
        assert "ଓ" in STOPWORDS
        assert "ଆଉ" in STOPWORDS

    def test_no_duplicates(self) -> None:
        assert len(STOPWORDS) == len(set(STOPWORDS))


class TestRemoveStopwordsIntegration:
    """``ud.remove_stopwords`` must accept the new optional ``stopwords`` kwarg."""

    def test_default_unchanged(self) -> None:
        # Behavior with no kwarg matches pre-change behavior.
        out = ud.remove_stopwords("ରାମ ଓ ସୀତା ଆମକୁ ଆଶୀର୍ବାଦ ଦେଇଛନ୍ତି")
        assert "ଓ" not in out
        assert "ଦେଇଛନ୍ତି" not in out
        assert "ରାମ" in out

    def test_accepts_stopwords_instance(self) -> None:
        custom = Stopwords(["ରାମ"])
        out = ud.remove_stopwords("ରାମ ଓ ସୀତା", stopwords=custom)
        assert "ରାମ" not in out
        # The bundled "ଓ" is no longer filtered because the user passed a
        # narrower list.
        assert "ଓ" in out

    def test_accepts_frozenset(self) -> None:
        out = ud.remove_stopwords("ରାମ ଓ ସୀତା", stopwords=frozenset({"ସୀତା"}))
        assert "ସୀତା" not in out
        assert "ରାମ" in out

    def test_accepts_list(self) -> None:
        out = ud.remove_stopwords("ରାମ ଓ ସୀତା", stopwords=["ରାମ", "ସୀତା"])
        assert "ରାମ" not in out
        assert "ସୀତା" not in out

    def test_get_str_combined_with_custom_stopwords(self) -> None:
        out = ud.remove_stopwords(
            "ରାମ ଓ ସୀତା",
            get_str=True,
            stopwords=Stopwords(["ଓ"]),
        )
        assert out == "ରାମ ସୀତା"
