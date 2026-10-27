import logging
import subprocess
import sys

import pytest

from openodia import name
from openodia.common.utility import LOGGER


def _run(code: str) -> str:
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def test_import_leaves_root_logger_untouched() -> None:
    out = _run(
        "import logging\n"
        "root = logging.getLogger()\n"
        "before = (list(root.handlers), root.level)\n"
        "import openodia\n"
        "print(before == (list(root.handlers), root.level) and not root.handlers)\n"
    )
    assert out == "True"


def test_import_does_not_load_rich() -> None:
    out = _run("import sys, openodia\nprint(any(m == 'rich' or m.startswith('rich.') for m in sys.modules))")
    assert out == "False"


def test_package_logger_has_a_null_handler() -> None:
    package_logger = logging.getLogger("openodia")
    assert any(isinstance(h, logging.NullHandler) for h in package_logger.handlers)
    assert LOGGER is package_logger


def test_library_warning_is_silent_without_logging_config() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "from openodia import ud\nud.detect_language('')"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert (result.stdout, result.stderr) == ("", "")


def test_invalid_name_type_logs_an_error_without_a_traceback(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR, logger="openodia"), pytest.raises(ValueError):
        name.generate_firstnames(1, "zzz")
    assert [r.levelno for r in caplog.records] == [logging.ERROR]
    assert caplog.records[0].exc_info is None
