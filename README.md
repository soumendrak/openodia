![image](docs/cover-pic.png)

<h4 align="center">
  <a href="https://img.shields.io/badge/Python-3.10+-blue"><img alt="python 3.10+" src="https://img.shields.io/badge/Python-3.10+-blue"></a>
  <a href="https://github.com/soumendrak/openodia/actions/workflows/codecov.yml"><img alt="Code coverage" src="https://github.com/soumendrak/openodia/actions/workflows/codecov.yml/badge.svg"></a>
  <a href="https://github.com/soumendrak/openodia/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
  <a href="https://codecov.io/gh/soumendrak/openodia"><img alt="code coverage" src="https://codecov.io/gh/soumendrak/openodia/branch/main/graph/badge.svg?token=1TOQIKGDQ2"/></a>
  <a href="https://app.fossa.com/projects/git%2Bgithub.com%2Fsoumendrak%2Fopenodia?ref=badge_shield" alt="FOSSA Status"><img src="https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsoumendrak%2Fopenodia.svg?type=shield" alt="license"/></a>
  <a href="https://pepy.tech/project/openodia" alt="downloads"><img src="https://static.pepy.tech/personalized-badge/openodia?period=total&units=none&left_color=black&right_color=orange&left_text=Downloads"/></a>
</h4>


- `openodia` is a Python package which contains various tools on Odia language.
- The short term goal of this package is to not make state-of-the-art methods, but to make tools which work.

## Install

- Requires **Python 3.10 or higher**.
- The library is tested on Python 3.10, 3.11, 3.12, 3.13, and 3.14.

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

## LLM Tool Interface

OpenOdia provides a tool interface for integration with AI agents and LLMs (OpenAI, Anthropic, MCP-compatible clients).

### Available Tools

| Tool | Description |
|------|-------------|
| `translate_to_odia` | Translate text from any language to Odia |
| `translate_from_odia` | Translate Odia text to other languages |
| `universal_translate` | Translate between any two languages |
| `detect_language` | Detect if text is Odia or non-Odia |
| `tokenize_words` | Split Odia text into word tokens |
| `tokenize_sentences` | Split Odia text into sentences |
| `remove_stopwords` | Remove common Odia stopwords |
| `summarize_text` | Generate summary of Odia text |
| `generate_odia_names` | Generate random Odia full names |
| `generate_odia_firstnames` | Generate Odia first names |
| `generate_odia_surnames` | Generate Odia surnames |

### Direct Usage

```python
from openodia import execute, tools

# Execute a tool directly
result = execute("detect_language", {"text": "ନମସ୍କାର"})
# {'success': True, 'result': {'language': 'odia', 'confidence_score': 1.0}}

result = execute("tokenize_words", {"text": "ନମସ୍କାର ବନ୍ଧୁ"})
# {'success': True, 'result': ['ନମସ୍କାର', 'ବନ୍ଧୁ']}

# Get tool definitions for LLM integration
openai_tools = tools.get_openai_tools()      # OpenAI function calling format
anthropic_tools = tools.get_anthropic_tools() # Anthropic tool use format
mcp_tools = tools.get_mcp_tools()            # MCP format
```

### MCP Server

OpenOdia includes an MCP (Model Context Protocol) server for IDE and agent integration.

```bash
# Run the MCP server
python -m openodia.mcp_server

# Or after installation
openodia-mcp
```

**MCP Client Configuration** (for Claude Desktop, Cursor, etc.):

```json
{
    "mcpServers": {
        "openodia": {
            "command": "python",
            "args": ["-m", "openodia.mcp_server"]
        }
    }
}
``` 

## License

<a align="center">
<a href="https://app.fossa.com/projects/git%2Bgithub.com%2Fsoumendrak%2Fopenodia?ref=badge_large" alt="FOSSA Status"><img src="https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsoumendrak%2Fopenodia.svg?type=large"/></a>
</a>
