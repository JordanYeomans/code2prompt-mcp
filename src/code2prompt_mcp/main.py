#!/usr/bin/env python3
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
    ignore_git_ignore: bool = False,
    template: Optional[str] = None,
    encoding: Optional[str] = "cl100k",
    sort_by: Optional[str] = None
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
        ignore_git_ignore: Ignore .gitignore rules
        template: Custom Handlebars template
        encoding: Token encoding (cl100k, gpt2, p50k_base)
        sort_by: Sort order for files (name_asc, name_desc, date_asc, date_desc)
    
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
        ignore_git_ignore=ignore_git_ignore
    )
    
    # Create a session for additional configuration
    session = prompt.session()
    
    # Apply optional configurations
    if sort_by:
        session = session.sort_by(sort_by)
    
    # Generate the prompt
    result = session.generate(template=template, encoding=encoding)
    
    # Return structured result
    return {
        "prompt": result.prompt,
        "directory": str(result.directory),
        "token_count": result.token_count
    }

@mcp.tool()
async def get_git_diff(path: str = ".") -> Dict[str, Any]:
    """
    Get git diff for uncommitted changes in the repository.
    
    Args:
        path: Path to the git repository
    
    Returns:
        Dictionary containing the git diff
    """
    try:
        prompt = Code2Prompt(path=path)
        result = prompt.git_diff()
        
        return {
            "prompt": result.prompt,
            "directory": str(result.directory),
            "token_count": result.token_count
        }
    except Exception as e:
        logger.exception("Error getting git diff")
        return {"error": str(e)}

@mcp.tool()
async def get_branch_diff(
    path: str = ".", 
    branch1: str = "main", 
    branch2: str = "HEAD"
) -> Dict[str, Any]:
    """
    Get git diff between two branches.
    
    Args:
        path: Path to the git repository
        branch1: First branch name
        branch2: Second branch name
    
    Returns:
        Dictionary containing the diff between branches
    """
    try:
        prompt = Code2Prompt(path=path)
        result = prompt.branch_diff(branch1=branch1, branch2=branch2)
        
        return {
            "prompt": result.prompt,
            "directory": str(result.directory),
            "token_count": result.token_count
        }
    except Exception as e:
        logger.exception("Error getting branch diff")
        return {"error": str(e)}

@mcp.tool()
async def get_git_log(
    path: str = ".", 
    branch1: str = "main", 
    branch2: str = "HEAD"
) -> Dict[str, Any]:
    """
    Get git log between two branches.
    
    Args:
        path: Path to the git repository
        branch1: First branch name
        branch2: Second branch name
    
    Returns:
        Dictionary containing the git log
    """
    try:
        prompt = Code2Prompt(path=path)
        result = prompt.git_log(branch1=branch1, branch2=branch2)
        
        return {
            "prompt": result.prompt,
            "directory": str(result.directory),
            "token_count": result.token_count
        }
    except Exception as e:
        logger.exception("Error getting git log")
        return {"error": str(e)}

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