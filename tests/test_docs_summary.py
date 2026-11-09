import ast
import re
from pathlib import Path

from openodia import WordFrequency

INDEX = (Path(__file__).resolve().parent.parent / "docs" / "index.md").read_text(encoding="utf-8")
SECTION = INDEX.split("### :material-shovel: Automatic extractive text summarization")[1].split("\n### ")[0]
CODE = re.search(r"```python\n(.*?)```", SECTION, re.DOTALL).group(1)
TEXT = next(
    ast.literal_eval(keyword.value)
    for node in ast.walk(ast.parse(CODE[: CODE.index("wf.get_summary()")]))
    if isinstance(node, ast.Call)
    for keyword in node.keywords
    if keyword.arg == "text"
)
OUTPUTS = re.findall(r"^'''\n'(.*?)'\n'''", CODE, re.DOTALL | re.MULTILINE)


def squash(text: str) -> str:
    return " ".join(text.split())


def test_documented_summaries_are_what_the_code_returns() -> None:
    wf = WordFrequency(text=TEXT)
    assert len(OUTPUTS) == 2
    assert squash(wf.get_summary()) == squash(OUTPUTS[0])
    assert squash(wf.get_summary(threshold=3.0)) == squash(OUTPUTS[1])
