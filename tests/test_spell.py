"""Odia spell checking: dictionary lookup, suggestions, and in-place correction."""

import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter

import pytest

from openodia.common.constants import STOPWORDS
from openodia.corpus.dictionary import get_dictionary
from openodia.syllable import split

WORD = re.compile(r"[\u0b00-\u0b63\u0b71\u200c\u200d]+")


def _has_base(token: str) -> bool:
    for char in token:
        code = ord(char)
        if 0x0B05 <= code <= 0x0B39 or 0x0B5C <= code <= 0x0B61 or code == 0x0B71:
            return True
    return False


def test_known_and_unknown_words_are_stable() -> None:
    from openodia import spell

    assert spell.is_correct("ନମସ୍କାର") is True
    assert spell.is_correct("ନମସ୍କର") is False
    assert spell.is_correct("") is False
    assert spell.is_correct("hello") is False
    assert spell.is_correct("ନମସ୍କାର") is True


def test_stopwords_missing_from_the_dictionary_count_as_correct() -> None:
    from openodia import spell

    assert spell.is_correct("ଲେଖାଏଁ") is True
    assert spell.correct_text("ଲେଖାଏଁ ଆସିଛନ୍ତି") == "ଲେଖାଏଁ ଆସିଛନ୍ତି"
    for word in STOPWORDS:
        token = unicodedata.normalize("NFC", word)
        if _has_base(token):
            assert spell.is_correct(token) is True


def test_suggest_ranks_the_issue_examples_first() -> None:
    from openodia import spell

    assert spell.suggest("ନମସ୍କାର") == ["ନମସ୍କାର"]
    assert spell.suggest("ନମସ୍କାର", top_k=3) == ["ନମସ୍କାର"]
    assert spell.suggest("ନମସ୍କର", top_k=1) == ["ନମସ୍କାର"]
    assert spell.suggest("ଆସୁଛନ୍ତ", top_k=1) == ["ଆସୁଛନ୍ତି"]
    assert spell.suggest("ସୁବିଧାଁ", top_k=1) == ["ସୁବିଧା"]
    suggestions = spell.suggest("ନମସ୍କର", top_k=5)
    assert suggestions[0] == "ନମସ୍କାର"
    assert len(suggestions) <= 5
    assert len(suggestions) == len(set(suggestions))
    assert spell.suggest("ନମସ୍କର", top_k=5) == suggestions
    assert spell.suggest("ନମସ୍କର", top_k=1) == suggestions[:1]


def test_suggest_finds_an_adjacent_transposition() -> None:
    from openodia import spell

    assert "ନମସ୍କାର" in spell.suggest("ମନସ୍କାର", top_k=5)


def test_suggest_finds_a_swap_combined_with_an_insertion() -> None:
    from openodia import spell

    assert spell.is_correct("ସହିତ") is True
    assert "ସହିତ" in spell.suggest("ତସ", top_k=100_000)


def test_suggest_returns_the_requested_number_of_candidates() -> None:
    from openodia import spell

    assert spell.suggest("ନମସ୍କର", top_k=5) == ["ନମସ୍କାର", "ଚମତ୍କାର", "ତୁମର", "ନରମ", "ମଟର"]


def test_suggest_of_a_dictionary_word_with_top_k_zero_is_empty() -> None:
    from openodia import spell

    assert spell.suggest("ନମସ୍କାର", top_k=0) == []


def test_equal_distance_and_frequency_break_ties_by_code_point() -> None:
    from openodia import spell

    assert spell.suggest("ତସ", top_k=40)[7] == "ତଳ"


def test_is_correct_normalizes_to_nfc() -> None:
    from openodia import spell

    nfd = unicodedata.normalize("NFD", "କୋଣ")
    assert nfd != "କୋଣ"
    assert spell.is_correct(nfd) is True


def test_a_word_two_substitutions_away_stays_a_candidate() -> None:
    from openodia import spell

    assert "ନମସ୍କାର" in spell.suggest("ଖଖସ୍କାର", top_k=20)


def test_two_inserted_aksharas_stay_inside_the_distance_window() -> None:
    from openodia import spell

    assert "ନମସ୍କାର" in spell.suggest("ସ୍କାର", top_k=100_000)


def test_two_deleted_aksharas_stay_inside_the_distance_window() -> None:
    from openodia import spell

    assert "ନମସ୍କାର" in spell.suggest("ନମସ୍କାରକର", top_k=20)


def test_correct_text_leaves_lone_vowel_signs() -> None:
    from openodia import spell

    assert spell.correct_text("ି ୍") == "ି ୍"
    from openodia import spell

    assert spell.suggest("ନମସ୍କର", top_k=0) == []
    assert spell.suggest("") == []
    distant = "କ" * 40
    assert spell.suggest(distant) == []
    assert spell.correct_text(distant) == distant
    with pytest.raises(ValueError):
        spell.suggest("ନମସ୍କର", top_k=-1)
    with pytest.raises(TypeError):
        spell.suggest("ନମସ୍କର", top_k=True)


def test_correct_text_preserves_whitespace_punctuation_and_non_odia() -> None:
    from openodia import spell

    assert spell.correct_text("ସେ ଆମ ଘରକୁ ଆସୁଛନ୍ତ") == "ସେ ଆମ ଘରକୁ ଆସୁଛନ୍ତି"
    assert spell.correct_text("ସେ  ଆମ\tଘରକୁ\nଆସୁଛନ୍ତ!") == "ସେ  ଆମ\tଘରକୁ\nଆସୁଛନ୍ତି!"
    assert spell.correct_text("(ନମସ୍କର), ନମସ୍କାର।") == "(ନମସ୍କାର), ନମସ୍କାର।"
    assert spell.correct_text("hello, ନମସ୍କର! ୧୨୩") == "hello, ନମସ୍କାର! ୧୨୩"
    assert spell.correct_text("ସୁବିଧାଁ") == "ସୁବିଧା"
    assert spell.correct_text("") == ""
    assert spell.correct_text("   ") == "   "
    assert spell.correct_text("ନମସ୍କାର") == "ନମସ୍କାର"


def _typo(word: str, kind: str, index: int) -> str:
    parts = list(split(word))
    if kind == "del":
        del parts[index % len(parts)]
    elif kind == "sub":
        parts[index % len(parts)] = "ଖ" if parts[index % len(parts)] == "କ" else "କ"
    elif kind == "swap":
        cursor = index % (len(parts) - 1)
        parts[cursor], parts[cursor + 1] = parts[cursor + 1], parts[cursor]
    else:
        parts.insert(index % (len(parts) + 1), "ଅ")
    return "".join(parts)


def _frequent_typos(limit: int = 100) -> list[tuple[str, str]]:
    from openodia import spell

    counts: Counter[str] = Counter()
    for value in get_dictionary().values():
        for word in WORD.findall(unicodedata.normalize("NFC", value)):
            if _has_base(word):
                counts[word] += 1
    pairs: list[tuple[str, str]] = []
    kinds = ("del", "sub", "swap", "ins")
    for number, word in enumerate(word for word, _count in counts.most_common() if len(split(word)) >= 3):
        typo = _typo(word, kinds[number % 4], 1)
        if typo != word and not spell.is_correct(typo):
            pairs.append((typo, word))
        if len(pairs) == limit:
            break
    return pairs


def test_suggestion_accuracy_on_one_hundred_typos() -> None:
    from openodia import spell

    pairs = _frequent_typos()
    assert len(pairs) == 100
    top1 = 0
    top5 = 0
    for typo, word in pairs:
        suggestions = spell.suggest(typo, top_k=5)
        assert len(suggestions) <= 5
        top1 += suggestions[:1] == [word]
        top5 += word in suggestions
    assert top1 >= 70
    assert top5 >= 90


def test_cli_corrects_suggests_and_checks(capsys: pytest.CaptureFixture[str]) -> None:
    from openodia import cli

    assert cli.main(["spell", "ସେ ଆମ ଘରକୁ ଆସୁଛନ୍ତ"]) == 0
    assert capsys.readouterr().out == "ସେ ଆମ ଘରକୁ ଆସୁଛନ୍ତି\n"
    assert cli.main(["spell", "--json", "ସେ ଆମ ଘରକୁ ଆସୁଛନ୍ତ"]) == 0
    assert json.loads(capsys.readouterr().out) == {"text": "ସେ ଆମ ଘରକୁ ଆସୁଛନ୍ତି"}
    assert cli.main(["spell", "--suggest", "--top", "1", "ନମସ୍କର"]) == 0
    assert capsys.readouterr().out == "ନମସ୍କାର\n"
    assert cli.main(["spell", "--suggest", "--top", "1", "--json", "ନମସ୍କର"]) == 0
    assert json.loads(capsys.readouterr().out) == {"suggestions": ["ନମସ୍କାର"]}
    assert cli.main(["spell", "--check", "ନମସ୍କାର"]) == 0
    assert capsys.readouterr().out == "true\n"
    assert cli.main(["spell", "--check", "--json", "ନମସ୍କର"]) == 0
    assert json.loads(capsys.readouterr().out) == {"correct": False}
    assert cli.main(["spell", "--suggest", "--json", "କ" * 40]) == 0
    assert json.loads(capsys.readouterr().out) == {"suggestions": []}


def test_cli_check_ignores_one_trailing_newline(tmp_path) -> None:
    piped = subprocess.run(
        [sys.executable, "-m", "openodia", "spell", "--check", "-"],
        input="ନମସ୍କାର\n".encode(),
        capture_output=True,
        check=False,
    )
    assert piped.returncode == 0
    assert piped.stdout == b"true\n"
    crlf = subprocess.run(
        [sys.executable, "-m", "openodia", "spell", "--check", "-"],
        input="ନମସ୍କାର\r\n".encode(),
        capture_output=True,
        check=False,
    )
    assert crlf.returncode == 0
    assert crlf.stdout == b"true\n"
    lone_cr = subprocess.run(
        [sys.executable, "-m", "openodia", "spell", "--check", "-"],
        input="ନମସ୍କାର\r".encode(),
        capture_output=True,
        check=False,
    )
    assert lone_cr.returncode == 0
    assert lone_cr.stdout == b"true\n"
    path = tmp_path / "word.txt"
    path.write_bytes("ନମସ୍କାର\n".encode())
    filed = subprocess.run(
        [sys.executable, "-m", "openodia", "spell", "--check", "--json", "--file", str(path)],
        capture_output=True,
        check=False,
    )
    assert filed.returncode == 0
    assert json.loads(filed.stdout) == {"correct": True}


def test_cli_file_keeps_the_newline(tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    from openodia import cli

    path = tmp_path / "in.txt"
    path.write_text("ନମସ୍କର ।\n", encoding="utf-8")
    assert cli.main(["spell", "--file", str(path)]) == 0
    assert capsys.readouterr().out == "ନମସ୍କାର ।\n\n"


def test_cli_rejects_bad_spell_usage() -> None:
    from openodia import cli

    with pytest.raises(SystemExit) as exclusive:
        cli.main(["spell", "--suggest", "--check", "ନମସ୍କାର"])
    assert exclusive.value.code == 2
    with pytest.raises(SystemExit) as negative:
        cli.main(["spell", "--suggest", "--top", "-1", "ନମସ୍କର"])
    assert negative.value.code == 2
