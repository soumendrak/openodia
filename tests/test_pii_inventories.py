import re
from pathlib import Path

import pytest

from openodia import pii

ROOT = Path(__file__).resolve().parents[1]
ONE_OF_EACH = {
    "PHONE": "9876543210",
    "EMAIL": "a@b.com",
    "URL": "https://example.org",
    "AADHAAR": "234567890124",
    "PAN": "ABCPE1234F",
    "PINCODE": "PIN 751001",
    "DATE": "15 January 2024",
}
WORDS = {
    "PHONE": ("phone", "mobile"),
    "EMAIL": ("email",),
    "URL": ("URL",),
    "AADHAAR": ("Aadhaar",),
    "PAN": ("PAN",),
    "PINCODE": ("PIN code",),
    "DATE": ("date",),
}
INVENTORIES = [
    ("docs/application.md", "#### Masking phone"),
    ("skills/openodia/SKILL.md", "description:"),
    ("skills/openodia/SKILL.md", "- `pii` is rule-based"),
    ("AGENTS.md", "`pii` finds"),
    ("docs/guides/pii.md", "`pii` finds"),
    ("docs/llms.txt", "- [PII guide]"),
    ("docs/index.md", "# Find or mask"),
    ("openodia/cli.py", '    p = sub.add_parser("pii"'),
    ("openodia/pii/__init__.py", '"""Detect and mask'),
]


def _types_mask_emits() -> set[str]:
    masked = pii.mask(" ; ".join(ONE_OF_EACH.values()))
    return set(re.findall(r"<([A-Z]+)>", masked))


def _line(path: str, start: str) -> str:
    lines = [line for line in (ROOT / path).read_text(encoding="utf-8").splitlines() if line.startswith(start)]
    assert len(lines) == 1, (path, start, lines)
    return lines[0]


def test_each_example_masks_to_its_own_tag_and_covers_every_type() -> None:
    assert set(ONE_OF_EACH) == set(pii.PII_TYPES) == set(WORDS)
    for kind, text in ONE_OF_EACH.items():
        assert pii.mask(text) == text.replace(text.removeprefix("PIN "), f"<{kind}>")
    assert _types_mask_emits() == set(pii.PII_TYPES)


def test_the_application_page_lists_every_tag_mask_emits() -> None:
    sentence = _line("docs/application.md", "- `openodia.pii.mask(text)` replaces them with")
    for kind in _types_mask_emits():
        assert f"`<{kind}>`" in sentence, kind


@pytest.mark.parametrize(("path", "start"), INVENTORIES)
def test_every_pii_inventory_names_every_type_mask_emits(path: str, start: str) -> None:
    assert len(INVENTORIES) == 9
    line = _line(path, start)
    for kind in _types_mask_emits():
        assert any(word in line for word in WORDS[kind]), (path, kind)
