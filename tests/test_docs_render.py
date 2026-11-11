import html
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TAGS = re.compile(r"<script.*?</script>|<style.*?</style>|<[^>]+>", re.DOTALL)
RAW_DOCSTRING_MARKUP = re.compile(
    r":(param|type|returns?|rtype|raises?)\b|:(class|func|meth|attr|data|mod|exc|obj|ref):|^\s*(Args|Arguments):|^\s*\.\. \w+::|::\s*$",
    re.MULTILINE,
)


@pytest.fixture(scope="module")
def site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    target = tmp_path_factory.mktemp("site")
    build = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--site-dir", str(target)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, build.stderr
    return target


def rendered_text(page: Path) -> str:
    return html.unescape(TAGS.sub("\n", page.read_text(encoding="utf-8")))


def test_legacy_api_page_lists_the_public_functions(site: Path) -> None:
    page = (site / "api" / "legacy" / "index.html").read_text(encoding="utf-8")
    for name in ("to_unicode", "detect_font", "to_unicode_auto"):
        assert f'id="openodia.legacy.{name}"' in page


def test_api_pages_were_built(site: Path) -> None:
    assert len(list((site / "api").glob("*/index.html"))) >= 10


def test_search_index_covers_the_new_pages(site: Path) -> None:
    payload = json.loads((site / "search" / "search_index.json").read_text(encoding="utf-8"))
    locations = {entry["location"] for entry in payload["docs"]}
    assert {
        "getting-started/",
        "guides/pii/",
        "guides/transliteration/",
        "api/pii/",
        "api/indic/",
        "contributing/",
        "changelog/",
    } <= locations
    page = (site / "getting-started" / "index.html").read_text(encoding="utf-8")
    assert 'id="__search"' in page
    assert "search.suggest" in page
    assert "search.highlight" in page
    assert "assets/javascripts/workers/search." in page
    assert "search/main.js" not in page
    assert not (site / "search.html").exists()


def test_api_pages_show_no_raw_docstring_markup(site: Path) -> None:
    leaks = {
        page.parent.name: match.group(0).strip()
        for page in sorted((site / "api").glob("*/index.html"))
        if (match := RAW_DOCSTRING_MARKUP.search(rendered_text(page)))
    }

    assert leaks == {}
