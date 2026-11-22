import ast
import hashlib
import json
import random
import re
from collections.abc import Iterator
from pathlib import Path
from typing import cast

import pytest

from openodia import legacy

ROOT = Path(__file__).resolve().parents[1]
UNDEFINED = (0x81, 0x8D, 0x8F, 0x90, 0x9D)
RELEASE_SENTENCE = "`openodia.legacy` needs a release newer than 0.2.0: `import openodia.legacy` fails on 0.2.0."
RELEASE_PAGES = ("README.md", "docs/index.md", "docs/llms.txt", "AGENTS.md", "CHANGELOG.md")
DECODE_PAGES = ("README.md", "docs/index.md", "docs/llms.txt", "CHANGELOG.md", "openodia/legacy/_decode.py")
EXAMPLE_PAGES = ("README.md", "docs/index.md")
EXAMPLE = re.compile(r'^legacy\.decode\((b"[^"]*")\)  # (\'[^\']*\')$', re.MULTILINE)


def _expected_decode(data: bytes) -> str:
    return "".join(chr(byte) if byte in UNDEFINED else bytes([byte]).decode("cp1252") for byte in data)


def _shuffled_triples() -> bytes:
    data = bytearray(bytes(range(256)) * 3)
    random.Random(305).shuffle(data)
    return bytes(data)


LONG_BYTES = bytes(range(256)) * 3
SHUFFLED_BYTES = _shuffled_triples()


def _page(name: str) -> str:
    return " ".join((ROOT / name).read_text(encoding="utf-8").split())


def test_cp1252_leaves_exactly_these_bytes_undefined() -> None:
    assert tuple(byte for byte in range(256) if bytes([byte]).decode("cp1252", "ignore") == "") == UNDEFINED


def test_decode_uses_cp1252_for_every_defined_byte_and_keeps_the_undefined_ones() -> None:
    data = bytes(range(256))
    expected = "".join(chr(byte) if byte in UNDEFINED else bytes([byte]).decode("cp1252") for byte in data)
    assert legacy.decode(data) == expected
    assert legacy.decode(bytearray(data)) == expected


@pytest.mark.parametrize(("byte", "expected"), [(0x85, "\u2026"), (0x80, "\u20ac"), (0x9F, "\u0178"), (0x8D, "\x8d")])
def test_decode_is_cp1252_and_not_latin_1(byte: int, expected: str) -> None:
    assert legacy.decode(bytes([byte])) == expected


class _Replaying(bytes):
    def __iter__(self) -> Iterator[int]:
        return iter([65])


class _ReplayingArray(bytearray):
    def __iter__(self) -> Iterator[int]:
        return iter([65])


def test_decode_reads_the_buffer_of_a_bytes_subclass() -> None:
    assert legacy.decode(_Replaying(b"xyz")) == "xyz"
    assert legacy.decode(_ReplayingArray(b"xyz")) == "xyz"


def test_decode_of_empty_bytes_is_empty() -> None:
    assert legacy.decode(b"") == ""
    assert legacy.decode(bytearray()) == ""


def test_long_decode_inputs_are_longer_than_256_bytes() -> None:
    assert len(LONG_BYTES) == len(SHUFFLED_BYTES) == 768
    assert SHUFFLED_BYTES != LONG_BYTES
    assert sorted(SHUFFLED_BYTES) == sorted(LONG_BYTES)


@pytest.mark.parametrize(
    "data",
    [
        b" J \r\n",
        b"\t leading",
        b"trailing \t",
        b"trailing ",
        b" ",
        b" \t\r\n",
        b"\r\n",
        b"\r",
        b"\n",
        b"\x00",
        b"\x00 \t\r\n\x00",
        LONG_BYTES,
        SHUFFLED_BYTES,
    ],
    ids=[
        "space-J-space-crlf",
        "tab-leading",
        "trailing-tab",
        "trailing-space",
        "space-only",
        "whitespace-only",
        "crlf",
        "cr",
        "lf",
        "nul",
        "nul-and-whitespace",
        "three-copies-of-every-byte",
        "shuffled-three-copies",
    ],
)
def test_decode_keeps_the_length_and_bytes_of_whitespace_newlines_and_long_inputs(data: bytes) -> None:
    expected = _expected_decode(data)
    assert len(expected) == len(data)
    assert legacy.decode(data) == expected
    assert len(legacy.decode(data)) == len(data)
    assert legacy.decode(bytearray(data)) == expected


@pytest.mark.parametrize("value", ["JX", memoryview(b"JX"), None, 74])
def test_decode_rejects_anything_but_bytes(value: object) -> None:
    with pytest.raises(TypeError, match="legacy font bytes are required"):
        legacy.decode(cast(bytes, value))


@pytest.mark.parametrize("page", RELEASE_PAGES)
def test_legacy_pages_name_the_release(page: str) -> None:
    assert RELEASE_SENTENCE in _page(page)


@pytest.mark.parametrize("page", DECODE_PAGES)
def test_pages_name_every_byte_cp1252_leaves_undefined(page: str) -> None:
    assert "cp1252" in _page(page)
    assert "0x81, 0x8D, 0x8F, 0x90 and 0x9D" in _page(page)


@pytest.mark.parametrize("page", EXAMPLE_PAGES)
def test_the_decode_example_on_each_page_is_what_decode_gives(page: str) -> None:
    examples = EXAMPLE.findall((ROOT / page).read_text(encoding="utf-8"))
    assert len(examples) == 1
    for data, expected in examples:
        assert repr(legacy.decode(ast.literal_eval(data))) == expected


def test_package_exports_the_module_once() -> None:
    import openodia

    assert openodia.legacy is legacy
    assert openodia.__all__.count("legacy") == 1
    assert legacy.__all__ == ["SUPPORTED_FONTS", "decode", "to_unicode"]


ORTT_TABLE_SHA256 = "d3fed7fae959f65f9e9fa777e40a7e20481616f059057cedddebb154e8763e76"


def test_the_ortt_table_is_the_reference_table_with_one_pair_per_line() -> None:
    source = ROOT / "openodia" / "legacy" / "fonts" / "ORTTSarala.json"
    with source.open(encoding="utf-8") as handle:
        table = json.load(handle)
    canonical = json.dumps(table, sort_keys=True, ensure_ascii=False).encode("utf-8")
    assert hashlib.sha256(canonical).hexdigest() == ORTT_TABLE_SHA256
    pair_lines = [line for line in source.read_text(encoding="utf-8").splitlines() if line.startswith("    [")]
    assert len(pair_lines) == len(table["pairs"]) == 186
