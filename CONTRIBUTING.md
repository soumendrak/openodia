# Contributing

Pull requests are welcome. Set up the repository, run the checks, and follow the rules below.

## Set up

Use Python 3.11 or newer.

```bash
git clone https://github.com/soumendrak/openodia.git
cd openodia
uv sync --all-extras
```

## Run the checks

Run these before you open a pull request.

```bash
uv run ruff check
uv run ruff format --check
uv run bandit -r -lll ./openodia ./tests
uv run pytest --cov=openodia
uv run mkdocs build --strict
uv lock --check
```

`uv run mkdocs build --strict` builds the documentation site. A broken link or a bad API reference fails that build.

## Rules for a change

- Write the failing test first. A behavior change without a test is incomplete.
- Do not change `version` in `pyproject.toml` or `openodia/__init__.py`. A merge to `main` with a version that PyPI does not have yet publishes a release.
- Do not add code comments, `# type: ignore`, or `# pragma: no cover`. Name things so the code reads on its own.
- Put a new feature in its own module, and keep a pull request under about 400 changed lines.
- Do not change the default command-line output. Add a flag.
- Add a line to the Unreleased section of `CHANGELOG.md` when users can see the change.
- A `pycon` block under `docs/` is executed by `tests/test_docs_guides.py`. The output on the page has to be what the code prints. A `console` block in `docs/guides/cli.md` is executed by `tests/test_agent_docs.py`.

Command-line behavior, JSON shapes, and exit codes are specified in [AGENTS.md](https://github.com/soumendrak/openodia/blob/main/AGENTS.md).

## Report a bug

Open an [issue](https://github.com/soumendrak/openodia/issues) and include the command, the input, and the output you got.

## Conduct

The project uses the [Contributor Covenant](https://github.com/soumendrak/openodia/blob/main/CODE_OF_CONDUCT.md).
