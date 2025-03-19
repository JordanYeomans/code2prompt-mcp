#!/usr/bin/env python3
"""
Code2Prompt MCP Server

An MCP server that allows LLMs to extract context from codebases using code2prompt CLI.
The LLM can control include/exclude patterns to focus on relevant files only.
"""

import tempfile
from typing import Dict, List, Optional, Any
import asyncio
import os
import json
from mcp.server.fastmcp import FastMCP
import logging
import colorlog

async def run_code2prompt(args: List[str]) -> Dict[str, Any]:
    """
    Run code2prompt CLI with given arguments and return the result.
    
    Args:
        args: List of command-line arguments for code2prompt
        
    Returns:
        Dictionary with the prompt and metadata
    """
    try:
        # Create a temporary file to store the output
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        # Add output file and format arguments
        output_args = ["-O", tmp_path]
        if "-F" not in args and "--output-format" not in args:
            output_args.extend(["-F", "json"])
        
        # Add no-clipboard flag
        if "--no-clipboard" not in args:
            output_args.append("--no-clipboard")
            
        # Run the code2prompt command
        cmd_args = [*args, *output_args]
        logger.info(f"Running: code2prompt {' '.join(cmd_args)}")
        process = await asyncio.create_subprocess_exec(
            "code2prompt", 
            *cmd_args, 
            stdout=asyncio.subprocess.PIPE, 
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Error running code2prompt: {stderr.decode()}")
            return {"error": stderr.decode()}
        
        # Read the output file
        with open(tmp_path, 'r') as f:
            content = f.read()
        
        # Clean up the temp file
        os.unlink(tmp_path)
        
        # Try to extract token count from stdout
        token_info = {}
        stdout_text = stdout.decode()
        if "Token count:" in stdout_text:
            try:
                token_part = stdout_text.split("Token count:")[1].split(",")[0].strip()
                token_count = int(token_part.replace(",", ""))
                token_info["token_count"] = token_count
                
                if "Model info:" in stdout_text:
                    model_info = stdout_text.split("Model info:")[1].strip()
                    token_info["model_info"] = model_info
            except (ValueError, IndexError):
                logger.warning("Could not parse token count information")
        
        # Directory path extracted from the args - the last argument is always the path
        directory = None
        for i, arg in enumerate(args):
            if i > 0 and args[i-1] not in ["-i", "-e", "-c", "-t", "-O", "-F", "--tokens", "--sort"]:
                directory = arg
        
        # Return the result
        return {
            "prompt": content,
            "directory": directory or args[-1],
            **token_info
        }
    
    except Exception as e:
        logger.exception("Error executing code2prompt")
        return {"error": str(e)}

@mcp.tool()
async def get_context(
    path: str = ".",
    include_patterns: List[str] = [],
    exclude_patterns: List[str] = [],
    include_priority: bool = False,
    line_numbers: bool = True,
    relative_paths: bool = True,
    full_directory_tree: bool = False,
    no_codeblock: bool = False,
    follow_symlinks: bool = False,
    hidden: bool = False,
    no_ignore: bool = False,
    template: Optional[str] = None,
    encoding: Optional[str] = None,
    tokens: str = "format",
    sort: Optional[str] = None,
    output_format: str = "markdown"
) -> Dict[str, Any]:
    """
    Retrieve context from a codebase using code2prompt CLI with the specified parameters.
    
    Args:
        path: Path to the codebase
        include_patterns: List of glob patterns for files to include
        exclude_patterns: List of glob patterns for files to exclude
        include_priority: Give priority to include patterns
        line_numbers: Add line numbers to code
        relative_paths: Use relative paths
        full_directory_tree: List the full directory tree
        no_codeblock: Don't wrap code in markdown blocks
        follow_symlinks: Follow symbolic links
        hidden: Include hidden directories and files
        no_ignore: Skip .gitignore rules
        template: Custom Handlebars template
        encoding: Token encoding (cl100k, etc.)
        tokens: Token count format (format or raw)
        sort: Sort order for files
        output_format: Output format (markdown, json, xml)
    
    Returns:
        Dictionary with the prompt and metadata
    """
    logger.info(f"Getting context from {path} with include patterns: {include_patterns}, exclude patterns: {exclude_patterns}")
    
    args = []
    
    # Add include patterns
    for pattern in include_patterns:
        args.extend(["-i", pattern])
    
    # Add exclude patterns
    for pattern in exclude_patterns:
        args.extend(["-e", pattern])
    
    # Add boolean flags
    if include_priority:
        args.append("--include-priority")
    if line_numbers:
        args.append("-l")
    if not relative_paths:
        args.append("--absolute-paths")
    if full_directory_tree:
        args.append("--full-directory-tree")
    if no_codeblock:
        args.append("--no-codeblock")
    if follow_symlinks:
        args.append("-L")
    if hidden:
        args.append("--hidden")
    if no_ignore:
        args.append("--no-ignore")
    
    # Add optional parameters
    if template:
        args.extend(["-t", template])
    if encoding:
        args.extend(["-c", encoding])
    if tokens:
        args.extend(["--tokens", tokens])
    if sort:
        args.extend(["--sort", sort])
    if output_format:
        args.extend(["-F", output_format])
    
    # Add the path argument
    args.append(path)
    
    # Run code2prompt and return the result
    return await run_code2prompt(args)

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
        args = ["-d", path]
        return await run_code2prompt(args)
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
        args = ["--git-diff-branch", branch1, branch2, path]
        return await run_code2prompt(args)
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
        args = ["--git-log-branch", branch1, branch2, path]
        return await run_code2prompt(args)
    except Exception as e:
        logger.exception("Error getting git log")
        return {"error": str(e)}

if __name__ == "__main__":
    # Initialize FastMCP server
    mcp = FastMCP("code2prompt")
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
    mcp.run(transport='sse')