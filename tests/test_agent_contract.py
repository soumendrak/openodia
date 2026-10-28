import json
import re
import tomllib
from pathlib import Path

import pytest

from openodia import cli

ROOT = Path(__file__).resolve().parent.parent
DOCS = ["AGENTS.md", "skills/openodia/SKILL.md", "README.md", "docs/llms.txt", "docs/index.md"]
LINK = re.compile(r"\]\(([^)\s]+)\)")
SITE = "https://openodia.soumendrak.com/"
BLOB = "https://github.com/soumendrak/openodia/blob/main/"
PROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["name"]
AGENTS = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

SAMPLES = {
    "tokenize": [["tokenize", "ରାମ ସୀତା"], ["tokenize", "--sentences", "ରାମ ସୀତା"]],
    "normalize": [["normalize", "ରାମ"]],
    "clean": [["clean", "ରାମ"]],
    "translate": [["translate", "good morning"]],
    "detect-language": [["detect-language", "ରାମ ସୀତା ଘରକୁ ଯାଏ"], ["detect-language", ""]],
    "name": [["name", "--count", "1"]],
    "summarize": [["summarize", "ରାମ ସୀତା ଘରକୁ ଯାଏ । ସେ ଭଲ ଲୋକ ।"]],
    "remove-stopwords": [["remove-stopwords", "ରାମ ସୀତା"], ["remove-stopwords", "--get-str", "ରାମ ସୀତା"]],
    "ngrams": [["ngrams", "-n", "2", "ରାମ ସୀତା ଘରକୁ"]],
    "freq": [["freq", "ରାମ ସୀତା ରାମ"]],
    "pii": [["pii", "a@b.com"], ["pii", "--mask", "a@b.com"]],
}


def table_rows(heading: str) -> list[list[str]]:
    section = AGENTS.split(f"## {heading}")[1].split("\n## ")[0]
    rows = [line for line in section.splitlines() if line.startswith("|")][2:]
    return [[cell.strip() for cell in row.strip("|").split("|")] for row in rows]


def json_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {key for item in value.values() for key in json_keys(item)}
    if isinstance(value, list):
        return {key for item in value for key in json_keys(item)}
    return set()


def run_json(argv: list[str], capsys: pytest.CaptureFixture[str]) -> object:
    capsys.readouterr()
    assert cli.main([*argv, "--json"]) == 0
    return json.loads(capsys.readouterr().out)


@pytest.mark.parametrize("doc", DOCS)
def test_doc_links_resolve(doc: str) -> None:
    base = (ROOT / doc).parent
    text = (ROOT / doc).read_text(encoding="utf-8")
    for url in LINK.findall(text):
        if url.startswith(BLOB):
            assert (ROOT / url.removeprefix(BLOB)).is_file(), url
        elif url.startswith(SITE):
            page = url.removeprefix(SITE)
            target = (
                ROOT / "docs" / (f"{page.rstrip('/')}.md" if page.endswith("/") else page) if page else ROOT / "docs/index.md"
            )
            assert target.is_file(), url
        elif "://" not in url:
            assert (base / url.split("#")[0]).exists(), url


def test_llms_txt_pypi_link_is_this_project() -> None:
    text = (ROOT / "docs/llms.txt").read_text(encoding="utf-8")
    assert f"[PyPI](https://pypi.org/project/{PROJECT}/)" in text


@pytest.mark.parametrize("doc", DOCS)
def test_doc_states_which_release_has_json(doc: str) -> None:
    text = (ROOT / doc).read_text(encoding="utf-8")
    assert "needs a release newer than 0.1.14" in text
    assert "`detect-language` only" in text


@pytest.mark.parametrize("doc", [*DOCS, "docs/application.md"])
def test_doc_that_mentions_pii_states_which_release_has_it(doc: str) -> None:
    text = (ROOT / doc).read_text(encoding="utf-8")
    if "pii" in text.lower():
        assert "`openodia pii` exits 2 on 0.1.14" in text
        assert "`import openodia.pii` fails" in text


def test_llms_txt_leads_with_the_version_note() -> None:
    lines = (ROOT / "docs/llms.txt").read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("# ")
    assert lines[2].startswith("> ")
    assert "0.1.14" in lines[4]


def test_json_shapes_table_covers_every_subcommand() -> None:
    documented = {name for row in table_rows("JSON shapes") for name in re.findall(r"`([a-z-]+)`", row[0])}
    assert documented == set(SAMPLES)


@pytest.mark.parametrize("row", table_rows("JSON shapes"), ids=lambda row: row[0])
def test_documented_json_keys_match_real_output(row: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    commands = re.findall(r"`([a-z-]+)`", row[0])
    documented = set(re.findall(r'"(\w+)":', row[1]))
    actual: set[str] = set()
    for command in commands:
        for argv in SAMPLES[command]:
            actual |= json_keys(run_json(argv, capsys))
    assert documented == actual


def test_documented_exit_codes_match_real_behaviour(capsys: pytest.CaptureFixture[str]) -> None:
    documented = {int(row[0]) for row in table_rows("Exit codes and errors")}
    assert documented == {0, 1, 2, 141}
    assert cli.main(["tokenize", "x"]) == 0
    assert cli.main(["tokenize", "--file", "missing-file.txt"]) == 1
    assert capsys.readouterr().err.startswith("openodia: error: ")
    with pytest.raises(SystemExit) as exc:
        cli.main(["tokenize"])
    assert exc.value.code == 2


@pytest.mark.parametrize("doc", ["AGENTS.md", "docs/index.md"])
def test_pii_docs_say_what_stdin_does_to_offsets_and_how_far_mask_can_be_trusted(doc: str) -> None:
    text = (ROOT / doc).read_text(encoding="utf-8")
    assert "`-` (stdin) drops a leading BOM only" in text
    assert "keeps any `\\r`" in text
    assert "for `--file` and `-`" not in text
    assert "can still contain raw PII" in text
    assert "`HTTPS://` and `WWW.`" in text
    assert "turns CRLF and a lone CR into LF" in text
    assert "``. _ % + - ! # $ & ' * / = ? ^ ` { | } ~``" in text


@pytest.mark.parametrize("doc", ["AGENTS.md", "docs/index.md"])
def test_pii_docs_qualify_the_masking_guarantee_and_name_the_email_limits(doc: str) -> None:
    text = (ROOT / doc).read_text(encoding="utf-8")
    assert "for every detected value" in text
    assert "see the limits below" in text
    assert "never leaves half of a value visible" not in text
    assert "no part of a value stays visible" not in text
    assert "`ଅଭିa@x.com`" in text
    assert "deliberate limit" in text
    assert "quadratic" not in text


def test_pii_docs_and_changelog_and_docstring_do_not_overclaim_masking() -> None:
    from openodia.pii import detect

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "never leaves part of a value visible" not in changelog
    assert "for every detected value" in changelog
    assert "see the limits below" in changelog
    assert detect.__doc__ is not None
    assert "no part of a value is left visible" not in detect.__doc__
    assert "for every detected value" in detect.__doc__
    assert "see the limits below" in detect.__doc__


def test_pii_index_documents_the_over_masking_of_leading_delimiters() -> None:
    text = (ROOT / "docs/index.md").read_text(encoding="utf-8")
    assert "`key=val@host.com`" in text
    assert "`ssh://git@host.com` loses `//`" in text
    assert "`ssh://git@host` has no top-level domain and stays unchanged" in text
    assert "`ssh://git@host` loses `//`" not in text
    assert "`www.x.com/a@b.com`" in text
    assert "nothing leaks" in text


def test_pii_index_documents_the_domain_label_limit_and_url_apostrophes() -> None:
    text = (ROOT / "docs/index.md").read_text(encoding="utf-8")
    assert "A domain label over 63 characters is not matched" in text
    assert "`<EMAIL>b.com`" in text
    assert "(`a@` + 64 `b` + `.com` is unchanged)" in text
    assert "an apostrophe inside the URL is part of it" in text


def test_pii_index_says_a_closing_apostrophe_is_swallowed_when_a_url_character_follows() -> None:
    text = (ROOT / "docs/index.md").read_text(encoding="utf-8")
    assert "unless a URL character follows it" in text
    assert "`'https://a.com/x'+p`" in text
    assert "`'https://a.com/x'9876543210`" in text
    assert "one that closes a quoted URL, ends it" not in text
    assert "trailing `. , ; : ! ? ) ]` and `।` are left out" in text
