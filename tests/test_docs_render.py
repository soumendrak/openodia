import html
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TAGS = re.compile(r"<script.*?</script>|<style.*?</style>|<[^>]+>", re.DOTALL)
RAW_DOCSTRING_MARKUP = re.compile(
    r":(param|type|returns?|rtype|raises?)\b|^\s*(Args|Arguments):|^\s*\.\. \w+::|::\s*$", re.MULTILINE
)


@pytest.fixture(scope="module")
def site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    target = tmp_path_factory.mktemp("site")
    subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--quiet", "--site-dir", str(target)],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return target


def rendered_text(page: Path) -> str:
    return html.unescape(TAGS.sub("\n", page.read_text(encoding="utf-8")))


def test_api_pages_were_built(site: Path) -> None:
    assert len(list((site / "api").glob("*/index.html"))) >= 10


def test_api_pages_show_no_raw_docstring_markup(site: Path) -> None:
    leaks = {
        page.parent.name: match.group(0).strip()
        for page in sorted((site / "api").glob("*/index.html"))
        if (match := RAW_DOCSTRING_MARKUP.search(rendered_text(page)))
    }

    assert leaks == {}
