import pytest

from openodia import sentences
from openodia.segment import ABBREVIATIONS


class TestBasicSplits:
    def test_three_sentences_with_mixed_terminators(self) -> None:
        out = sentences("ଆଜି ୨.୫ କୋଟି। ଆଗକୁ କଣ? ଭଲ ଦିନ!")
        assert out == ["ଆଜି ୨.୫ କୋଟି।", "ଆଗକୁ କଣ?", "ଭଲ ଦିନ!"]

    def test_no_space_between_sentences(self) -> None:
        # The pre-existing tokenizer needed " ।" — the new one doesn't.
        out = sentences("ରାମ ଗଲା।ସୀତା ଆସିଲା।")
        assert out == ["ରାମ ଗଲା।", "ସୀତା ଆସିଲା।"]

    def test_double_danda(self) -> None:
        # Whitespace before the terminator is normalised away.
        out = sentences("ଶ୍ଳୋକ ଏକ ॥ ଶ୍ଳୋକ ଦୁଇ ॥")
        assert out == ["ଶ୍ଳୋକ ଏକ॥", "ଶ୍ଳୋକ ଦୁଇ॥"]

    def test_ellipsis_treated_as_terminator(self) -> None:
        out = sentences("ଭାବୁଛି… ତୁମେ କିଏ?")
        assert out == ["ଭାବୁଛି…", "ତୁମେ କିଏ?"]

    def test_run_of_terminators_stays_with_sentence(self) -> None:
        out = sentences("Really?! Yes!")
        assert out == ["Really?!", "Yes!"]


class TestDecimalsPreserved:
    def test_odia_digits_decimal(self) -> None:
        out = sentences("ଆଜି ୨.୫ କୋଟି।")
        assert out == ["ଆଜି ୨.୫ କୋଟି।"]

    def test_ascii_digits_decimal(self) -> None:
        out = sentences("Price is 12.50 only.")
        assert out == ["Price is 12.50 only."]

    def test_decimal_inside_multi_sentence_input(self) -> None:
        out = sentences("Cost 2.5 cr. Net 3.4 cr.")
        # Cost ... 2.5 cr — but "cr." is not in our abbreviation list, so
        # it's a real terminator. Result is two sentences.
        assert out == ["Cost 2.5 cr.", "Net 3.4 cr."]


class TestAbbreviations:
    def test_doctor_honorific(self) -> None:
        out = sentences("ଡଃ ସୁନୀତା ଆସିଲେ।")
        assert out == ["ଡଃ ସୁନୀତା ଆସିଲେ।"]

    def test_latin_eg(self) -> None:
        out = sentences("Use any tool, e.g. ripgrep. Done.")
        assert out == ["Use any tool, e.g. ripgrep.", "Done."]

    def test_latin_dr(self) -> None:
        out = sentences("Dr. Sahoo arrived. He left.")
        assert out == ["Dr. Sahoo arrived.", "He left."]

    def test_longest_match_wins(self) -> None:
        """``ଶ୍ରୀମତୀ`` and ``ଶ୍ରୀ`` share a prefix; longer must mask first."""
        out = sentences("ଶ୍ରୀମତୀ ଲତା ଗଲେ।")
        assert out == ["ଶ୍ରୀମତୀ ଲତା ଗଲେ।"]

    def test_abbreviations_constant_is_populated(self) -> None:
        assert "ଡଃ" in ABBREVIATIONS
        assert "Dr." in ABBREVIATIONS


class TestModes:
    def test_strict_ignores_latin_period(self) -> None:
        # Latin period is not a strict-mode terminator.
        out = sentences("Hi. ତୁମେ କେମିତି।", mode="strict")
        assert out == ["Hi. ତୁମେ କେମିତି।"]

    def test_default_splits_latin_period(self) -> None:
        out = sentences("Hi. ତୁମେ କେମିତି।")
        assert out == ["Hi.", "ତୁମେ କେମିତି।"]

    def test_unknown_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown mode"):
            sentences("Hi.", mode="loose")  # type: ignore[arg-type]


class TestKeepTerminators:
    def test_default_keeps_terminators(self) -> None:
        out = sentences("Hello. World!")
        assert out == ["Hello.", "World!"]

    def test_strip_terminators(self) -> None:
        out = sentences("Hello. World!", keep_terminators=False)
        assert out == ["Hello", "World"]


class TestEdgeCases:
    def test_empty(self) -> None:
        assert sentences("") == []

    def test_only_whitespace(self) -> None:
        assert sentences("   \n\t  ") == []

    def test_only_terminator(self) -> None:
        assert sentences("...") == []

    def test_single_sentence_no_terminator(self) -> None:
        assert sentences("ଏକା ବାକ୍ୟ") == ["ଏକା ବାକ୍ୟ"]

    def test_leading_punctuation_dropped(self) -> None:
        assert sentences(". hello world.") == ["hello world."]

    def test_internal_newlines_collapsed_into_whitespace(self) -> None:
        out = sentences("Hello.\n\nWorld.")
        assert out == ["Hello.", "World."]


class TestIdempotenceProperty:
    """Joining sentences then re-splitting should match the original split."""

    def test_round_trip(self) -> None:
        text = "ରାମ ଗଲା। ସୀତା ଆସିଲା। ଲକ୍ଷ୍ମଣ ଅଛନ୍ତି।"
        first = sentences(text)
        joined = " ".join(first)
        second = sentences(joined)
        assert first == second


class TestBackwardCompatibility:
    """The pre-existing ``ud.sentence_tokenizer`` must keep working unchanged."""

    def test_old_tokenizer_still_works(self) -> None:
        from openodia import ud

        # Same behaviour as before: splits on " ।".
        out = ud.sentence_tokenizer("ରାମ ଗଲା । ସୀତା ଆସିଲା ।")
        assert isinstance(out, list)
        assert len(out) > 0


class TestPublicAPI:
    def test_top_level_alias(self) -> None:
        import openodia

        assert openodia.sentences is sentences
