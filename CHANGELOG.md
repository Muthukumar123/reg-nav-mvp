# Changelog

All notable changes to the Regulation Navigator MVP are documented here.

## [1.0.0] - 2026-02-15

### 🔧 Fixed
- **Azure OpenAI API v2 Compatibility** (Critical Fix)
  - Upgraded `openai` library from v1.40.6 to v2.21.0
  - Fixed client initialization error: `Client.__init__() got an unexpected keyword argument 'proxies'`
  - Updated deprecated API parameters to match OpenAI SDK v2 spec
  - Replaced `max_tokens` with `max_completion_tokens` parameter
  - Removed unsupported `temperature` parameter for gpt-5-mini model

### 📝 Changed
- **requirements.txt**: Pinned `openai==2.21.0` for API v2 compatibility
- **llm.py**: Updated Azure OpenAI client initialization and API call parameters
- **llm_azure.py**: Added alternative Azure OpenAI integration with v2 compatibility
- **infrastructure/llm_client.py**: Updated LLM client to use v2 API parameters

### ✅ Verified
- Azure OpenAI client initializes successfully without proxies error
- LLM API calls use correct parameter names (max_completion_tokens)
- Application generates compliance answers with proper citations
- Backend (FastAPI) and Frontend (Next.js) both running successfully
- API endpoint `/ask` returns proper JSON responses with answers, citations, and relevance scores

### 📋 Release Status
- ✅ Full system operational
- ✅ Backend API responding to requests
- ✅ Frontend UI accessible
- ✅ Documentation updated with API v2 notes
- ✅ Code committed to main branch

## Key Files Updated

| File | Changes |
|------|---------|
| `requirements.txt` | openai 1.40.6 → 2.21.0 |
| `llm.py` | max_tokens → max_completion_tokens, removed temperature |
| `llm_azure.py` | Created with v2 compatibility |
| `infrastructure/llm_client.py` | Updated parameters for v2 API |
| `README.md` | Added API v2 compatibility section |

## Installation & Upgrade

If upgrading from a previous version:

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Restart the application
# The application will automatically use the updated API client
```

No action needed if installing fresh - all dependencies are pre-configured.

## Known Limitations

None at this time. All features are operational.

## Next Steps

- Monitor API usage and optimize token consumption
- Consider implementing response caching for frequently asked questions
- Collect user feedback on answer quality and citation accuracy
- Plan integration with additional regulatory documents

---

For more information, see:
- [README.md](README.md) - System overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed architecture documentation
- [llm.py](llm.py) - LLM integration implementation
