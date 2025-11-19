# Adding New Gemini Models

This guide explains how to add support for new Google Gemini AI models to the code2prompt MCP server.

## Quick Start

Follow these steps to add a new model:

1. **Test the model** - Verify it works with the Google API
2. **Update the code** - Add to supported models list
3. **Update documentation** - Update parameter docs
4. **Run tests** - Ensure everything works
5. **Commit changes** - Document what model was added

---

## Step-by-Step Guide

### Step 1: Test the New Model

Before adding a model to the codebase, verify it works with Google's API.

#### 1.1 Find the Model Identifier

Check Google's documentation for the exact model identifier:
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Google AI Studio](https://aistudio.google.com/)

Common patterns:
- Preview models: `gemini-X-pro-preview` or `gemini-X-flash-preview`
- Dated versions: `gemini-X-pro-preview-MM-YYYY`
- Stable releases: `gemini-X-pro`

#### 1.2 Run the Model Test Script

Use the provided test script to verify the model works:

```bash
# Edit tests/test_gemini_models.py
# Add your model to the test_new_model_example() function:

new_models = [
    ("gemini-4-pro-preview", 3000),  # (model_name, max_tokens)
]

# Run the test
poetry run python tests/test_gemini_models.py
```

**Important considerations:**
- **Token limits**: Newer models with reasoning capabilities need higher `max_tokens`
  - Gemini 3+: Use 2000-3000 tokens minimum
  - Gemini 2.x: 500-1000 tokens usually sufficient
- **Thinking tokens**: Models with enhanced reasoning use tokens for internal "thinking" before generating output
- **Response structure**: Verify the model returns text in the expected format

#### 1.3 Analyze the Test Results

The test will show:
- ✓ Whether the model responds successfully
- Token usage breakdown (prompt, output, thinking)
- Whether the model uses enhanced reasoning
- Any errors or warnings

**Example output:**
```
🧪 Testing model: gemini-4-pro-preview
   Max tokens: 3000
   ✓ gemini-4-pro-preview works!
   Response: Hello from Gemini! I am Gemini 4 Pro...
   Token usage: 1234 total (16 prompt, 20 output, 1198 thinking)
   ⚡ Model uses enhanced reasoning (thinking tokens)
```

### Step 2: Update the Code

#### 2.1 Add to Supported Models List

Edit `src/code2prompt_mcp/main.py`:

```python
# Find this section (around line 293):
# Step 1: Validate model selection
supported_models = ["gemini-3-pro-preview"]  # Add your model here
```

**Add your model to the list:**

```python
supported_models = [
    "gemini-3-pro-preview",
    "gemini-4-pro-preview",  # <- Your new model
]
```

#### 2.2 Update the Default Model (Optional)

If you want the new model to be the default:

```python
# Find the function signature (around line 228):
async def ask_gemini_question(
    question: str,
    path: str = ".",
    model: str = "gemini-3-pro-preview",  # <- Change this
    # ...
```

**Change to:**

```python
    model: str = "gemini-4-pro-preview",  # <- New default
```

#### 2.3 Update the Documentation String

Update the parameter documentation in the same function:

```python
# Find this section (around line 271):
Args:
    question: The natural language question to ask about the codebase (required)
    path: Path to the codebase
    model: Gemini model to use (gemini-3-pro-preview, default: gemini-3-pro-preview)
```

**Update to:**

```python
    model: Gemini model to use (gemini-3-pro-preview, gemini-4-pro-preview, default: gemini-4-pro-preview)
```

### Step 3: Update the Test Suite

#### 3.1 Add to Current Models Test

Edit `tests/test_gemini_models.py`:

```python
def test_currently_supported_models():
    """Test the models currently supported by the MCP server"""
    tester = GeminiModelTester()

    # Update this list to match supported_models in main.py
    current_models = [
        ("gemini-3-pro-preview", 2000),
        ("gemini-4-pro-preview", 3000),  # <- Add your model
    ]
```

**Important**: The models in this test should exactly match the `supported_models` list in `main.py`.

### Step 4: Run Tests

Run the full test suite to verify everything works:

```bash
# Run all tests
poetry run pytest tests/test_gemini_models.py -v

# Or run the test script directly
poetry run python tests/test_gemini_models.py
```

**Expected output:**
```
✓ Successful: 2/2
  - gemini-3-pro-preview
  - gemini-4-pro-preview

✅ All currently supported models passed!
```

### Step 5: Commit Your Changes

Document your changes with a clear commit message:

```bash
git add src/code2prompt_mcp/main.py tests/test_gemini_models.py
git commit -m "Add support for Gemini 4 Pro Preview model

- Added gemini-4-pro-preview to supported models
- Updated default model to gemini-4-pro-preview
- Updated tests to verify new model
- Tested with max_tokens=3000 for enhanced reasoning"
```

---

## Model Configuration Guidelines

### Token Limits

Different model generations require different token allocations:

| Model Generation | Recommended max_tokens | Reason |
|-----------------|----------------------|---------|
| Gemini 3.x+ | 2000-3000 | Enhanced reasoning requires thinking tokens |
| Gemini 2.x | 500-1000 | Standard generation, less thinking overhead |
| Future models | Start with 3000+ | Likely to have more advanced reasoning |

**How to determine the right limit:**
1. Run the test script with a high limit (e.g., 5000)
2. Check the token usage output
3. Set limit to: `thinking_tokens + output_tokens + 20% buffer`

### Model Naming Patterns

Google typically uses these naming patterns:

- **Preview models**: `gemini-X-pro-preview` (latest features, may change)
- **Dated previews**: `gemini-X-pro-preview-MM-YYYY` (pinned version)
- **Stable models**: `gemini-X-pro` (production-ready)
- **Flash variants**: `gemini-X-flash` (faster, lighter)

**Recommendation**: Support preview models first, migrate to stable when available.

### Response Structure

All supported models should return responses with this structure:

```python
response.text  # Main text output (preferred access method)
response.candidates[0].content.parts[0].text  # Fallback method
response.usage_metadata  # Token usage information
response.candidates[0].finish_reason  # Completion status
```

New models may include additional fields:
- `thought_signature` - Reasoning trace (Gemini 3+)
- `grounding_metadata` - Search grounding info
- `citation_metadata` - Citation information

---

## Troubleshooting

### Model Returns Empty Response

**Symptom**: Test passes but `response_text` is None

**Common causes:**
1. **Insufficient tokens**: Thinking tokens exceed max_tokens
   - **Solution**: Increase `max_tokens` in test
2. **Model not fully released**: Preview model still in rollout
   - **Solution**: Wait for full availability or contact Google
3. **API version mismatch**: Model requires newer API version
   - **Solution**: Update `google-genai` package

### Model Not Found (404 Error)

**Symptom**: `404 NOT_FOUND` error from Google API

**Common causes:**
1. **Incorrect model name**: Typo or wrong format
   - **Solution**: Verify exact name in Google's documentation
2. **Model not available yet**: Announced but not released
   - **Solution**: Monitor Google AI updates
3. **API version incompatibility**: Model requires different API
   - **Solution**: Check API version requirements

### Authentication Errors

**Symptom**: API key errors or authentication failures

**Common causes:**
1. **Missing API key**: GEMINI_API_KEY not set
   - **Solution**: Set in `.env` file
2. **Invalid API key**: Key expired or incorrect
   - **Solution**: Generate new key at [Google AI Studio](https://aistudio.google.com/)
3. **Permissions**: Model requires special access
   - **Solution**: Request access through Google AI

### Rate Limits

**Symptom**: Quota or rate limit errors

**Common causes:**
1. **Too many requests**: Testing too frequently
   - **Solution**: Wait 60 seconds between test runs
2. **Quota exceeded**: Daily/monthly limit reached
   - **Solution**: Wait for quota reset or upgrade plan

---

## Example: Adding Gemini 4 Pro

Here's a complete example of adding a hypothetical "Gemini 4 Pro" model:

### 1. Test the model

```bash
# Edit tests/test_gemini_models.py
new_models = [
    ("gemini-4-pro-preview", 3000),
]

# Run test
poetry run python tests/test_gemini_models.py
```

### 2. Update main.py

```python
# Line 293: Add to supported models
supported_models = [
    "gemini-3-pro-preview",
    "gemini-4-pro-preview",
]

# Line 231: Update default (optional)
model: str = "gemini-4-pro-preview",

# Line 271: Update docs
model: Gemini model to use (gemini-3-pro-preview, gemini-4-pro-preview, default: gemini-4-pro-preview)
```

### 3. Update tests

```python
# tests/test_gemini_models.py
current_models = [
    ("gemini-3-pro-preview", 2000),
    ("gemini-4-pro-preview", 3000),
]
```

### 4. Verify

```bash
poetry run pytest tests/test_gemini_models.py -v
```

### 5. Commit

```bash
git add src/code2prompt_mcp/main.py tests/test_gemini_models.py
git commit -m "Add Gemini 4 Pro Preview support"
```

---

## Checklist

Use this checklist when adding a new model:

- [ ] Find exact model identifier from Google documentation
- [ ] Add model to `test_new_model_example()` in test file
- [ ] Run test and verify successful response
- [ ] Note token usage (especially thinking tokens)
- [ ] Add to `supported_models` list in `main.py`
- [ ] Update default model in function signature (if desired)
- [ ] Update model parameter documentation string
- [ ] Add to `test_currently_supported_models()` in test file
- [ ] Run full test suite and verify all tests pass
- [ ] Commit changes with descriptive message
- [ ] Update main README.md if default model changed

---

## Resources

- [Google Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Google AI Studio](https://aistudio.google.com/) - Get API keys and test models
- [google-genai Python SDK](https://github.com/googleapis/python-genai) - SDK source code
- [Model Updates Blog](https://blog.google/products/gemini/) - Latest model announcements

---

## Questions?

If you encounter issues not covered in this guide:

1. Check the test output for specific error messages
2. Review Google's API documentation for the specific model
3. Verify your `google-genai` package is up to date: `poetry update google-genai`
4. Check Google's status page for API availability

For issues with the MCP server itself (not Google's API), open an issue in the repository.
