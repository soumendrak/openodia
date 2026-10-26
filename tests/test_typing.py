import subprocess
import tarfile
import zipfile
from importlib import resources
from pathlib import Path

import pytest
from mypy import api

ROOT = Path(__file__).resolve().parent.parent
CONFIG = str(ROOT / "pyproject.toml")

REVEAL = """
from openodia import ud
reveal_type(ud.remove_stopwords("a b"))
reveal_type(ud.remove_stopwords(["a"], get_str=True))
reveal_type(ud.remove_stopwords("a", get_str=False))
"""

UNANNOTATED = """
def untyped(x):
    return x
"""


def run_mypy(*args: str) -> tuple[str, int]:
    stdout, _, status = api.run(["--config-file", CONFIG, "--no-incremental", *args])
    return stdout, status


def test_package_ships_py_typed_marker():
    assert resources.files("openodia").joinpath("py.typed").is_file()


def test_plain_uv_build_ships_py_typed_in_sdist_and_wheel(tmp_path):
    try:
        built = subprocess.run(["uv", "build", "--out-dir", str(tmp_path)], cwd=ROOT, capture_output=True, text=True)
    except FileNotFoundError:
        pytest.fail("uv is not on PATH; this test runs `uv build` exactly as release.yml and codequality.yml do")
    assert built.returncode == 0, built.stderr

    (wheel,) = tmp_path.glob("openodia-*.whl")
    (sdist,) = tmp_path.glob("openodia-*.tar.gz")
    with zipfile.ZipFile(wheel) as archive:
        assert "openodia/py.typed" in archive.namelist(), built.stderr
    with tarfile.open(sdist) as archive:
        assert f"{sdist.name.removesuffix('.tar.gz')}/openodia/py.typed" in archive.getnames(), built.stderr


def test_project_config_is_strict(tmp_path):
    source = tmp_path / "untyped.py"
    source.write_text(UNANNOTATED, encoding="utf-8")

    stdout, status = run_mypy(str(source))

    assert status == 1
    assert "[no-untyped-def]" in stdout


def test_remove_stopwords_return_type_follows_get_str(tmp_path):
    source = tmp_path / "reveal.py"
    source.write_text(REVEAL, encoding="utf-8")

    stdout, status = run_mypy(str(source))

    assert status == 0
    revealed = [line.split('"')[1].replace("builtins.", "") for line in stdout.splitlines() if "Revealed type" in line]
    assert revealed == ["list[str]", "str", "list[str]"]
