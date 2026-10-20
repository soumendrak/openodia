![image](docs/cover-pic.png)

<h4 align="center">
  <a href="https://img.shields.io/badge/Python-3.11+-blue"><img alt="python 3.11+" src="https://img.shields.io/badge/Python-3.11+-blue"></a>
  <a href="https://github.com/soumendrak/openodia/actions/workflows/codecov.yml"><img alt="Code coverage" src="https://github.com/soumendrak/openodia/actions/workflows/codecov.yml/badge.svg"></a>
  <a href="https://github.com/soumendrak/openodia/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
  <a href="https://codecov.io/gh/soumendrak/openodia"><img alt="code coverage" src="https://codecov.io/gh/soumendrak/openodia/branch/main/graph/badge.svg?token=1TOQIKGDQ2"/></a>
  <a href="https://pepy.tech/project/openodia" alt="downloads"><img src="https://static.pepy.tech/personalized-badge/openodia?period=total&units=none&left_color=black&right_color=orange&left_text=Downloads"/></a>
</h4>


- `openodia` is a Python package which contains various tools on Odia language.
- The short term goal of this package is to not make state-of-the-art methods, but to make tools which work.

## Install

- Requires **Python 3.11 or higher**.
- The library is tested on Python 3.11, 3.12, 3.13, and 3.14.

### Using pip

```bash
pip install openodia
```

### Using uv (recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package installer and resolver.

```bash
# Install uv if you haven't already
pip install uv

# Install openodia
uv pip install openodia

# Or add to your project
uv add openodia
```

### From source

```bash
git clone https://github.com/soumendrak/openodia.git
cd openodia
uv sync  # or: pip install -e .
```

## Usage and Documentation

For usage and further documentation please visit the [Documentation](https://openodia.soumendrak.com/) page. 

### Command-line interface

Run `openodia --help` or `python -m openodia --help` for commands, and
`openodia --version` for the installed version.

```bash
openodia tokenize 'ରାମ ସୀତା'
openodia tokenize --file input.txt
cat input.txt | python -m openodia tokenize -
```

Text arguments are literal text, even when they match an existing filename.
Use `--file` to read a UTF-8 file explicitly (implicit file detection has been
removed). Pass `-` without `--file` to read UTF-8 text from stdin.

## Sponsor

If this project helps you, consider [sponsoring my work on GitHub](https://github.com/sponsors/soumendrak). Your support helps fund maintenance, documentation, and continued development.

## License

Released under the [MIT License](LICENSE).
