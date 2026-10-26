import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RUNNABLE = ["AGENTS.md", "skills/openodia/SKILL.md", "README.md"]
DOCS = [*RUNNABLE, "docs/llms.txt", "docs/index.md"]
FENCE = re.compile(r"^```console\n(.*?)^```", re.DOTALL | re.MULTILINE)

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="documented examples use a POSIX shell")


def console_blocks(doc: str) -> list[str]:
    return FENCE.findall((ROOT / doc).read_text(encoding="utf-8"))


def parse_steps(block: str) -> list[tuple[str, list[str]]]:
    steps: list[tuple[str, list[str]]] = []
    for line in block.splitlines():
        if line.startswith("$ "):
            steps.append((line[2:], []))
        else:
            steps[-1][1].append(line)
    return steps


CASES = [(doc, index) for doc in DOCS for index in range(len(console_blocks(doc)))]


@pytest.mark.parametrize("doc", RUNNABLE)
def test_doc_has_runnable_examples(doc: str) -> None:
    assert console_blocks(doc)


@pytest.mark.parametrize(("doc", "index"), CASES)
def test_documented_example_runs_as_shown(doc: str, index: int, tmp_path: Path) -> None:
    env = {
        **os.environ,
        "PATH": os.pathsep.join([str(Path(sys.executable).parent), os.environ["PATH"]]),
        "PYTHONUTF8": "1",
    }
    for command, expected in parse_steps(console_blocks(doc)[index]):
        done = subprocess.run(["sh", "-c", command], cwd=tmp_path, env=env, capture_output=True, text=True, encoding="utf-8")
        assert done.returncode == 0, f"{command}\n{done.stderr}"
        if expected:
            assert done.stdout == "\n".join(expected) + "\n", command
