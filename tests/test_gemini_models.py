"""
Test suite for Gemini model integration

This script tests the integration of Gemini AI models with the code2prompt MCP server.
Run this test when adding new Gemini models to verify they work correctly.

Usage:
    poetry run pytest tests/test_gemini_models.py -v

    Or run directly:
    poetry run python tests/test_gemini_models.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class GeminiModelTester:
    """Test Gemini models for compatibility with the MCP server"""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None

    def validate_environment(self) -> bool:
        """Validate that the environment is set up correctly"""
        if not self.api_key:
            print("❌ GEMINI_API_KEY not found in environment")
            print("   Please set it in .env file or environment variables")
            return False

        print("✓ API key found")

        try:
            self.client = genai.Client(api_key=self.api_key)
            print("✓ Google AI client initialized")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize client: {e}")
            return False

    def test_model(self, model_name: str, max_tokens: int = 2000) -> dict:
        """
        Test a single Gemini model

        Args:
            model_name: The model identifier (e.g., "gemini-3-pro-preview")
            max_tokens: Maximum tokens to allow (Gemini 3+ needs more for thinking)

        Returns:
            Dictionary with test results
        """
        print(f"\n🧪 Testing model: {model_name}")
        print(f"   Max tokens: {max_tokens}")

        result = {
            "model": model_name,
            "success": False,
            "error": None,
            "response_text": None,
            "token_usage": None,
            "has_thinking": False,
            "finish_reason": None
        }

        try:
            # Make a simple test request
            response = self.client.models.generate_content(
                model=model_name,
                contents="Say 'Hello from Gemini!' and tell me which model version you are.",
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=max_tokens
                )
            )

            # Extract response text
            answer = None
            if hasattr(response, 'text') and response.text:
                answer = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    content = candidate.content
                    if hasattr(content, 'parts') and content.parts:
                        if len(content.parts) > 0:
                            answer = content.parts[0].text

            # Extract metadata
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                result["token_usage"] = {
                    "prompt_tokens": getattr(usage, 'prompt_token_count', 0),
                    "output_tokens": getattr(usage, 'candidates_token_count', 0),
                    "thinking_tokens": getattr(usage, 'thoughts_token_count', 0),
                    "total_tokens": getattr(usage, 'total_token_count', 0)
                }

                # Check if model uses thinking tokens
                if getattr(usage, 'thoughts_token_count', 0) > 0:
                    result["has_thinking"] = True

            # Get finish reason
            if hasattr(response, 'candidates') and response.candidates:
                finish_reason = response.candidates[0].finish_reason
                result["finish_reason"] = str(finish_reason)

            if answer:
                result["success"] = True
                result["response_text"] = answer
                print(f"   ✓ {model_name} works!")
                print(f"   Response: {answer[:100]}...")

                if result["token_usage"]:
                    usage = result["token_usage"]
                    print(f"   Token usage: {usage['total_tokens']} total " +
                          f"({usage['prompt_tokens']} prompt, " +
                          f"{usage['output_tokens']} output, " +
                          f"{usage['thinking_tokens']} thinking)")

                if result["has_thinking"]:
                    print(f"   ⚡ Model uses enhanced reasoning (thinking tokens)")

                if result["finish_reason"] != "FinishReason.STOP":
                    print(f"   ⚠️  Finish reason: {result['finish_reason']}")
                    if "MAX_TOKENS" in result["finish_reason"]:
                        print(f"   💡 Consider increasing max_tokens for this model")
            else:
                result["error"] = "No text in response"
                print(f"   ❌ {model_name} returned no text")
                print(f"   Finish reason: {result['finish_reason']}")

        except Exception as e:
            result["error"] = str(e)
            error_msg = str(e)[:200]
            print(f"   ❌ {model_name} failed: {error_msg}")

            # Provide helpful error messages
            if "404" in error_msg or "not found" in error_msg.lower():
                print(f"   💡 Model not available. Check the model name or API version.")
            elif "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                print(f"   💡 Authentication issue. Check your GEMINI_API_KEY.")
            elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                print(f"   💡 Rate limit or quota exceeded. Wait before testing again.")

        return result

    def run_tests(self, models_to_test: list) -> dict:
        """
        Run tests for multiple models

        Args:
            models_to_test: List of tuples (model_name, max_tokens)

        Returns:
            Dictionary of results keyed by model name
        """
        if not self.validate_environment():
            return {}

        results = {}

        print("\n" + "=" * 70)
        print("GEMINI MODEL INTEGRATION TESTS")
        print("=" * 70)

        for model_config in models_to_test:
            if isinstance(model_config, tuple):
                model_name, max_tokens = model_config
            else:
                model_name = model_config
                # Default to higher tokens for Gemini 3+ models
                max_tokens = 2000 if "gemini-3" in model_name or "gemini-4" in model_name else 500

            results[model_name] = self.test_model(model_name, max_tokens)

        # Print summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        successful = [m for m, r in results.items() if r["success"]]
        failed = [m for m, r in results.items() if not r["success"]]

        print(f"\n✓ Successful: {len(successful)}/{len(results)}")
        for model in successful:
            print(f"  - {model}")

        if failed:
            print(f"\n❌ Failed: {len(failed)}/{len(results)}")
            for model in failed:
                error = results[model]["error"]
                print(f"  - {model}: {error[:100]}")

        print("\n" + "=" * 70)

        return results


def test_currently_supported_models():
    """Test the models currently supported by the MCP server"""
    tester = GeminiModelTester()

    # These should match the models in main.py's supported_models list
    current_models = [
        ("gemini-3-pro-preview", 2000),
    ]

    results = tester.run_tests(current_models)

    # Assert all current models work
    for model_name, result in results.items():
        assert result["success"], f"Supported model {model_name} failed: {result['error']}"


def test_new_model_example():
    """
    Example test for adding a new model

    To add a new model:
    1. Add it to the list below
    2. Run this test to verify it works
    3. If successful, add to main.py's supported_models list
    4. Update the default model if desired
    """
    tester = GeminiModelTester()

    # Example: Testing potential future models
    # Uncomment and modify to test new models
    new_models = [
        # ("gemini-4-pro-preview", 3000),  # Example future model
        # ("gemini-3-flash-preview", 2000),  # Example faster variant
    ]

    if not new_models:
        print("\nℹ️  No new models to test. Modify test_new_model_example() to add models.")
        return

    results = tester.run_tests(new_models)
    return results


if __name__ == "__main__":
    print("Running Gemini model integration tests...\n")

    # Run current model tests
    try:
        test_currently_supported_models()
        print("\n✅ All currently supported models passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

    # Run new model tests (if any)
    test_new_model_example()
