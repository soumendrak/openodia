import json
import random
import time
from pathlib import Path

import pytest

from openodia import ud

GOLD = json.loads((Path(__file__).parent / "fixtures" / "gold_sentences.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", GOLD, ids=[case["name"] for case in GOLD])
def test_gold_sentences(case: dict[str, object]) -> None:
    assert ud.sentence_tokenizer(case["text"]) == case["sentences"]


@pytest.mark.parametrize("case", GOLD, ids=[case["name"] for case in GOLD])
def test_no_text_is_lost_in_gold_cases(case: dict[str, object]) -> None:
    assert_text_kept(case["text"])


def test_returns_list_of_str() -> None:
    result = ud.sentence_tokenizer("ରାମ ଗଲା । ସୀତା ଆସିଲା ।")
    assert isinstance(result, list)
    assert all(isinstance(sentence, str) for sentence in result)


def test_large_text_is_linear() -> None:
    text = "ରାମ ଗଲା ଘରକୁ? ସେ ଆସିଲା! ଏହା ଏକ ବାକ୍ୟ ।" * 50_000
    start = time.perf_counter()
    result = ud.sentence_tokenizer(text)
    assert len(result) == 150_000
    assert time.perf_counter() - start < 2


WORDS = ["ରାମ", "ସୀତା", "ଗଲା", "ଘରକୁ", "୧୨୩", "a", "Hello", "?q=1", "a?id=5", "Yahoo!Mail", "😀", ".", ",", "…"]
TERMINATORS = ["।", "॥", "?", "!", "।।", "?!"]
CLOSERS = ['"', "'", "”", ")", "]", "}", ">", "(", "{", "<"]
SPACES = [" ", " ", " ", "\t", "\n", "\r\n", "\r", "\u2028", "\u2029"]
PIECES = WORDS + TERMINATORS + CLOSERS + SPACES

LONG = 400_000
PATHOLOGICAL = {
    "stray terminators after a sentence": "ରାମ।" + " ।" * LONG,
    "stray question marks after a word": "ରାମ" + " ?!" * LONG,
    "leading stray terminators": "। " * LONG + "ରାମ",
    "leading mixed terminators": "। ? ! " * (LONG // 2) + "ରାମ",
    "alternating closers": "ରାମ।" + ')"' * LONG,
    "long run of closers": "ରାମ।" + ")" * (2 * LONG),
    "many terminator runs": "ରାମ" + "?!" * LONG,
    "spaced closers": "ରାମ। ) " * LONG,
    "no terminator": "ରାମ " * LONG,
    "one long word": "ରାମ" * LONG,
}


@pytest.mark.parametrize("name", PATHOLOGICAL)
def test_pathological_shapes_are_linear(name: str) -> None:
    text = PATHOLOGICAL[name]
    start = time.perf_counter()
    result = ud.sentence_tokenizer(text)
    assert time.perf_counter() - start < 2
    assert squash("".join(result)) == squash(text)


def random_texts(count: int = 5000, seed: int = 20260427) -> list[str]:
    rng = random.Random(seed)
    return ["".join(rng.choices(PIECES, k=rng.randint(0, 14))) for _ in range(count)]


TEXTS = random_texts()


def squash(text: str) -> str:
    return "".join(text.split())


def has_word(text: str) -> bool:
    return any(char.isalnum() for char in text)


def assert_text_kept(text: str) -> None:
    parts = ud.sentence_tokenizer(text)
    expected = squash(text) if has_word(text) else ""
    assert squash("".join(parts)) == expected, (text, parts)


def test_every_part_has_a_word() -> None:
    for text in TEXTS:
        for part in ud.sentence_tokenizer(text):
            assert has_word(part), (text, part)


def test_parts_are_trimmed_and_not_empty() -> None:
    for text in TEXTS:
        for part in ud.sentence_tokenizer(text):
            assert part
            assert part == part.strip(), (text, part)


def test_no_text_is_lost() -> None:
    for text in TEXTS:
        assert_text_kept(text)


def test_splitting_the_joined_parts_gives_the_same_parts() -> None:
    for text in TEXTS:
        parts = ud.sentence_tokenizer(text)
        assert ud.sentence_tokenizer(" ".join(parts)) == parts, (text, parts)
