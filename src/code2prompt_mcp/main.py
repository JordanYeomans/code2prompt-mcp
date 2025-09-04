"""
Code2Prompt MCP Server

An MCP server that allows LLMs to extract context from codebases using the code2prompt_rs SDK.
"""

from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP
import logging
import colorlog
import os
import tempfile
import uuid
from pathlib import Path
from code2prompt_rs import Code2Prompt
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()

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
    Retrieve context from a codebase using code2prompt and save it to a temporary file.
    
    This function works identically to get_context but saves the output to a unique 
    temporary file in the system's temp directory under "Claude Code Gemini Context" 
    subfolder and returns the absolute file path instead of the content.
    
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
        Absolute file path to the created temporary context file with UUID
        
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
    
    # Step 2: Create temp directory and define output file path with UUID
    temp_dir = Path(tempfile.gettempdir()) / "Claude Code Gemini Context"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename with UUID to prevent race conditions
    unique_filename = f"context_{uuid.uuid4().hex}.txt"
    output_file = temp_dir / unique_filename
    logger.info(f"Writing context to temp file: {output_file}")
    
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


@mcp.tool()
async def ask_gemini_question(
    question: str,
    path: str = ".",
    model: str = "gemini-2.5-pro",
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
    Ask a question about a codebase using Google's Gemini AI.
    
    This tool first extracts structured context from a codebase by scanning files and 
    generating a comprehensive summary with code snippets, directory structure, and 
    file content. It then saves this context to a temporary file and sends it along 
    with your question to Google's Gemini AI model for intelligent analysis and answers.
    
    IMPORTANT: Gemini is stateless across invocations - it cannot remember previous 
    conversations or sessions. For follow-up questions, you MUST include 100% of the 
    required context again. The tool will always extract the full codebase context 
    for each question to ensure Gemini has complete information.
    
    The context extraction process:
    - Scans the specified directory and subdirectories for relevant files
    - Applies include/exclude patterns to filter files
    - Generates formatted output with optional line numbers and code blocks
    - Saves the complete context to a unique temporary file with UUID naming
    - Combines the context with your question and sends to Gemini AI
    
    Args:
        question: The natural language question to ask about the codebase (required)
        path: Path to the codebase
        model: Gemini model to use (gemini-2.5-pro, gemini-2.5-flash, default: gemini-2.5-pro)
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
        Dictionary with AI answer, context file path, and metadata
    
    Raises:
        Exception: If API key is missing, context extraction fails, or AI API fails
    """
    logger.info(f"Processing Gemini question about codebase at {path} using model {model}")
    
    # Step 1: Validate model selection
    supported_models = ["gemini-2.5-pro", "gemini-2.5-flash"]
    if model not in supported_models:
        error_msg = f"Unsupported model '{model}'. Supported models: {', '.join(supported_models)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    # Step 2: Validate API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        error_msg = (
            "GEMINI_API_KEY environment variable is required. "
            "Please set it in your environment or create a .env file with: "
            "GEMINI_API_KEY=your_api_key_here"
        )
        logger.error("Missing GEMINI_API_KEY")
        raise Exception(error_msg)
    
    # Step 3: Extract context using existing tool
    try:
        context_file_path = await get_context_for_gemini(
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
        logger.info(f"Context extracted to: {context_file_path}")
    except Exception as e:
        logger.error(f"Failed to extract context: {str(e)}")
        raise Exception(f"Context extraction failed: {str(e)}")
    
    # Step 4: Read the context file
    try:
        context_file = Path(context_file_path)
        if not context_file.exists():
            raise Exception(f"Context file not found at: {context_file_path}")
        
        context_content = context_file.read_text(encoding="utf-8")
        logger.info(f"Read context file with {len(context_content)} characters")
    except Exception as e:
        logger.error(f"Failed to read context file: {str(e)}")
        raise Exception(f"Failed to read context file: {str(e)}")
    
    # Step 5: Initialize Gemini AI client and query
    try:
        # Initialize the Google AI client
        client = genai.Client(api_key=api_key)
        
        # Combine context with question
        full_prompt = f"{context_content}\n\nQuestion: {question}"
        
        # Generate response using the specified Gemini model
        logger.info(f"Sending query to Gemini AI using model: {model}")
        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=30000
            )
        )
        
        logger.info("Successfully received response from Gemini AI")
        
        # Extract answer from response
        answer = response.text if hasattr(response, 'text') else str(response)
        
        # Return structured response
        return {
            "answer": answer,
            "context_file": context_file_path,
            "token_count": len(full_prompt.split()),  # Simple token approximation
            "model_used": model
        }
        
    except Exception as e:
        # Handle Google AI specific exceptions
        error_type = type(e).__name__
        logger.error(f"Gemini AI request failed ({error_type}): {str(e)}")
        
        # Return structured error without exposing sensitive information
        if "authentication" in str(e).lower() or "api key" in str(e).lower():
            raise Exception("Authentication failed: Invalid or expired API key. Please check your GEMINI_API_KEY.")
        elif "rate limit" in str(e).lower() or "quota" in str(e).lower():
            raise Exception("Rate limit exceeded. Please wait before making another request.")
        elif "safety" in str(e).lower() or "blocked" in str(e).lower():
            raise Exception("Content blocked by safety filters. Please rephrase your question.")
        elif "model" in str(e).lower() and "unavailable" in str(e).lower():
            raise Exception("Gemini model temporarily unavailable. Please try again later.")
        elif "timeout" in str(e).lower() or "network" in str(e).lower():
            raise Exception("Network timeout. Please check your connection and try again.")
        else:
            raise Exception(f"AI service error: {str(e)}")


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