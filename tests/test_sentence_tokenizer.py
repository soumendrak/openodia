import json
import time
from pathlib import Path

import pytest

from openodia import ud

GOLD = json.loads((Path(__file__).parent / "fixtures" / "gold_sentences.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", GOLD, ids=[case["name"] for case in GOLD])
def test_gold_sentences(case: dict[str, object]) -> None:
    assert ud.sentence_tokenizer(case["text"]) == case["sentences"]


@pytest.mark.parametrize("case", GOLD, ids=[case["name"] for case in GOLD])
def test_no_text_is_lost(case: dict[str, object]) -> None:
    assert "".join("".join(s.split()) for s in ud.sentence_tokenizer(case["text"])) == "".join(case["text"].split())


def test_returns_list_of_str() -> None:
    result = ud.sentence_tokenizer("ରାମ ଗଲା । ସୀତା ଆସିଲା ।")
    assert isinstance(result, list)
    assert all(isinstance(sentence, str) for sentence in result)


def test_large_text_is_linear() -> None:
    text = "ରାମ ଗଲା ଘରକୁ? ସେ ଆସିଲା! ଏହା ଏକ ବାକ୍ୟ ।" * 50_000
    start = time.perf_counter()
    result = ud.sentence_tokenizer(text)
    assert len(result) == 150_000
    assert time.perf_counter() - start < 10
