# Code2Prompt MCP Server Installation Guide

This guide provides step-by-step instructions for installing and configuring the code2prompt MCP server to work with Claude Code.

## Prerequisites

- [Rye](https://rye.astral.sh/) package manager installed
- Claude Code installed and running
- Git for cloning the repository

## Installation Steps

### 1. Clone and Navigate to Repository

```bash
git clone https://github.com/odancona/code2prompt-mcp.git
cd code2prompt-mcp
```

### 2. Install Dependencies and Package

```bash
# Sync dependencies with rye
rye sync

# Install the package in editable mode using the virtual environment
.venv/bin/pip install -e .
```

### 3. Verify Installation

Test that the MCP server can start correctly:

```bash
rye run python -m code2prompt_mcp.main
```

If successful, you should see the server start without errors. Press `Ctrl+C` to stop it.

### 4. Configure Claude Code

#### Option A: Automatic Configuration (Recommended)

If you have the `claude` CLI tool:

```bash
claude mcp add-json "code2prompt" '{
  "command": "/path/to/your/project/.venv/bin/python",
  "args": ["-m", "code2prompt_mcp.main"],
  "cwd": "/path/to/your/project"
}'
```

#### Option B: Manual Configuration

1. **Locate your Claude Code configuration file:**
   - Path: `~/.claude.json`

2. **Add the MCP server configuration:**

   Find the `"mcpServers"` section in your `~/.claude.json` file and add:

   ```json
   {
     "mcpServers": {
       "code2prompt": {
         "command": "/Users/YOUR_USERNAME/path/to/code2prompt-mcp/.venv/bin/python",
         "args": [
           "-m",
           "code2prompt_mcp.main"
         ],
         "cwd": "/Users/YOUR_USERNAME/path/to/code2prompt-mcp"
       }
     }
   }
   ```

   **Important:** Replace the paths with your actual project location:
   - Replace `YOUR_USERNAME` with your actual username
   - Replace `path/to/code2prompt-mcp` with the full path to your cloned repository

3. **Example full configuration:**

   ```json
   {
     "mcpServers": {
       "code2prompt": {
         "command": "/Users/jordanyeomans/Documents/claude_working/code2prompt-mcp/code2prompt-mcp/.venv/bin/python",
         "args": [
           "-m",
           "code2prompt_mcp.main"
         ],
         "cwd": "/Users/jordanyeomans/Documents/claude_working/code2prompt-mcp/code2prompt-mcp"
       }
     }
   }
   ```

### 5. Restart Claude Code

After updating the configuration, restart Claude Code completely to load the new MCP server.

### 6. Verify MCP Server Connection

1. In Claude Code, type `/mcp` to see available MCP servers
2. You should see "Code2prompt MCP Server" listed with a ✓ working status
3. The server should show tools like `get_context` and `get_context_for_gemini`

## Available Tools

Once installed, you'll have access to these MCP tools:

### `get_context`
Retrieves context from a codebase and returns it as structured data.

**Parameters:**
- `path` (string): Path to the codebase (default: ".")
- `include_patterns` (array): Glob patterns for files to include
- `exclude_patterns` (array): Glob patterns for files to exclude
- `line_numbers` (boolean): Add line numbers to code (default: true)
- `code_blocks` (boolean): Wrap code in markdown blocks (default: true)
- Plus many more configuration options

### `get_context_for_gemini`
Same as `get_context` but saves the output to `latest_context.txt` and returns the file path.

**Use case:** Perfect for when you need to save codebase context to a file for external use or sharing with other tools.

## Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'code2prompt_mcp'"

**Solution:** Ensure you've installed the package in editable mode:
```bash
.venv/bin/pip install -e .
```

#### 2. MCP Server Shows "Failed" Status

**Causes & Solutions:**
- **Wrong Python path:** Ensure you're using the full path to `.venv/bin/python`
- **Wrong working directory:** Ensure `cwd` points to the project root (where `pyproject.toml` is located)
- **Module not found:** Re-run the pip install command above

#### 3. "command not found: python"

**Solution:** Use the full path to the Python executable in your virtual environment instead of just `python`.

#### 4. Server starts but tools don't appear

**Solution:** 
1. Restart Claude Code completely
2. Check that the MCP server shows as "working" in `/mcp`
3. Verify your configuration syntax is correct (valid JSON)

### Debug Steps

1. **Test manual server start:**
   ```bash
   cd /path/to/your/code2prompt-mcp
   rye run python -m code2prompt_mcp.main
   ```

2. **Check virtual environment:**
   ```bash
   .venv/bin/python -c "import code2prompt_mcp; print('Module found!')"
   ```

3. **Validate JSON configuration:**
   Use a JSON validator to ensure your `~/.claude.json` file is properly formatted.

## Configuration Tips

- **Use absolute paths:** Always use full absolute paths in the configuration
- **Backup your config:** Keep a backup of your `~/.claude.json` before making changes
- **Test incrementally:** Add one MCP server at a time to isolate issues

## Example Usage

Once installed, you can use the tools in Claude Code:

```
Please use get_context to analyze my Python project in ./src and show me all the modules with line numbers.
```

```
Use get_context_for_gemini to save the context of this repository to a file I can share.
```

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all paths are correct and absolute
3. Ensure the virtual environment has the package installed
4. Test the server manually before configuring Claude Code

---

## Quick Reference

**Installation Commands:**
```bash
git clone https://github.com/odancona/code2prompt-mcp.git
cd code2prompt-mcp
rye sync
.venv/bin/pip install -e .
```

**Test Command:**
```bash
rye run python -m code2prompt_mcp.main
```

**Configuration Location:**
- `~/.claude.json`

**Key Configuration:**
```json
"code2prompt": {
  "command": "/FULL/PATH/TO/.venv/bin/python",
  "args": ["-m", "code2prompt_mcp.main"],
  "cwd": "/FULL/PATH/TO/PROJECT"
}
```