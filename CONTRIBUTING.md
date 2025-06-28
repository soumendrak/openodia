# Contributing

Thank you for considering contributing to **OpenOdia**!

## Development setup

1. Install project dependencies using `uv`:
   ```bash
   pip install uv
   uv sync --all-extras
   ```
2. Run tests with:
   ```bash
   uv run pytest -v
   ```
   Ensure tests pass on your local machine.
3. We expect new features to include tests and to maintain overall coverage above **70%**.

## Pull requests

- Format and lint your code using **Ruff**:
  ```bash
  uv run ruff format
  uv run ruff check
  ```
- Run **Bandit** for security scanning:
  ```bash
  uv run bandit -r -lll ./openodia ./tests
  ```
- Open a pull request and be ready for review.
