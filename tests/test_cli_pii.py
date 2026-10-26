import json

import pytest

from openodia import cli

TEXT = "ମୋ ଫୋନ ୯୮୭୬୫୪୩୨୧୦ ଓ a@b.com"
PHONE = {"type": "PHONE", "text": "୯୮୭୬୫୪୩୨୧୦", "start": 7, "end": 17, "confidence": 0.9}
EMAIL = {"type": "EMAIL", "text": "a@b.com", "start": 20, "end": 27, "confidence": 0.95}


def run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> str:
    capsys.readouterr()
    assert cli.main(["pii", *argv]) == 0
    return capsys.readouterr().out


def test_json_lists_entities(capsys: pytest.CaptureFixture[str]) -> None:
    assert json.loads(run([TEXT, "--json"], capsys)) == {"entities": [PHONE, EMAIL]}


def test_json_with_nothing_found(capsys: pytest.CaptureFixture[str]) -> None:
    assert json.loads(run(["ରାମ ସୀତା", "--json"], capsys)) == {"entities": []}


def test_text_output_is_tab_separated(capsys: pytest.CaptureFixture[str]) -> None:
    assert run([TEXT], capsys) == "PHONE\t7\t17\t୯୮୭୬୫୪୩୨୧୦\nEMAIL\t20\t27\ta@b.com\n"


def test_mask_prints_masked_text(capsys: pytest.CaptureFixture[str]) -> None:
    assert run([TEXT, "--mask"], capsys) == "ମୋ ଫୋନ <PHONE> ଓ <EMAIL>\n"


def test_mask_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert json.loads(run([TEXT, "--mask", "--json"], capsys)) == {"text": "ମୋ ଫୋନ <PHONE> ଓ <EMAIL>"}


def test_type_option_repeats(capsys: pytest.CaptureFixture[str]) -> None:
    only_email = json.loads(run([TEXT, "--type", "EMAIL", "--json"], capsys))
    assert only_email == {"entities": [EMAIL]}
    both = json.loads(run([TEXT, "--type", "EMAIL", "--type", "PHONE", "--json"], capsys))
    assert both == {"entities": [PHONE, EMAIL]}


def test_min_confidence(capsys: pytest.CaptureFixture[str]) -> None:
    assert json.loads(run([TEXT, "--min-confidence", "0.92", "--json"], capsys)) == {"entities": [EMAIL]}


def test_unknown_type_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["pii", TEXT, "--type", "NAME"])
    assert exc.value.code == 2


def test_reads_stdin(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO("a@b.com"))
    assert run(["-", "--mask"], capsys) == "<EMAIL>\n"
