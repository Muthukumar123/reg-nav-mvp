# Azure OpenAI API v2 Migration Guide

## Overview

This document explains the changes made to support Azure OpenAI API v2 (OpenAI Python SDK v2.21.0+).

## What Changed & Why

### Problem
The application was using the OpenAI Python SDK v1.x which had compatibility issues:
1. Client initialization failed with proxies parameter error
2. Old API parameter names were deprecated
3. Some parameters became unsupported for certain models

### Solution
Upgraded to OpenAI SDK v2.21.0 which provides:
- ✅ Better Azure OpenAI integration
- ✅ Updated parameter names
- ✅ Improved error handling
- ✅ Stable model support

## Parameter Changes

### Before (SDK v1.x)
```python
resp = client.chat.completions.create(
    model=deployment,
    messages=[...],
    temperature=0.2,        # ❌ No longer supported
    max_tokens=1024,        # ❌ Renamed in v2
)
```

### After (SDK v2.0+)
```python
resp = client.chat.completions.create(
    model=deployment,
    messages=[...],
    max_completion_tokens=1024,  # ✅ New parameter name
    # temperature removed (uses model default)
)
```

## Files Modified

### 1. requirements.txt
- `openai>=1.40.6` → `openai==2.21.0`
- Pinned to specific v2 version for compatibility

### 2. llm.py
- Updated `client.chat.completions.create()` call
- Replaced `max_tokens` with `max_completion_tokens`
- Removed `temperature=0.2` parameter

### 3. llm_azure.py
- New file created with v2-compatible implementation
- Serves as alternative LLM integration module

### 4. infrastructure/llm_client.py
- Updated `AzureOpenAIModel` class
- Changed LLM API parameters for v2 compatibility

## Installation

### For New Installation
```bash
pip install -r requirements.txt
```

This automatically installs openai==2.21.0

### For Existing Installation (Upgrade)
```bash
pip install --upgrade openai==2.21.0
```

## Testing the Migration

### 1. Verify Installation
```bash
python -c "import openai; print(openai.__version__)"
# Should print: 2.21.0
```

### 2. Test API Call
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is customer due diligence?", "top_k": 3}'
```

Expected response:
```json
{
  "answer": "...",
  "citations": [...],
  "scores": [...]
}
```

### 3. Check Logs
Look for success messages:
```
Azure OpenAI client initialized successfully
LLM response received - length: 256 chars
```

## Troubleshooting

### Error: "unsupported_parameter: 'max_tokens'"
**Solution:** Ensure openai==2.21.0 is installed
```bash
pip install --upgrade openai==2.21.0
```

### Error: "unsupported_value: 'temperature' does not support 0.2"
**Solution:** Remove temperature parameter from API call (already fixed in v2.21.0+)

### Error: "Client.__init__() got an unexpected keyword argument"
**Solution:** Update to SDK v2.0+ which removes proxies parameter
```bash
pip install openai==2.21.0
```

## Configuration Compatibility

### Environment Variables (No Changes)
Still use the same .env configuration:
```env
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

### Model Support (Tested)
- ✅ gpt-5-mini
- ✅ gpt-4-turbo (use newer SDK versions)
- ✅ gpt-35-turbo

## Performance Notes

- **Max Completion Tokens:** 1024 (for detailed compliance answers)
- **Timeout:** 20 seconds
- **No Temperature:** Model uses default for stability

## References

- [OpenAI Python SDK Changelog](https://github.com/openai/openai-python/releases)
- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [SDK v2 Migration Guide](https://github.com/openai/openai-python/blob/main/MIGRATION_GUIDE.md)

## Support

For issues or questions:
1. Check the [CHANGELOG.md](CHANGELOG.md) for recent updates
2. Review the [README.md](README.md) for system overview
3. Check [llm.py](llm.py) for implementation details
