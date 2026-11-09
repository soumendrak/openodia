import json
import subprocess
import sys

import pytest

HEAVY = ("faker", "deep_translator", "requests", "bs4")


def _loaded_heavy(code: str) -> list[str]:
    script = f"import sys\n{code}\nimport json\nprint(json.dumps(sorted(m for m in {HEAVY!r} if m in sys.modules)))"
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)
    return json.loads(result.stdout.splitlines()[-1])


@pytest.mark.parametrize(
    "code",
    [
        "import openodia",
        "import openodia.text",
        "from openodia.cli import main\ntry:\n    main(['--help'])\nexcept SystemExit:\n    pass",
        "from openodia.cli import main\nmain(['tokenize', 'a b'])",
        "from openodia.cli import main\nmain(['detect-language', 'abc'])",
    ],
    ids=["import", "import-submodule", "cli-help", "cli-tokenize", "cli-detect-language"],
)
def test_heavy_dependencies_stay_unloaded(code: str) -> None:
    assert _loaded_heavy(code) == []


def test_generate_names_loads_faker_on_demand() -> None:
    loaded = _loaded_heavy("import openodia\nopenodia.name.generate_names(1)")
    assert loaded == ["faker"]


def test_cached_translation_does_not_load_deep_translator() -> None:
    code = (
        "import openodia\n"
        "openodia.cache.get_cache().set(('x', 'en', 'fr'), 'cached')\n"
        "assert openodia.universal_translation('x', 'en', 'fr') == 'cached'"
    )
    assert _loaded_heavy(code) == []


def test_cli_reports_translation_errors_after_lazy_import(capsys: pytest.CaptureFixture[str]) -> None:
    from openodia.cli import main

    assert main(["translate", "hello", "--from", "en", "--to", "zz"]) == 1
    assert capsys.readouterr().err == "openodia: error: unsupported language code 'zz'\n"
