# Logging and Exception Handling Reference

## Overview
The application now includes comprehensive logging, tracing, and exception handling throughout all modules.

## Logging Configuration

### Log Levels Used
- **INFO**: Normal operations, API calls, initialization
- **DEBUG**: Detailed information (query transformations, token usage, retrieved chunks)
- **WARNING**: Unexpected situations that don't prevent operation
- **ERROR**: Errors that affect specific requests
- **CRITICAL**: System-level failures (missing data, failed initialization)

### Log Format
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## Key Logging Points

### Application Startup (app.py)
- ✅ Data loading from file
- ✅ Number of chunks loaded
- ✅ TF-IDF index initialization
- ✅ Matrix shape and dimensions

### Health Endpoint
- ✅ Health check requests
- ✅ System status validation

### Ask Endpoint
- ✅ Incoming question (first 100 chars)
- ✅ Request parameters (top_k)
- ✅ Best similarity score
- ✅ Retrieved chunks with scores
- ✅ LLM call status
- ✅ Response generation

### LLM Module (llm.py)
- ✅ Client initialization
- ✅ Environment variable validation
- ✅ API call details (question/sources length)
- ✅ Token usage statistics
- ✅ Response length

## Exception Handling

### Input Validation
- **Empty question**: Raises ValueError
- **Empty sources**: Raises ValueError
- **Missing required fields**: Returns 422 (FastAPI validation)

### Service Initialization Errors
- **Missing data file**: Logs critical error, raises FileNotFoundError
- **Failed index build**: Logs critical error, returns empty structures
- **Missing env variables**: Raises ValueError with specific missing vars

### Runtime Errors
- **No data chunks**: Returns 503 Service Unavailable
- **Index not ready**: Returns 503 Service Unavailable
- **LLM API failure**: Returns 502 Bad Gateway with error details
- **Unexpected errors**: Returns 500 Internal Server Error with traceback

### HTTP Status Codes
- `200`: Success
- `422`: Validation error (missing/invalid fields)
- `500`: Internal server error
- `502`: LLM service error (Azure OpenAI issues)
- `503`: Service not initialized

## Debugging Tips

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### View Token Usage
Debug logs include:
- Prompt tokens
- Completion tokens
- Total tokens

### View Retrieved Chunks
Debug logs show:
- Document name
- Section
- Similarity score

## Monitored Metrics

The logs capture:
1. **Request volume**: Every `/ask` request is logged
2. **Query relevance**: Similarity scores for threshold monitoring
3. **LLM performance**: Response times and token usage
4. **Error rates**: All exceptions are logged with context
5. **System health**: Initialization status and data availability

## Example Log Output

```
2026-02-14 18:42:11,691 - app - INFO - Loading chunks from data.txt
2026-02-14 18:42:11,691 - app - INFO - Loaded 3 chunks from data.txt
2026-02-14 18:42:11,691 - app - INFO - Initialized with 3 document chunks
2026-02-14 18:42:11,693 - app - INFO - Built TF-IDF index with shape (3, 32)
2026-02-14 18:42:41,201 - app - INFO - Processing question: What is customer due diligence?...
2026-02-14 18:42:41,202 - app - INFO - Best similarity score: 0.5001
2026-02-14 18:42:41,202 - app - INFO - Calling LLM with 2 source chunks
2026-02-14 18:42:41,202 - app - INFO - LLM call successful
```

## Testing

Run the demo script to see logging in action:
```bash
python demo_logging.py
```

All tests pass with logging enabled:
```bash
python -m unittest discover -s tests -v
```
