[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/odancona-code2prompt-mcp-badge.png)](https://mseep.ai/app/odancona-code2prompt-mcp)

# code2prompt-mcp

An MCP server that generates contextual prompts from codebases, making it easier for AI assistants to understand and work with your code repositories.

## About

code2prompt-mcp leverages the high-performance [code2prompt-rs](https://github.com/yourusername/code2prompt-rs) Rust library to analyze codebases and produce structured summaries. It helps bridge the gap between your code and language models by extracting relevant context in a format that's optimized for AI consumption.

## Installation

This project uses [Rye](https://rye.astral.sh/) for dependency management, make sure you have it installed.

To install the necessary dependencies, and build the module in the local environment, run:

```bash
# Clone the repository
git clone https://github.com/odancona/code2prompt-mcp.git
cd code2prompt-mcp

# Install dependencies with Rye
rye build
```

It will install all the required dependencies specified in the `pyproject.toml` file in the `.venv` directory.

## Usage

Run the MCP server:

```bash
rye run python code2prompt_mcp.main
```

## License

MIT License - See LICENSE file for details.

## Development

For testing, you can use the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector python -m code2prompt_mcp.main
```
