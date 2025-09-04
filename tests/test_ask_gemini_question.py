"""
Tests for ask_gemini_question MCP tool function.

This test suite covers all functionality, edge cases, and error handling
as specified in the product specification and implementation plan.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock, mock_open
import os
import sys

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from code2prompt_mcp.main import ask_gemini_question, get_context_for_gemini


class TestAskGeminiQuestion:
    """Test suite for the ask_gemini_question function."""
    
    @pytest.fixture
    def temp_cwd(self):
        """Create a temporary directory and change to it for testing."""
        original_cwd = Path.cwd()
        temp_dir = Path(tempfile.mkdtemp())
        os.chdir(temp_dir)
        yield temp_dir
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_gemini_response(self):
        """Mock response from Gemini AI."""
        mock_response = MagicMock()
        mock_response.text = "This is a sample AI response to the codebase question."
        return mock_response
    
    @pytest.fixture
    def mock_context_file(self, temp_cwd):
        """Mock context file with test content."""
        context_file = temp_cwd / "latest_context.txt"
        context_content = "# Test Codebase Context\n\nThis is test codebase context.\n\n```python\nprint('hello')\n```"
        context_file.write_text(context_content, encoding="utf-8")
        return str(context_file.absolute()), context_content
    
    @pytest.fixture
    def valid_api_key(self):
        """Valid API key for testing."""
        return "AIzaSyTest_ValidAPIKey_123456789"
    
    # Core Functionality Tests
    
    @pytest.mark.asyncio
    async def test_successful_question_answering(self, temp_cwd, mock_gemini_response, mock_context_file, valid_api_key):
        """Test successful question answering flow."""
        context_file_path, context_content = mock_context_file
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                with patch('code2prompt_mcp.main.genai.Client') as mock_client_class:
                    # Setup mocks
                    mock_get_context.return_value = context_file_path
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    mock_client.models.generate_content.return_value = mock_gemini_response
                    
                    # Execute function
                    result = await ask_gemini_question(
                        question="What does this code do?",
                        path="/test/path",
                        model="gemini-2.5-pro",
                        include_patterns=["*.py"]
                    )
                    
                    # Verify get_context_for_gemini was called with correct parameters
                    mock_get_context.assert_called_once()
                    call_args = mock_get_context.call_args[1]
                    assert call_args['path'] == "/test/path"
                    assert call_args['include_patterns'] == ["*.py"]
                    
                    # Verify Gemini client was initialized
                    mock_client_class.assert_called_once_with(api_key=valid_api_key)
                    
                    # Verify Gemini API was called
                    mock_client.models.generate_content.assert_called_once()
                    generate_call = mock_client.models.generate_content.call_args
                    assert generate_call[1]['model'] == "gemini-2.5-pro"
                    assert "What does this code do?" in generate_call[1]['contents']
                    assert context_content in generate_call[1]['contents']
                    
                    # Verify response structure
                    assert isinstance(result, dict)
                    assert result['answer'] == "This is a sample AI response to the codebase question."
                    assert result['context_file'] == context_file_path
                    assert result['model_used'] == "gemini-2.5-pro"
                    assert isinstance(result['token_count'], int)
    
    @pytest.mark.asyncio
    async def test_gemini_flash_model_selection(self, temp_cwd, mock_gemini_response, mock_context_file, valid_api_key):
        """Test successful question answering with gemini-2.5-flash model."""
        context_file_path, context_content = mock_context_file
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                with patch('code2prompt_mcp.main.genai.Client') as mock_client_class:
                    # Setup mocks
                    mock_get_context.return_value = context_file_path
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    mock_client.models.generate_content.return_value = mock_gemini_response
                    
                    # Execute function with flash model
                    result = await ask_gemini_question(
                        question="What does this code do?",
                        model="gemini-2.5-flash"
                    )
                    
                    # Verify Gemini API was called with flash model
                    generate_call = mock_client.models.generate_content.call_args
                    assert generate_call[1]['model'] == "gemini-2.5-flash"
                    
                    # Verify response uses flash model
                    assert result['model_used'] == "gemini-2.5-flash"
    
    @pytest.mark.asyncio
    async def test_parameter_forwarding(self, temp_cwd, mock_gemini_response, mock_context_file, valid_api_key):
        """Test that all context parameters are forwarded correctly."""
        context_file_path, _ = mock_context_file
        
        test_params = {
            'question': "Test question",
            'path': "/custom/path",
            'model': "gemini-2.5-flash",
            'include_patterns': ["*.py", "*.md"],
            'exclude_patterns': ["test_*"],
            'include_priority': True,
            'line_numbers': False,
            'absolute_paths': True,
            'full_directory_tree': True,
            'code_blocks': False,
            'follow_symlinks': True,
            'include_hidden': True,
            'template': "custom template",
            'encoding': "gpt2"
        }
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                with patch('code2prompt_mcp.main.genai.Client') as mock_client_class:
                    # Setup mocks
                    mock_get_context.return_value = context_file_path
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    mock_client.models.generate_content.return_value = mock_gemini_response
                    
                    await ask_gemini_question(**test_params)
                    
                    # Verify all parameters were forwarded (excluding 'question')
                    mock_get_context.assert_called_once()
                    call_args = mock_get_context.call_args[1]
                    
                    expected_params = {k: v for k, v in test_params.items() if k not in ['question', 'model']}
                    for param, value in expected_params.items():
                        assert call_args[param] == value
    
    @pytest.mark.asyncio
    async def test_response_structure(self, temp_cwd, mock_gemini_response, mock_context_file, valid_api_key):
        """Test that response has correct structure and data types."""
        context_file_path, _ = mock_context_file
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                with patch('code2prompt_mcp.main.genai.Client') as mock_client_class:
                    mock_get_context.return_value = context_file_path
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    mock_client.models.generate_content.return_value = mock_gemini_response
                    
                    result = await ask_gemini_question(question="Test question")
                    
                    # Verify response structure
                    required_keys = ['answer', 'context_file', 'token_count', 'model_used']
                    for key in required_keys:
                        assert key in result
                    
                    # Verify data types
                    assert isinstance(result['answer'], str)
                    assert isinstance(result['context_file'], str)
                    assert isinstance(result['token_count'], int)
                    assert isinstance(result['model_used'], str)
                    
                    # Verify specific values
                    assert result['model_used'] == "gemini-2.5-pro"
                    assert result['token_count'] > 0
    
    # Error Handling Tests
    
    @pytest.mark.asyncio
    async def test_invalid_model_error(self, temp_cwd):
        """Test error handling when invalid model is provided."""
        with pytest.raises(Exception) as exc_info:
            await ask_gemini_question(
                question="Test question",
                model="invalid-model"
            )
        
        assert "Unsupported model 'invalid-model'" in str(exc_info.value)
        assert "gemini-2.5-pro, gemini-2.5-flash" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_missing_api_key_error(self, temp_cwd):
        """Test error handling when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception) as exc_info:
                await ask_gemini_question(question="Test question")
            
            assert "GEMINI_API_KEY environment variable is required" in str(exc_info.value)
            assert "create a .env file" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_context_extraction_failure(self, temp_cwd, valid_api_key):
        """Test error handling when context extraction fails."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                mock_get_context.side_effect = Exception("Invalid codebase path")
                
                with pytest.raises(Exception) as exc_info:
                    await ask_gemini_question(question="Test question")
                
                assert "Context extraction failed" in str(exc_info.value)
                assert "Invalid codebase path" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_context_file_not_found(self, temp_cwd, valid_api_key):
        """Test error handling when context file doesn't exist."""
        non_existent_path = "/non/existent/path/latest_context.txt"
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                mock_get_context.return_value = non_existent_path
                
                with pytest.raises(Exception) as exc_info:
                    await ask_gemini_question(question="Test question")
                
                assert "Context file not found at" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_context_file_read_error(self, temp_cwd, valid_api_key):
        """Test error handling when context file can't be read."""
        context_file_path = temp_cwd / "latest_context.txt"
        context_file_path.write_text("test content")
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                mock_get_context.return_value = str(context_file_path)
                
                with patch('pathlib.Path.read_text', side_effect=PermissionError("Permission denied")):
                    with pytest.raises(Exception) as exc_info:
                        await ask_gemini_question(question="Test question")
                    
                    assert "Failed to read context file" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_gemini_authentication_error(self, temp_cwd, mock_context_file, valid_api_key):
        """Test handling of Gemini authentication errors."""
        context_file_path, _ = mock_context_file
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                with patch('code2prompt_mcp.main.genai.Client') as mock_client_class:
                    mock_get_context.return_value = context_file_path
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    mock_client.models.generate_content.side_effect = Exception("Authentication failed: Invalid API key")
                    
                    with pytest.raises(Exception) as exc_info:
                        await ask_gemini_question(question="Test question")
                    
                    assert "Authentication failed: Invalid or expired API key" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_gemini_rate_limit_error(self, temp_cwd, mock_context_file, valid_api_key):
        """Test handling of Gemini rate limit errors."""
        context_file_path, _ = mock_context_file
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                with patch('code2prompt_mcp.main.genai.Client') as mock_client_class:
                    mock_get_context.return_value = context_file_path
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    mock_client.models.generate_content.side_effect = Exception("Rate limit exceeded")
                    
                    with pytest.raises(Exception) as exc_info:
                        await ask_gemini_question(question="Test question")
                    
                    assert "Rate limit exceeded" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_gemini_safety_filter_error(self, temp_cwd, mock_context_file, valid_api_key):
        """Test handling of Gemini safety filter blocks."""
        context_file_path, _ = mock_context_file
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                with patch('code2prompt_mcp.main.genai.Client') as mock_client_class:
                    mock_get_context.return_value = context_file_path
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    mock_client.models.generate_content.side_effect = Exception("Content blocked by safety filters")
                    
                    with pytest.raises(Exception) as exc_info:
                        await ask_gemini_question(question="Test question")
                    
                    assert "Content blocked by safety filters" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_gemini_model_unavailable_error(self, temp_cwd, mock_context_file, valid_api_key):
        """Test handling of Gemini model unavailable errors."""
        context_file_path, _ = mock_context_file
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                with patch('code2prompt_mcp.main.genai.Client') as mock_client_class:
                    mock_get_context.return_value = context_file_path
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    mock_client.models.generate_content.side_effect = Exception("Model temporarily unavailable")
                    
                    with pytest.raises(Exception) as exc_info:
                        await ask_gemini_question(question="Test question")
                    
                    assert "Gemini model temporarily unavailable" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_gemini_network_timeout_error(self, temp_cwd, mock_context_file, valid_api_key):
        """Test handling of network timeout errors."""
        context_file_path, _ = mock_context_file
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                with patch('code2prompt_mcp.main.genai.Client') as mock_client_class:
                    mock_get_context.return_value = context_file_path
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    mock_client.models.generate_content.side_effect = Exception("Network timeout occurred")
                    
                    with pytest.raises(Exception) as exc_info:
                        await ask_gemini_question(question="Test question")
                    
                    assert "Network timeout" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_gemini_generic_error(self, temp_cwd, mock_context_file, valid_api_key):
        """Test handling of generic Gemini API errors."""
        context_file_path, _ = mock_context_file
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                with patch('code2prompt_mcp.main.genai.Client') as mock_client_class:
                    mock_get_context.return_value = context_file_path
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    mock_client.models.generate_content.side_effect = Exception("Unknown API error")
                    
                    with pytest.raises(Exception) as exc_info:
                        await ask_gemini_question(question="Test question")
                    
                    assert "AI service error: Unknown API error" in str(exc_info.value)
    
    # Edge Cases and Special Scenarios
    
    @pytest.mark.asyncio
    async def test_empty_context_file(self, temp_cwd, mock_gemini_response, valid_api_key):
        """Test handling of empty context file."""
        empty_context_file = temp_cwd / "latest_context.txt"
        empty_context_file.write_text("", encoding="utf-8")
        context_file_path = str(empty_context_file.absolute())
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                with patch('code2prompt_mcp.main.genai.Client') as mock_client_class:
                    mock_get_context.return_value = context_file_path
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    mock_client.models.generate_content.return_value = mock_gemini_response
                    
                    result = await ask_gemini_question(question="Test question")
                    
                    # Should still work with empty context
                    assert result['answer'] == "This is a sample AI response to the codebase question."
                    
                    # Verify the prompt sent to Gemini contains the question even with empty context
                    generate_call = mock_client.models.generate_content.call_args
                    assert "Test question" in generate_call[1]['contents']
    
    @pytest.mark.asyncio
    async def test_unicode_question_handling(self, temp_cwd, mock_gemini_response, mock_context_file, valid_api_key):
        """Test handling of Unicode characters in questions."""
        context_file_path, _ = mock_context_file
        unicode_question = "这段代码做什么？ 🤔 What does this émojis code do?"
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                with patch('code2prompt_mcp.main.genai.Client') as mock_client_class:
                    mock_get_context.return_value = context_file_path
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    mock_client.models.generate_content.return_value = mock_gemini_response
                    
                    result = await ask_gemini_question(question=unicode_question)
                    
                    # Verify Unicode question was handled correctly
                    generate_call = mock_client.models.generate_content.call_args
                    assert unicode_question in generate_call[1]['contents']
                    assert result['answer'] == "This is a sample AI response to the codebase question."
    
    @pytest.mark.asyncio
    async def test_long_question_handling(self, temp_cwd, mock_gemini_response, mock_context_file, valid_api_key):
        """Test handling of very long questions."""
        context_file_path, _ = mock_context_file
        long_question = "This is a very long question. " * 100  # ~3000 characters
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                with patch('code2prompt_mcp.main.genai.Client') as mock_client_class:
                    mock_get_context.return_value = context_file_path
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    mock_client.models.generate_content.return_value = mock_gemini_response
                    
                    result = await ask_gemini_question(question=long_question)
                    
                    # Should handle long questions without issues
                    assert result['answer'] == "This is a sample AI response to the codebase question."
                    
                    # Verify the full question was included
                    generate_call = mock_client.models.generate_content.call_args
                    assert long_question in generate_call[1]['contents']
    
    @pytest.mark.asyncio
    async def test_gemini_response_without_text_attribute(self, temp_cwd, mock_context_file, valid_api_key):
        """Test handling when Gemini response doesn't have text attribute."""
        context_file_path, _ = mock_context_file
        
        # Mock response without text attribute
        mock_response_without_text = MagicMock()
        del mock_response_without_text.text  # Remove text attribute
        mock_response_without_text.__str__ = lambda self: "String representation of response"
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                with patch('code2prompt_mcp.main.genai.Client') as mock_client_class:
                    mock_get_context.return_value = context_file_path
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    mock_client.models.generate_content.return_value = mock_response_without_text
                    
                    result = await ask_gemini_question(question="Test question")
                    
                    # Should fallback to string representation
                    assert "String representation of response" in result['answer']
    
    @pytest.mark.asyncio
    async def test_gemini_config_parameters(self, temp_cwd, mock_gemini_response, mock_context_file, valid_api_key):
        """Test that Gemini is configured with correct parameters."""
        context_file_path, _ = mock_context_file
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_api_key}):
            with patch('code2prompt_mcp.main.get_context_for_gemini', new_callable=AsyncMock) as mock_get_context:
                with patch('code2prompt_mcp.main.genai.Client') as mock_client_class:
                    with patch('code2prompt_mcp.main.types.GenerateContentConfig') as mock_config_class:
                            mock_get_context.return_value = context_file_path
                            mock_client = MagicMock()
                            mock_client_class.return_value = mock_client
                            mock_client.models.generate_content.return_value = mock_gemini_response
                            
                            await ask_gemini_question(question="Test question")
                            
                            # Verify GenerateContentConfig was created with correct parameters
                            mock_config_class.assert_called_once_with(
                                temperature=0.1,
                                max_output_tokens=30000
                            )


if __name__ == "__main__":
    pytest.main([__file__])