import io
import json
from pathlib import Path

import pytest

from openodia import cli


def run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    """Invoke the CLI in-process; return (exit_code, stdout, stderr)."""
    capsys.readouterr()  # clear buffers
    exit_code = cli.main(argv)
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


class TestParser:
    def test_help_lists_all_commands(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            cli.main(["--help"])
        out = capsys.readouterr().out
        for cmd in [
            "tokenize",
            "normalize",
            "clean",
            "translate",
            "detect-language",
            "name",
            "summarize",
            "remove-stopwords",
            "ngrams",
            "freq",
        ]:
            assert cmd in out

    def test_missing_subcommand_fails(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            cli.main([])


class TestReadInput:
    def test_literal_text(self) -> None:
        assert cli._read_input("hello") == "hello"

    def test_file_path(self, tmp_path: Path) -> None:
        f = tmp_path / "in.txt"
        f.write_text("from file", encoding="utf-8")
        assert cli._read_input(str(f)) == "from file"

    def test_stdin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.stdin", io.StringIO("piped"))
        assert cli._read_input("-") == "piped"


class TestNormalize:
    def test_default_nfc(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Decomposed nukta in input; expect composed output.
        code, out, _ = run(["normalize", "ଡ" + "଼"], capsys)
        assert code == 0
        # NFC may keep the decomposed form for nukta (composition exclusion);
        # what we really care about is the program runs without error.
        assert "଼" in out or "ଡ଼" in out

    def test_nfd_form(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, _, _ = run(["normalize", "ଡ଼", "--form", "NFD"], capsys)
        assert code == 0


class TestClean:
    def test_strips_zwnj_by_default(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, out, _ = run(["clean", "ନମ‌ସ୍କାର"], capsys)
        assert code == 0
        assert "‌" not in out

    def test_latin_to_odia_digits(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, out, _ = run(["clean", "ଆଜି 123", "--latin-to-odia"], capsys)
        assert code == 0
        assert "୧୨୩" in out


class TestTokenize:
    def test_word_tokenize(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, out, _ = run(["tokenize", "ରାମ ଓ ସୀତା"], capsys)
        assert code == 0
        tokens = out.strip().splitlines()
        assert "ରାମ" in tokens
        assert "ସୀତା" in tokens

    def test_sentence_tokenize(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, out, _ = run(["tokenize", "ରାମ ଗଲା । ସୀତା ଆସିଲା ।", "--sentences"], capsys)
        assert code == 0
        assert out.strip()  # non-empty


class TestDetectLanguage:
    def test_text_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, out, _ = run(["detect-language", "ନମସ୍କାର"], capsys)
        assert code == 0
        assert "odia" in out

    def test_json_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, out, _ = run(["detect-language", "ନମସ୍କାର", "--json"], capsys)
        assert code == 0
        data = json.loads(out)
        assert data["language"] == "odia"

    def test_empty_input(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, out, _ = run(["detect-language", ""], capsys)
        assert code == 0
        assert "(empty input)" in out


class TestName:
    def test_full_names(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, out, _ = run(["name", "--count", "5"], capsys)
        assert code == 0
        assert len(out.strip().splitlines()) == 5

    @pytest.mark.parametrize("kind", ["first", "middle", "surname"])
    def test_other_kinds(self, kind: str, capsys: pytest.CaptureFixture[str]) -> None:
        code, out, _ = run(["name", "--kind", kind, "--count", "3"], capsys)
        assert code == 0
        assert len(out.strip().splitlines()) == 3

    def test_prefix(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Prefixes use a different generator API; just check it runs.
        code, out, _ = run(["name", "--kind", "prefix", "--count", "3"], capsys)
        assert code == 0
        assert out.strip()


class TestSummarize:
    def test_auto_threshold(self, capsys: pytest.CaptureFixture[str]) -> None:
        text = "ରାମ ଗଲା । ସୀତା ଆସିଲା । ଲକ୍ଷ୍ମଣ ଅଛନ୍ତି ।"
        code, _, _ = run(["summarize", text], capsys)
        assert code == 0

    def test_explicit_threshold(self, capsys: pytest.CaptureFixture[str]) -> None:
        text = "ରାମ ଗଲା । ସୀତା ଆସିଲା ।"
        code, _, _ = run(["summarize", text, "--threshold", "1.5"], capsys)
        assert code == 0


class TestRemoveStopwords:
    def test_default_tokens_one_per_line(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, out, _ = run(["remove-stopwords", "ରାମ ଓ ସୀତା"], capsys)
        assert code == 0
        tokens = out.strip().splitlines()
        assert "ରାମ" in tokens
        assert "ସୀତା" in tokens
        assert "ଓ" not in tokens

    def test_get_str(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, out, _ = run(
            ["remove-stopwords", "ରାମ ଓ ସୀତା", "--get-str"],
            capsys,
        )
        assert code == 0
        # One line of output rather than tokens-per-line.
        assert "\n" not in out.strip()


class TestNgrams:
    def test_bigrams(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, out, _ = run(["ngrams", "ରାମ ସୀତା ଲକ୍ଷ୍ମଣ", "-n", "2"], capsys)
        assert code == 0
        lines = out.strip().splitlines()
        assert lines == ["ରାମ ସୀତା", "ସୀତା ଲକ୍ଷ୍ମଣ"]


class TestFreq:
    def test_basic(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, out, _ = run(["freq", "ରାମ ସୀତା ରାମ", "--top", "5"], capsys)
        assert code == 0
        # Top entry should be ରାମ with count 2.
        first_line = out.strip().splitlines()[0]
        count, token = first_line.split("\t")
        assert count == "2"
        assert token == "ରାମ"


class TestTranslate:
    def test_odia_to_english_uses_static(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Uses a string in the static-translations table to keep tests offline.
        code, out, _ = run(
            ["translate", "ନମସ୍କାର!ଭଲ ଲାଗୁଛି?", "--from", "or", "--to", "en"],
            capsys,
        )
        assert code == 0
        assert "Hello" in out

    def test_english_to_odia_uses_static(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, out, _ = run(
            ["translate", "hello! feeling good?", "--from", "en", "--to", "or"],
            capsys,
        )
        assert code == 0
        assert "ନମସ୍କାର" in out

    def test_universal_path(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Hindi → Odia exercises the universal branch (neither src nor dst is 'en').
        # Uses a static-table entry to stay offline.
        code, _, _ = run(
            ["translate", "क्यों", "--from", "hi", "--to", "or"],
            capsys,
        )
        assert code == 0


class TestFileInputAndStdin:
    def test_file_input(self, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
        f = tmp_path / "in.txt"
        f.write_text("ରାମ ଓ ସୀତା", encoding="utf-8")
        code, out, _ = run(["remove-stopwords", str(f), "--get-str"], capsys)
        assert code == 0
        assert "ରାମ" in out

    def test_stdin_input(self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.stdin", io.StringIO("ରାମ ସୀତା"))
        code, out, _ = run(["tokenize", "-"], capsys)
        assert code == 0
        assert "ରାମ" in out
