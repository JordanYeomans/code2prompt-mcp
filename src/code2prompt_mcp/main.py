"""
Code2Prompt MCP Server

An MCP server that allows LLMs to extract context from codebases using the code2prompt_rs SDK.
"""

from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP
import logging
import colorlog
from code2prompt_rs import Code2Prompt

mcp = FastMCP("code2prompt")


@mcp.tool()
async def get_context(
    path: str = ".",
    include_patterns: List[str] = [],
    exclude_patterns: List[str] = [],
    include_priority: bool = False,
    line_numbers: bool = True,
    absolute_paths: bool = False,
    full_directory_tree: bool = False,
    code_blocks: bool = True,
    follow_symlinks: bool = False,
    include_hidden: bool = False,
    template: Optional[str] = None,
    encoding: Optional[str] = "cl100k",
) -> Dict[str, Any]:
    """
    Retrieve context from a codebase using code2prompt with the specified parameters.
    
    Args:
        path: Path to the codebase
        include_patterns: List of glob patterns for files to include
        exclude_patterns: List of glob patterns for files to exclude
        include_priority: Give priority to include patterns
        line_numbers: Add line numbers to code
        absolute_paths: Use absolute paths instead of relative paths
        full_directory_tree: List the full directory tree
        code_blocks: Wrap code in markdown code blocks
        follow_symlinks: Follow symbolic links
        include_hidden: Include hidden directories and files
        template: Custom Handlebars template
        encoding: Token encoding (cl100k, gpt2, p50k_base)
    
    Returns:
        Dictionary with the prompt and metadata
    """
    logger.info(f"Getting context from {path} with include patterns: {include_patterns}, exclude patterns: {exclude_patterns}")
    
    # Initialize the Code2Prompt instance with all parameters
    prompt = Code2Prompt(
        path=path,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        include_priority=include_priority,
        line_numbers=line_numbers,
        absolute_paths=absolute_paths,
        full_directory_tree=full_directory_tree,
        code_blocks=code_blocks,
        follow_symlinks=follow_symlinks,
        include_hidden=include_hidden,
    )
    
    # Generate the prompt directly using the instance method
    # Note: sort_by configuration should be added if supported by the SDK
    result = prompt.generate(template=template, encoding=encoding)
    
    # Return structured result
    return {
        "prompt": result.prompt,
        "directory": str(result.directory),
        "token_count": result.token_count
    }

if __name__ == "__main__":
    # Initialize FastMCP server
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={},
        style="%",
    )
    handler.setFormatter(formatter)
    logger = colorlog.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    mcp.run(transport='stdio')