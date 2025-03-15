#!/usr/bin/env python3
"""
Code2Prompt MCP Server

An MCP server that allows LLMs to extract context from codebases using code2prompt.
The LLM can control include/exclude patterns to focus on relevant files only.
"""

import logging
from typing import Dict, List, Optional, Any, Union
import asyncio
from code2prompt_rs import Code2Prompt
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='code2prompt_mcp.log'
)
logger = logging.getLogger('code2prompt_mcp')

# Initialize FastMCP server
mcp = FastMCP("code2prompt")

@mcp.tool()
async def get_context(
    path: str = ".",
    include_patterns: List[str] = [],
    exclude_patterns: List[str] = [],
    include_priority: bool = False,
    line_numbers: bool = True,
    relative_paths: bool = True,
    exclude_from_tree: bool = False,
    no_codeblock: bool = False,
    follow_symlinks: bool = False,
    hidden: bool = False,
    no_ignore: bool = False,
    template: Optional[str] = None,
    encoding: str = "cl100k"
) -> Dict[str, Any]:
    """
    Retrieve context from a codebase using code2prompt with the specified parameters.
    
    Args:
        path: Path to the codebase
        include_patterns: List of glob patterns for files to include
        exclude_patterns: List of glob patterns for files to exclude
        include_priority: Give priority to include patterns
        line_numbers: Add line numbers to code
        relative_paths: Use relative paths
        exclude_from_tree: Exclude files from tree based on patterns
        no_codeblock: Don't wrap code in markdown blocks
        follow_symlinks: Follow symbolic links
        hidden: Include hidden directories and files
        no_ignore: Skip .gitignore rules
        template: Custom Handlebars template
        encoding: Token encoding
    
    Returns:
        Dictionary with the prompt and metadata
    """
    logger.info(f"Getting context from {path} with include patterns: {include_patterns}, exclude patterns: {exclude_patterns}")
    
    try:
        # Create a Code2Prompt instance - use wrapper for async
        prompt = await asyncio.to_thread(
            Code2Prompt,
            path=path,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            include_priority=include_priority,
            line_numbers=line_numbers,
            relative_paths=relative_paths,
            exclude_from_tree=exclude_from_tree,
            no_codeblock=no_codeblock,
            follow_symlinks=follow_symlinks,
            hidden=hidden,
            no_ignore=no_ignore
        )
        
        # Generate the prompt - use wrapper for async
        result = await asyncio.to_thread(
            prompt.generate,
            template=template, 
            encoding=encoding
        )
        
        return {
            "prompt": result.get("prompt", ""),
            "directory": result.get("directory", ""),
            "token_count": result.get("token_count", 0),
            "model_info": result.get("model_info", "")
        }
    except Exception as e:
        logger.exception("Error generating context")
        return {"error": str(e)}

@mcp.tool()
async def get_git_diff(path: str = ".") -> Dict[str, str]:
    """
    Get git diff for the repository.
    
    Args:
        path: Path to the git repository
    
    Returns:
        Dictionary containing the git diff
    """
    try:
        prompt = await asyncio.to_thread(Code2Prompt, path=path)
        diff = await asyncio.to_thread(prompt.get_git_diff)
        return {"diff": diff}
    except Exception as e:
        logger.exception("Error getting git diff")
        return {"error": str(e)}

@mcp.tool()
async def get_branch_diff(
    path: str = ".", 
    branch1: str = "main", 
    branch2: str = "HEAD"
) -> Dict[str, str]:
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
        prompt = await asyncio.to_thread(Code2Prompt, path=path)
        diff = await asyncio.to_thread(
            prompt.get_git_diff_between_branches,
            branch1,
            branch2
        )
        return {"diff": diff}
    except Exception as e:
        logger.exception("Error getting branch diff")
        return {"error": str(e)}

@mcp.tool()
async def get_git_log(
    path: str = ".", 
    branch1: str = "main", 
    branch2: str = "HEAD"
) -> Dict[str, str]:
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
        prompt = await asyncio.to_thread(Code2Prompt, path=path)
        log = await asyncio.to_thread(prompt.get_git_log, branch1, branch2)
        return {"log": log}
    except Exception as e:
        logger.exception("Error getting git log")
        return {"error": str(e)}

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')