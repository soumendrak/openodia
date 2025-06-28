# Migration to uv - Next Steps

This repository has been migrated from Poetry to uv. Here's what to do next:

## 1. Install uv
```bash
# Install uv (if not already installed)
pip install uv
```

## 2. Initialize uv project
```bash
# Navigate to project directory
cd openodia

# Initialize uv and generate lock file
uv sync --all-extras
```

## 3. Common uv commands (replacements for poetry commands)

| Poetry Command | uv Equivalent |
|---|---|
| `poetry install` | `uv sync` |
| `poetry install --extras dev` | `uv sync --all-extras` |
| `poetry add package` | `uv add package` |
| `poetry add --group dev package` | `uv add --dev package` |
| `poetry remove package` | `uv remove package` |
| `poetry run command` | `uv run command` |
| `poetry build` | `uv build` |
| `poetry shell` | `uv shell` |
| `poetry lock` | `uv lock` |
| `poetry show` | `uv tree` |

## 4. Development workflow
```bash
# Install all dependencies (including dev)
uv sync --all-extras

# Run tests
uv run pytest

# Run linting
uv run ruff check

# Run formatting (if needed)
uv run ruff format --check

# Run security analysis
uv run bandit -r ./openodia ./tests

# Run linting and formatting
uv run ruff check
uv run ruff format --check

# Build documentation
uv run mkdocs serve

# Build package
uv build
```

## 5. What changed

### Files modified:
- `pyproject.toml` - Converted from Poetry format to standard Python project format
- `.github/workflows/*` - Updated all CI/CD workflows to use uv
- `poetry.lock` - Removed (will be replaced by `uv.lock`)

### Benefits of uv:
- **Faster**: 10-100x faster than Poetry for dependency resolution
- **Better lockfiles**: More deterministic dependency resolution  
- **Standards compliant**: Uses standard `pyproject.toml` format
- **Modern**: Active development and frequent updates
- **Compatible**: Drop-in replacement for most Poetry workflows

## 6. Verification
After running `uv sync --all-extras`, verify everything works:
```bash
# Run tests
uv run pytest

# Try importing the package
uv run python -c "import openodia; print(openodia.__version__)"
```

The migration preserves all functionality while making dependency management faster and more reliable.
