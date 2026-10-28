import doctest
import re
from pathlib import Path

import pytest

import openodia.cache._cache as cache_module

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
FENCE = re.compile(r"^```pycon\n(.*?)^```", re.DOTALL | re.MULTILINE)
GUIDES = sorted((DOCS / "guides").glob("*.md"))
PYCON_GUIDES = [guide for guide in GUIDES if FENCE.search(guide.read_text(encoding="utf-8"))]
PAGES = sorted(path for path in DOCS.rglob("*.md"))
MD_REFERENCE = re.compile(r"[\w/.-]+\.md")


def nav_pages() -> set[str]:
    nav = (ROOT / "mkdocs.yml").read_text(encoding="utf-8").split("\nnav:\n", 1)[1]
    return set(MD_REFERENCE.findall(nav))


def test_guides_exist() -> None:
    assert len(PYCON_GUIDES) >= 5


@pytest.mark.parametrize("guide", PYCON_GUIDES, ids=lambda path: path.name)
def test_guide_examples_print_what_the_page_shows(guide: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cache_module, "_cache", None)
    source = "\n".join(FENCE.findall(guide.read_text(encoding="utf-8")))
    test = doctest.DocTestParser().get_doctest(source, {}, guide.name, str(guide), 0)
    runner = doctest.DocTestRunner(verbose=False)
    runner.run(test, clear_globs=True)
    assert runner.failures == 0, f"{guide.name}: {runner.failures} of {runner.tries} examples differ from the page"
    assert runner.tries > 0


@pytest.mark.parametrize("page", PAGES, ids=lambda path: path.relative_to(DOCS).as_posix())
def test_every_docs_page_is_in_the_nav(page: Path) -> None:
    relative = page.relative_to(DOCS).as_posix()
    assert relative in nav_pages()


@pytest.mark.parametrize("guide", GUIDES, ids=lambda path: path.name)
def test_llms_txt_links_every_guide(guide: Path) -> None:
    llms = (DOCS / "llms.txt").read_text(encoding="utf-8")
    assert f"/guides/{guide.stem}/" in llms
