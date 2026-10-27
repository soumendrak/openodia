import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from deep_translator.exceptions import LanguageNotSupportedException

from openodia import cli

ODIA = "ରାମ ସୀତା ଘରକୁ ଯାଏ । ସେ ଭଲ ଲୋକ ।"
ENGLISH = "Hello world. Bye now."
LONG_ODIA = "ରାମ ସୀତା ଘରକୁ ଯାଏ । ସେ ଭଲ ଲୋକ । ରାମ ଭଲ ପିଲା । ଓଡ଼ିଶା ଏକ ସୁନ୍ଦର ରାଜ୍ୟ । ପୁରୀରେ ଜଗନ୍ନାଥ ମନ୍ଦିର ଅଛି । ରାମ ପୁରୀକୁ ଯାଏ ।"
LONG_SUMMARY = "ରାମ ସୀତା ଘରକୁ ଯାଏ  ସେ ଭଲ ଲୋକ  ରାମ ଭଲ ପିଲା  ରାମ ପୁରୀକୁ ଯାଏ"
ODIA_TOKENS = ["ରାମ", "ସୀତା", "ଘରକୁ", "ଯାଏ", "।", "ସେ", "ଭଲ", "ଲୋକ", "।"]
ENGLISH_TOKENS = ["Hello", "world", "Bye", "now"]
ODIA_SENTENCES = ["ରାମ ସୀତା ଘରକୁ ଯାଏ", " ସେ ଭଲ ଲୋକ", ""]

CASES = {
    "tokenize-odia": (["tokenize"], ODIA, "\n".join(ODIA_TOKENS) + "\n", {"tokens": ODIA_TOKENS}),
    "tokenize-english": (["tokenize"], ENGLISH, "\n".join(ENGLISH_TOKENS) + "\n", {"tokens": ENGLISH_TOKENS}),
    "tokenize-empty": (["tokenize"], "", "", {"tokens": []}),
    "sentences-odia": (
        ["tokenize", "--sentences"],
        ODIA,
        "ରାମ ସୀତା ଘରକୁ ଯାଏ\n ସେ ଭଲ ଲୋକ\n\n",
        {"tokens": ODIA_SENTENCES},
    ),
    "sentences-english": (["tokenize", "--sentences"], ENGLISH, ENGLISH + "\n", {"tokens": [ENGLISH]}),
    "sentences-empty": (["tokenize", "--sentences"], "", "\n", {"tokens": [""]}),
    "normalize-odia": (["normalize"], ODIA, ODIA + "\n", {"text": ODIA}),
    "normalize-english": (["normalize"], ENGLISH, ENGLISH + "\n", {"text": ENGLISH}),
    "normalize-empty": (["normalize"], "", "\n", {"text": ""}),
    "clean-odia": (["clean"], "ନମ‌ସ୍କାର  ୧୨୩", "ନମସ୍କାର ୧୨୩\n", {"text": "ନମସ୍କାର ୧୨୩"}),
    "clean-digits": (["clean", "--odia-to-latin"], "୧୨୩", "123\n", {"text": "123"}),
    "clean-english": (["clean"], "a   b", "a b\n", {"text": "a b"}),
    "clean-empty": (["clean"], "", "\n", {"text": ""}),
    "detect-odia": (
        ["detect-language"],
        ODIA,
        "odia (confidence: 0.91)\n",
        {"language": "odia", "confidence_score": 0.91},
    ),
    "detect-english": (
        ["detect-language"],
        ENGLISH,
        "non-odia (confidence: 1.0)\n",
        {"language": "non-odia", "confidence_score": 1.0},
    ),
    "detect-empty": (["detect-language"], "", "(empty input)\n", {}),
    "summarize-odia": (["summarize"], LONG_ODIA, LONG_SUMMARY + "\n", {"summary": LONG_SUMMARY}),
    "summarize-english": (["summarize"], ENGLISH, "\n", {"summary": ""}),
    "summarize-empty": (["summarize"], "", "\n", {"summary": ""}),
    "stopwords-odia": (
        ["remove-stopwords"],
        ODIA,
        "\n".join(ODIA_TOKENS[:4] + ODIA_TOKENS[5:8]) + "\n",
        {"tokens": ODIA_TOKENS[:4] + ODIA_TOKENS[5:8]},
    ),
    "stopwords-english": (["remove-stopwords"], ENGLISH, "\n".join(ENGLISH_TOKENS) + "\n", {"tokens": ENGLISH_TOKENS}),
    "stopwords-empty": (["remove-stopwords"], "", "", {"tokens": []}),
    "stopwords-str-odia": (
        ["remove-stopwords", "--get-str"],
        ODIA,
        "ରାମ ସୀତା ଘରକୁ ଯାଏ ସେ ଭଲ ଲୋକ\n",
        {"text": "ରାମ ସୀତା ଘରକୁ ଯାଏ ସେ ଭଲ ଲୋକ"},
    ),
    "stopwords-str-english": (
        ["remove-stopwords", "--get-str"],
        ENGLISH,
        "Hello world Bye now\n",
        {"text": "Hello world Bye now"},
    ),
    "stopwords-str-empty": (["remove-stopwords", "--get-str"], "", "\n", {"text": ""}),
    "ngrams-odia": (
        ["ngrams"],
        ODIA,
        "ରାମ ସୀତା\nସୀତା ଘରକୁ\nଘରକୁ ଯାଏ\nଯାଏ ।\n। ସେ\nସେ ଭଲ\nଭଲ ଲୋକ\nଲୋକ ।\n",
        {"ngrams": [list(pair) for pair in zip(ODIA_TOKENS, ODIA_TOKENS[1:])]},
    ),
    "ngrams-english": (
        ["ngrams", "-n", "3"],
        ENGLISH,
        "Hello world Bye\nworld Bye now\n",
        {"ngrams": [["Hello", "world", "Bye"], ["world", "Bye", "now"]]},
    ),
    "ngrams-empty": (["ngrams"], "", "", {"ngrams": []}),
    "freq-odia": (
        ["freq", "--top", "2"],
        ODIA,
        "2\t।\n1\tରାମ\n",
        {"counts": [{"token": "।", "count": 2}, {"token": "ରାମ", "count": 1}]},
    ),
    "freq-english": (
        ["freq"],
        ENGLISH,
        "1\tHello\n1\tworld\n1\tBye\n1\tnow\n",
        {"counts": [{"token": token, "count": 1} for token in ENGLISH_TOKENS]},
    ),
    "freq-empty": (["freq"], "", "", {"counts": []}),
    "translate-odia": (["translate", "--from", "or", "--to", "en"], "ନମସ୍କାର", "Hello\n", {"text": "Hello"}),
    "translate-english": (["translate"], "good morning", "ଶୁଭ ସକାଳ\n", {"text": "ଶୁଭ ସକାଳ"}),
    "translate-empty": (["translate"], "", "\n", {"text": ""}),
}

MODES = ["inline", "stdin", "file"]


class _FakeGoogleTranslator:
    def __init__(self, source: str, target: str) -> None:
        self._pair = (source, target)

    def translate(self, text: str) -> str:
        return {("or", "en"): {"ନମସ୍କାର": "Hello"}}.get(self._pair, {}).get(text, text)


@pytest.fixture(autouse=True)
def _offline_translator(monkeypatch: pytest.MonkeyPatch):
    import deep_translator
    from openodia.cache import _cache as cache_module

    monkeypatch.setattr(cache_module, "_cache", cache_module.TranslationCache())
    monkeypatch.setattr(deep_translator, "GoogleTranslator", _FakeGoogleTranslator)


def invoke(
    argv: list[str],
    text: str,
    mode: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, str, str]:
    if mode == "inline":
        full = [*argv, text]
    elif mode == "stdin":
        monkeypatch.setattr("sys.stdin", io.StringIO(text))
        full = [*argv, "-"]
    else:
        path = tmp_path / "input.txt"
        path.write_text(text, encoding="utf-8")
        full = [*argv, "--file", str(path)]
    capsys.readouterr()
    code = cli.main(full)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("case", CASES)
def test_default_output_is_unchanged(case, mode, tmp_path, monkeypatch, capsys) -> None:
    argv, text, expected, _ = CASES[case]
    assert invoke(argv, text, mode, tmp_path, monkeypatch, capsys) == (0, expected, "")


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("case", CASES)
def test_json_output_is_one_utf8_document(case, mode, tmp_path, monkeypatch, capsys) -> None:
    argv, text, _, payload = CASES[case]
    code, out, err = invoke([*argv, "--json"], text, mode, tmp_path, monkeypatch, capsys)
    assert (code, err) == (0, "")
    assert out == json.dumps(payload, ensure_ascii=False) + "\n"
    assert json.loads(out) == payload


def test_json_keeps_odia_unescaped(capsys) -> None:
    assert cli.main(["tokenize", "ରାମ", "--json"]) == 0
    assert capsys.readouterr().out == '{"tokens": ["ରାମ"]}\n'


@pytest.mark.parametrize("count", [0, 3])
def test_name_json(count, monkeypatch, capsys) -> None:
    names = ["ରାମ ଦାସ", "ସୀତା ଦେବୀ", "ଲକ୍ଷ୍ମଣ ସାହୁ"][:count]
    monkeypatch.setattr("openodia.name.generate_names", lambda n: names)
    assert cli.main(["name", "--count", str(count)]) == 0
    assert capsys.readouterr().out == "".join(f"{n}\n" for n in names)
    assert cli.main(["name", "--count", str(count), "--json"]) == 0
    assert capsys.readouterr().out == json.dumps({"names": names}, ensure_ascii=False) + "\n"


@pytest.mark.parametrize("kind", ["first", "middle", "surname", "prefix"])
def test_name_json_for_every_kind(kind, capsys) -> None:
    assert cli.main(["name", "--kind", kind, "--count", "2", "--json"]) == 0
    names = json.loads(capsys.readouterr().out)["names"]
    assert len(names) == 2
    assert all(isinstance(n, str) and n for n in names)


def test_summarize_json_with_threshold(capsys) -> None:
    assert cli.main(["summarize", LONG_ODIA, "--threshold", "1", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"summary": LONG_SUMMARY}


class _UnsupportedTranslator:
    def __init__(self, source: str, target: str) -> None:
        raise LanguageNotSupportedException("zz")


@pytest.mark.parametrize(
    ("argv", "code", "message"),
    [
        (["translate", "x", "--from", "zz", "--json"], 1, "openodia: error: unsupported language code 'zz'\n"),
        (["tokenize", "--file", "missing-file.txt", "--json"], 1, "openodia: error: [Errno 2]"),
        (["summarize", "x", "--threshold", "0", "--json"], 2, "error: --threshold must be a positive number\n"),
    ],
)
def test_json_errors_stay_on_stderr(argv, code, message, monkeypatch, capsys) -> None:
    monkeypatch.setattr("deep_translator.GoogleTranslator", _UnsupportedTranslator)
    assert cli.main(argv) == code
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith(message)


def test_json_usage_error_exits_2_with_empty_stdout(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["freq", "x", "--top", "-1", "--json"])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "openodia freq: error: argument --top" in captured.err


@pytest.mark.parametrize(
    "command", ["tokenize", "normalize", "clean", "translate", "name", "summarize", "remove-stopwords", "ngrams", "freq"]
)
def test_every_subcommand_accepts_json(command, capsys) -> None:
    argv = [command] if command == "name" else [command, ""]
    assert cli.main([*argv, "--json"]) == 0
    json.loads(capsys.readouterr().out)


def _run_cli(*argv: str, stdin: bytes) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run([sys.executable, "-m", "openodia", *argv], input=stdin, capture_output=True, timeout=60)


def test_json_rejects_invalid_utf8_stdin() -> None:
    done = _run_cli("tokenize", "-", "--json", stdin=b"\xff")
    assert done.returncode == 1
    assert done.stdout == b""
    assert done.stderr.decode("utf-8").startswith("openodia: error: 'utf-8' codec can't decode byte 0xff")


def test_json_stdin_stays_valid_utf8_for_valid_input() -> None:
    done = _run_cli("tokenize", "-", "--json", stdin="ରାମ ସୀତା".encode())
    assert done.returncode == 0
    assert json.loads(done.stdout.decode("utf-8")) == {"tokens": ["ରାମ", "ସୀତା"]}


def test_json_strict_stdin_in_process(monkeypatch, capsys) -> None:
    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(b"\xff"), encoding="utf-8", errors="surrogateescape"))
    assert cli.main(["tokenize", "-", "--json"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("openodia: error: 'utf-8' codec can't decode byte 0xff")


def test_json_rejects_non_utf8_text_argument(capsys) -> None:
    assert cli.main(["normalize", "\udcff", "--json"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "openodia: error: text argument is not valid UTF-8\n"


def test_json_accepts_any_file_path_argument(tmp_path, capsys) -> None:
    path = tmp_path / "input.txt"
    path.write_text("ରାମ", encoding="utf-8")
    assert cli.main(["tokenize", "--file", str(path), "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"tokens": ["ରାମ"]}


@pytest.mark.skipif(sys.platform == "win32", reason="raw argv bytes need POSIX")
@pytest.mark.parametrize("command", ["normalize", "tokenize"])
def test_json_rejects_invalid_utf8_argv_bytes(command) -> None:
    done = subprocess.run(
        [sys.executable.encode(), b"-m", b"openodia", command.encode(), b"\xff", b"--json"], capture_output=True, timeout=60
    )
    assert (done.returncode, done.stdout) == (1, b"")
    assert done.stderr == b"openodia: error: text argument is not valid UTF-8\n"


def test_json_closed_stdin_is_a_clean_error(monkeypatch, capsys) -> None:
    stdin = io.TextIOWrapper(io.BytesIO(b""), encoding="utf-8")
    stdin.close()
    monkeypatch.setattr("sys.stdin", stdin)
    assert cli.main(["normalize", "hello", "--json"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("openodia: error: ")


@pytest.mark.skipif(sys.platform == "win32", reason="closed-pipe status is 141 on POSIX")
def test_json_into_closed_reader_exits_141(tmp_path) -> None:
    source = tmp_path / "big.txt"
    source.write_text("ରାମ " * 300_000, encoding="utf-8")
    with source.open("rb") as stdin:
        proc = subprocess.Popen(
            [sys.executable, "-m", "openodia", "tokenize", "-", "--json"],
            stdin=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        proc.stdout.close()
        _, stderr = proc.communicate(timeout=60)
    assert (proc.returncode, stderr) == (141, b"")


ODD_LOCALE = {"LC_ALL": "C", "PYTHONUTF8": "0"}


def _argv_run(*argv: bytes, env: dict[str, str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [os.fsencode(sys.executable), b"-m", b"openodia", *argv],
        env={**os.environ, **env},
        capture_output=True,
        timeout=60,
    )


@pytest.mark.skipif(sys.platform == "win32", reason="raw argv bytes need POSIX")
@pytest.mark.parametrize("env", [{}, ODD_LOCALE], ids=["default", "c-locale"])
def test_json_accepts_valid_utf8_argv_in_any_locale(env) -> None:
    done = _argv_run(b"tokenize", "ରାମ ସୀତା".encode(), b"--json", env=env)
    assert (done.returncode, done.stderr) == (0, b"")
    assert json.loads(done.stdout.decode("utf-8")) == {"tokens": ["ରାମ", "ସୀତା"]}


@pytest.mark.skipif(sys.platform == "win32", reason="raw argv bytes need POSIX")
@pytest.mark.parametrize("env", [{}, ODD_LOCALE], ids=["default", "c-locale"])
def test_json_rejects_invalid_utf8_argv_in_any_locale(env) -> None:
    done = _argv_run(b"tokenize", b"\xff", b"--json", env=env)
    assert (done.returncode, done.stdout) == (1, b"")
    assert done.stderr == b"openodia: error: text argument is not valid UTF-8\n"


def test_json_rejects_unencodable_surrogate_argument(capsys) -> None:
    assert cli.main(["tokenize", "\ud800", "--json"]) == 1
    assert capsys.readouterr().err == "openodia: error: text argument is not valid UTF-8\n"


@pytest.mark.skipif(sys.platform == "win32", reason="raw file names need POSIX")
def test_json_file_path_may_contain_invalid_utf8(tmp_path, capsys) -> None:
    path = Path(os.fsdecode(os.fsencode(tmp_path) + b"/bad\xff.txt"))
    try:
        path.write_text("ରାମ ସୀତା", encoding="utf-8")
    except OSError:
        pytest.skip("filesystem rejects non-UTF-8 file names")
    assert cli.main(["tokenize", "--file", str(path), "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"tokens": ["ରାମ", "ସୀତା"]}
