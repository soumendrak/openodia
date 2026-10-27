import errno
import io
import os
import json
import subprocess
import sys
from pathlib import Path

import pytest

from deep_translator import GoogleTranslator
from deep_translator.exceptions import RequestError, TooManyRequests

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
        assert cli._read_input(str(f), file=True) == "from file"

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
        assert out == "ରାମ ଗଲା\n ସୀତା ଆସିଲା\n\n"


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


_FAKE_TRANSLATIONS = {
    ("or", "en"): {"ନମସ୍କାର!ଭଲ ଲାଗୁଛି?": "Hello! Feeling good?"},
    ("en", "or"): {"hello! feeling good?": "ନମସ୍କାର! ଭଲ ଲାଗୁଛି?"},
    ("hi", "en"): {"क्यों": "why"},
}


class _FakeGoogleTranslator:
    """Offline stand-in for deep_translator.GoogleTranslator."""

    def __init__(self, source: str, target: str) -> None:
        self._pair = (source, target)

    def translate(self, text: str) -> str:
        return _FAKE_TRANSLATIONS.get(self._pair, {}).get(text, text)


@pytest.fixture(autouse=True)
def _offline_translator(monkeypatch: pytest.MonkeyPatch):
    """Keep CLI translation tests off the network and start with an empty cache."""
    import deep_translator
    from openodia.cache import _cache as cache_module

    # A fresh in-memory cache: never touch a configured OPENODIA_CACHE_DISK.
    monkeypatch.setattr(cache_module, "_cache", cache_module.TranslationCache())
    monkeypatch.setattr(deep_translator, "GoogleTranslator", _FakeGoogleTranslator)
    yield


class TestTranslate:
    def test_odia_to_english_uses_static(self, capsys: pytest.CaptureFixture[str]) -> None:
        # The translator is faked by ``_offline_translator`` to keep tests offline.
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
        # Hindi → English exercises the universal branch (neither side is 'or').
        code, out, _ = run(
            ["translate", "क्यों", "--from", "hi", "--to", "en"],
            capsys,
        )
        assert code == 0
        assert "why" in out


class TestFileInputAndStdin:
    def test_file_input(self, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
        f = tmp_path / "in.txt"
        f.write_text("ରାମ ଓ ସୀତା", encoding="utf-8")
        code, out, _ = run(["remove-stopwords", str(f), "--file", "--get-str"], capsys)
        assert code == 0
        assert "ରାମ" in out

    def test_stdin_input(self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.stdin", io.StringIO("ରାମ ସୀତା"))
        code, out, _ = run(["tokenize", "-"], capsys)
        assert code == 0
        assert "ରାମ" in out


class TestReviewEdgeCases:
    def test_detect_language_whitespace_only(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, out, _ = run(["detect-language", "   "], capsys)
        assert code == 0
        assert "(empty input)" in out

    def test_prefix_count_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, out, _ = run(["name", "--kind", "prefix", "--count", "0"], capsys)
        assert code == 0
        assert out == ""

    def test_summarize_rejects_zero_threshold(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, _, err = run(["summarize", "ରାମ ଆସିଲେ।", "--threshold", "0"], capsys)
        assert code == 2
        assert "--threshold must be a positive number" in err

    def test_python_dash_m_runs_cli(self) -> None:
        import subprocess
        import sys

        r = subprocess.run(
            [sys.executable, "-m", "openodia", "tokenize", "ରାମ ସୀତା"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            # No PYTHONIOENCODING: the CLI must emit UTF-8 on its own, even
            # where a redirected stream defaults to cp1252 (Windows).
            env={k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"},
        )
        assert r.returncode == 0, r.stderr
        assert "ରାମ" in r.stdout


class TestArgumentValidation:
    def test_long_inline_text_is_not_statted_as_path(self, capsys: pytest.CaptureFixture[str]) -> None:
        text = "ରାମ " * 100  # > 255 bytes in one "path component"
        code, out, _ = run(["tokenize", text], capsys)
        assert code == 0
        assert "ରାମ" in out

    def test_digit_flags_are_mutually_exclusive(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc:
            cli.main(["clean", "x", "--latin-to-odia", "--odia-to-latin"])
        assert exc.value.code == 2
        assert "not allowed with argument" in capsys.readouterr().err

    def test_negative_count_rejected(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc:
            cli.main(["name", "--kind", "first", "--count", "-1"])
        assert exc.value.code == 2
        assert "must be >= 0" in capsys.readouterr().err

    def test_ngram_size_must_be_positive(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc:
            cli.main(["ngrams", "ରାମ ସୀତା", "-n", "0"])
        assert exc.value.code == 2
        assert "must be >= 1" in capsys.readouterr().err


class TestCodexValidationRound:
    @pytest.mark.parametrize("value", ["-1", "2", "nan"])
    def test_detect_threshold_bounds(self, value: str, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc:
            cli.main(["detect-language", "hello", "--threshold", value])
        assert exc.value.code == 2

    def test_freq_rejects_negative_top(self) -> None:
        with pytest.raises(SystemExit) as exc:
            cli.main(["freq", "ରାମ ସୀତା", "--top", "-1"])
        assert exc.value.code == 2

    def test_summarize_rejects_nan_threshold(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, _, err = run(["summarize", "ରାମ ଆସିଲେ।", "--threshold", "nan"], capsys)
        assert code == 2
        assert "--threshold must be a positive number" in err

    def test_utf8_stdio_reconfigures_legacy_stream(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import io
        import sys

        raw = io.BytesIO()
        legacy = io.TextIOWrapper(raw, encoding="cp1252")
        monkeypatch.setattr(sys, "stdout", legacy)
        cli._utf8_stdio()
        print("ରାମ", file=legacy)
        legacy.flush()
        assert raw.getvalue().decode("utf-8").strip() == "ରାମ"

    def test_detect_threshold_in_range_accepted(self, capsys: pytest.CaptureFixture[str]) -> None:
        code, _, _ = run(["detect-language", "ରାମ", "--threshold", "0.3"], capsys)
        assert code == 0


class TestRequestedReviewCoverage:
    def test_version(self, capsys):
        from openodia import __version__

        with pytest.raises(SystemExit) as exc:
            cli.main(["--version"])
        assert exc.value.code == 0
        assert capsys.readouterr().out == f"openodia {__version__}\n"

    def test_stdin_utf8_in_c_locale(self):
        import subprocess
        import sys

        env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
        env.update(LC_ALL="C", PYTHONCOERCECLOCALE="0", PYTHONUTF8="0")
        result = subprocess.run(
            [sys.executable, "-m", "openodia", "tokenize", "-"],
            input="ରାମ ସୀତା".encode(),
            capture_output=True,
            env=env,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.decode("utf-8").replace("\r\n", "\n") == "ରାମ\nସୀତା\n"

    def test_invalid_utf8_file(self, tmp_path, capsys):
        path = tmp_path / "invalid.txt"
        path.write_bytes(b"\xff")
        code, out, err = run(["normalize", "--file", str(path)], capsys)
        assert code != 0
        assert out == ""
        assert err.startswith("openodia: error: ")
        assert "decode" in err
        assert "Traceback" not in err

    def test_missing_file(self, tmp_path, capsys):
        code, out, err = run(["normalize", "--file", str(tmp_path / "missing")], capsys)
        assert code != 0
        assert out == ""
        assert err.startswith("openodia: error: ")
        assert "Traceback" not in err

    def test_file_flag_and_literal_existing_path(self, tmp_path, capsys):
        path = tmp_path / "input.txt"
        path.write_text("ରାମ", encoding="utf-8")
        assert run(["normalize", str(path)], capsys) == (0, f"{path}\n", "")
        assert run(["normalize", "--file", str(path)], capsys) == (0, "ରାମ\n", "")

    @pytest.mark.parametrize(
        ("flag", "text", "default", "kept"),
        [
            ("--keep-zwj", "ରା\u200dମ", "ରାମ", "ରା\u200dମ"),
            ("--keep-zwnj", "ରା\u200cମ", "ରାମ", "ରା\u200cମ"),
            ("--keep-whitespace", "ରାମ   ସୀତା", "ରାମ ସୀତା", "ରାମ   ସୀତା"),
        ],
    )
    def test_clean_keep_flags(self, flag, text, default, kept, capsys):
        assert run(["clean", text], capsys) == (0, default + "\n", "")
        assert run(["clean", text, flag], capsys) == (0, kept + "\n", "")

    @pytest.mark.parametrize(
        ("source", "target", "expected"),
        [("or", "en", "from Odia"), ("en", "or", "to Odia"), ("hi", "en", "universal")],
    )
    def test_translate_routing(self, source, target, expected, monkeypatch, capsys):
        def from_odia(text, *, dest_language_code):
            assert (text, dest_language_code) == ("input", target)
            return "from Odia"

        def to_odia(text, *, source_language_code):
            assert (text, source_language_code) == ("input", source)
            return "to Odia"

        def universal(text, *, source_language_code, dest_language_code):
            assert (text, source_language_code, dest_language_code) == ("input", source, target)
            return "universal"

        monkeypatch.setattr("openodia.odia_to_other_lang", from_odia)
        monkeypatch.setattr("openodia.other_lang_to_odia", to_odia)
        monkeypatch.setattr("openodia.universal_translation", universal)
        assert run(["translate", "input", "--from", source, "--to", target], capsys) == (0, expected + "\n", "")

    def test_json_preserves_odia(self, monkeypatch, capsys):
        monkeypatch.setattr("openodia.ud.detect_language", lambda text, threshold: {"language": "ଓଡ଼ିଆ"})
        assert run(["detect-language", "ରାମ", "--json"], capsys) == (0, '{"language": "ଓଡ଼ିଆ"}\n', "")

    @pytest.mark.parametrize("kind", ["prefix", "middle"])
    def test_name_kind_content(self, kind, monkeypatch, capsys):
        def generate(count):
            assert count == 2
            return ["ଶ୍ରୀ", "କୁମାର"]

        method = "generate_prefixes" if kind == "prefix" else "generate_middlenames"
        monkeypatch.setattr(f"openodia.name.{method}", generate)
        assert run(["name", "--kind", kind, "--count", "2"], capsys) == (0, "ଶ୍ରୀ\nକୁମାର\n", "")

    @pytest.mark.parametrize(("top", "expected"), [("0", ""), ("1", "3\tରାମ\n"), ("2", "3\tରାମ\n2\tସୀତା\n")])
    def test_top_limits_output(self, top, expected, capsys):
        assert run(["freq", "ରାମ ସୀତା ରାମ ଲକ୍ଷ୍ମଣ ସୀତା ରାମ", "--top", top], capsys) == (0, expected, "")


class _RaisingTranslator:
    def __init__(self, source: str, target: str) -> None:
        pass

    def translate(self, text: str) -> str:
        raise TooManyRequests()


class TestTranslateErrors:
    @staticmethod
    def assert_clean_failure(code, out, err, expected):
        assert (code, out) == (1, "")
        assert err == f"openodia: error: {expected}\n"

    def test_unsupported_language_code(self, monkeypatch, capsys):
        monkeypatch.setattr("deep_translator.GoogleTranslator", GoogleTranslator)
        self.assert_clean_failure(*run(["translate", "hello", "--to", "zz"], capsys), "unsupported language code 'zz'")

    def test_text_over_google_limit(self, monkeypatch, capsys, tmp_path):
        monkeypatch.setattr("deep_translator.GoogleTranslator", GoogleTranslator)
        long_text = tmp_path / "long.txt"
        long_text.write_text("ab " * 2000, encoding="utf-8")
        code, out, err = run(["translate", str(long_text), "--file"], capsys)
        self.assert_clean_failure(code, out, err, "Text length need to be between 0 and 5000 characters")
        assert "ab ab" not in err

    def test_rate_limit(self, monkeypatch, capsys):
        monkeypatch.setattr("deep_translator.GoogleTranslator", _RaisingTranslator)
        self.assert_clean_failure(
            *run(["translate", "ନମସ୍କାର", "--from", "or", "--to", "en"], capsys),
            "Google Translate refused the request (rate limit or captcha); try again later",
        )

    def test_request_error(self, monkeypatch, capsys):
        class Failing(_RaisingTranslator):
            def translate(self, text):
                raise RequestError()

        monkeypatch.setattr("deep_translator.GoogleTranslator", Failing)
        code, out, err = run(["translate", "ନମସ୍କାର", "--from", "or", "--to", "en"], capsys)
        self.assert_clean_failure(code, out, err, RequestError().message)

    def test_unexpected_error_still_propagates(self, monkeypatch, capsys):
        class Crashing(_RaisingTranslator):
            def translate(self, text):
                raise RuntimeError("boom")

        monkeypatch.setattr("deep_translator.GoogleTranslator", Crashing)
        with pytest.raises(RuntimeError, match="boom"):
            run(["translate", "ନମସ୍କାର", "--from", "or", "--to", "en"], capsys)

    @pytest.mark.parametrize(
        ("value", "message"),
        [
            ("abc", "OPENODIA_CACHE_MAX_SIZE must be an integer >= 1, got 'abc'"),
            ("0", "OPENODIA_CACHE_MAX_SIZE must be an integer >= 1, got '0'"),
            ("-3", "OPENODIA_CACHE_MAX_SIZE must be an integer >= 1, got '-3'"),
        ],
    )
    def test_bad_cache_size_env(self, value, message, monkeypatch, capsys):
        from openodia.cache import _cache as cache_module

        monkeypatch.setattr(cache_module, "_cache", None)
        monkeypatch.setenv("OPENODIA_CACHE_MAX_SIZE", value)
        self.assert_clean_failure(*run(["translate", "ନମସ୍କାର", "--from", "or", "--to", "en"], capsys), message)

    @pytest.mark.parametrize(("value", "size"), [(" 5 ", 5), ("1_000", 1000), ("+7", 7)])
    def test_cache_size_env_accepts_what_int_accepts(self, value, size, monkeypatch):
        from openodia.cache import _cache as cache_module

        monkeypatch.setenv("OPENODIA_CACHE_MAX_SIZE", value)
        assert cache_module._build_from_env().max_size == size

    def test_disk_cache_without_diskcache(self, monkeypatch, capsys):
        from openodia.cache import _cache as cache_module

        monkeypatch.setattr(cache_module, "_cache", None)
        monkeypatch.setenv("OPENODIA_CACHE_DISK", "/nonexistent")
        monkeypatch.setitem(sys.modules, "diskcache", None)
        code, out, err = run(["translate", "ନମସ୍କାର", "--from", "or", "--to", "en"], capsys)
        assert (code, out) == (1, "")
        assert (
            err
            == "openodia: error: Disk caching requires the 'diskcache' package. Install with: pip install openodia[cache]\n"
        )


BOM = "\ufeff"


class TestBom:
    @pytest.mark.parametrize("command", ["tokenize", "freq", "normalize", "clean"])
    def test_file_bom_is_stripped(self, command, capsys, tmp_path):
        f = tmp_path / "bom.txt"
        f.write_bytes(BOM.encode("utf-8") + "ରାମ ସୀତା\n".encode())
        code, out, _ = run([command, str(f), "--file"], capsys)
        assert code == 0
        assert BOM not in out
        assert "ରାମ" in out

    def test_stdin_bom_is_stripped(self, monkeypatch, capsys):
        stdin = io.TextIOWrapper(io.BytesIO(BOM.encode("utf-8") + "ରାମ ସୀତା\n".encode()), encoding="utf-8")
        monkeypatch.setattr("sys.stdin", stdin)
        assert run(["tokenize", "-"], capsys) == (0, "ରାମ\nସୀତା\n", "")

    def test_bom_does_not_change_detect_language(self, capsys, tmp_path):
        plain, marked = tmp_path / "plain.txt", tmp_path / "bom.txt"
        plain.write_text("ରାମ ସୀତା", encoding="utf-8")
        marked.write_bytes(BOM.encode("utf-8") + "ରାମ ସୀତା".encode())
        assert run(["detect-language", str(marked), "--file"], capsys) == run(
            ["detect-language", str(plain), "--file"], capsys
        )


class TestRobustness:
    def test_closed_stdin(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", None)
        assert run(["tokenize", "-"], capsys) == (1, "", "openodia: error: standard input is closed\n")

    def test_broken_pipe_exits_quietly(self, monkeypatch, capsys):
        class Stdout:
            def fileno(self):
                return 1

        redirected = []
        monkeypatch.setattr("sys.stdout", Stdout())
        monkeypatch.setattr(os, "dup2", lambda source, target: redirected.append(target))
        monkeypatch.setattr("openodia.name.generate_names", lambda count: (_ for _ in ()).throw(BrokenPipeError()))
        assert cli.main(["name"]) == 141
        assert redirected == [1]
        assert capsys.readouterr().err == ""

    @pytest.mark.parametrize(
        ("platform", "filename", "exit_code"),
        [("win32", None, 141), ("win32", "a|b.txt", 1), ("linux", None, 1)],
    )
    def test_einval_is_a_closed_pipe_only_on_windows_writes(self, platform, filename, exit_code, monkeypatch, capsys):
        class Stdout:
            def fileno(self):
                return 1

        monkeypatch.setattr("sys.stdout", Stdout())
        monkeypatch.setattr("sys.platform", platform)
        monkeypatch.setattr(os, "dup2", lambda source, target: None)
        error = OSError(errno.EINVAL, "Invalid argument", filename)
        monkeypatch.setattr("openodia.name.generate_names", lambda count: (_ for _ in ()).throw(error))
        assert cli.main(["name"]) == exit_code

    @pytest.mark.skipif(sys.platform == "win32", reason="needs POSIX fork to close a descriptor")
    @pytest.mark.parametrize("closed", [(1,), (2,), (1, 2)])
    @pytest.mark.parametrize("argv", [["tokenize", "ରାମ"], ["name", "--count", "3"]])
    def test_closed_standard_streams_exit_quietly(self, argv, closed):
        def close_streams():
            for fd in closed:
                os.close(fd)

        proc = subprocess.run(
            [sys.executable, "-m", "openodia", *argv],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            preexec_fn=close_streams,
            timeout=60,
        )
        assert (proc.returncode, proc.stderr) == (0, b"")

    def test_long_error_is_truncated(self, capsys):
        assert cli._fail("x" * 500) == 1
        assert capsys.readouterr().err == "openodia: error: " + "x" * 197 + "...\n"

    def test_name_piped_into_closed_reader(self):
        cmd = [sys.executable, "-m", "openodia", "name", "--count", "100000"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert proc.stdout.readline()
        proc.stdout.close()
        assert proc.stderr.read() == b""
        assert proc.wait(timeout=60) == 141

    def test_small_output_into_closed_reader(self):
        proc = subprocess.Popen(
            [sys.executable, "-m", "openodia", "name", "--count", "3"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        proc.stdout.close()
        assert proc.stderr.read() == b""
        assert proc.wait(timeout=60) == 141

    @pytest.mark.parametrize(
        ("argv", "message"),
        [
            (
                ["detect-language", "x", "--threshold", "abc"],
                "argument --threshold: must be a number between 0 and 1, got 'abc'",
            ),
            (["name", "--count", "abc"], "argument --count: must be an integer, got 'abc'"),
            (["ngrams", "x", "-n", "abc"], "argument -n: must be an integer, got 'abc'"),
            (["freq", "x", "--top", "1.5"], "argument --top: must be an integer, got '1.5'"),
        ],
    )
    def test_argparse_messages_name_no_internals(self, argv, message, capsys):
        with pytest.raises(SystemExit) as exc:
            cli.main(argv)
        assert exc.value.code == 2
        assert capsys.readouterr().err.splitlines()[-1] == f"openodia {argv[0]}: error: {message}"
