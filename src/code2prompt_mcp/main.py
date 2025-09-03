"""
Code2Prompt MCP Server

An MCP server that allows LLMs to extract context from codebases using the code2prompt_rs SDK.
"""

from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP
import logging
import colorlog
from pathlib import Path
from code2prompt_rs import Code2Prompt

# Initialize logger at module level
logger = logging.getLogger(__name__)

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


@mcp.tool()
async def get_context_for_gemini(
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
) -> str:
    """
    Retrieve context from a codebase using code2prompt and save it to a file.
    
    This function works identically to get_context but saves the output to 
    "latest_context.txt" in the current working directory and returns the 
    absolute file path instead of the content.
    
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
        Absolute file path to the created "latest_context.txt" file
        
    Raises:
        Exception: If file cannot be created due to permissions, disk space, or other IO issues
    """
    logger.info(f"Getting context from {path} for Gemini file output")
    
    # Step 1: Get context using existing function
    try:
        context_result = await get_context(
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
            template=template,
            encoding=encoding
        )
    except Exception as e:
        logger.error(f"Failed to generate context: {str(e)}")
        raise Exception(f"Failed to generate codebase context: {str(e)}")
    
    # Step 2: Define output file path in current working directory
    output_file = Path.cwd() / "latest_context.txt"
    logger.info(f"Writing context to file: {output_file}")
    
    # Step 3: Write content to file with comprehensive error handling
    try:
        # Handle empty context case
        content = context_result["prompt"]
        if not content or content.strip() == "":
            content = "# No context generated\n\nNo files were found or all files were excluded by the specified patterns.\n"
        
        # Write content atomically using pathlib
        output_file.write_text(content, encoding="utf-8")
        logger.info(f"Successfully wrote {len(content)} characters to {output_file}")
        
    except PermissionError as e:
        error_msg = f"Permission denied when writing to {output_file}: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except OSError as e:
        if e.errno == 28:  # ENOSPC - No space left on device
            error_msg = f"Insufficient disk space to write context file to {output_file}"
            logger.error(error_msg)
            raise Exception(error_msg)
        else:
            error_msg = f"Failed to write context file to {output_file}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error writing context file to {output_file}: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    # Step 4: Return absolute path
    absolute_path = str(output_file.absolute())
    logger.info(f"Context successfully saved to: {absolute_path}")
    return absolute_path


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
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    mcp.run(transport='stdio')