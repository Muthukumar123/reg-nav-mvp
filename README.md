# Regulation Navigator — Production RAG System

A production-grade Retrieval-Augmented Generation (RAG) system for answering regulatory compliance questions using grounded LLM responses with citations.

This project is an independent exploration into building reliable, enterprise-style AI systems that combine classical information retrieval with modern LLM deployment patterns.

Designed and implemented end-to-end using FastAPI and Azure OpenAI.

---

## 🧠 Why This Project Exists

Most AI demos stop at notebooks or thin wrappers around LLM APIs.

I built this project to explore:
- **Real-world RAG architecture patterns** — beyond toy examples
- **Grounded generation and hallucination control** — production reliability
- **Production-ready API design** — clean contracts, proper error handling
- **Applying enterprise architecture principles to AI systems** — SOLID principles, testability, maintainability

The goal was to build a clean, extensible AI service — not a demo.

---

## 🎯 What This Project Demonstrates

- Production-style RAG system design with retrieval + generation stages
- Grounded LLM deployment patterns using constrained prompting
- Hallucination-aware reasoning strategies and source citation extraction
- Architecture-first AI development using SOLID principles
- Enterprise-ready documentation and structured codebase
- Real regulatory compliance Q&A system (GDPR, AML, PSD2, MiFID II)

---

## 🏗️ System Architecture

### High-Level Flow

```
User Query
    ↓
---------- API LAYER ----------
POST /ask {question, top_k}
    ↓
---------- APPLICATION LAYER ----------
[1] TF-IDF Retrieval Engine
    - Load query text
    - Calculate cosine similarity against indexed chunks
    - Return top_k most relevant chunks with scores
    ↓
[2] LLM Generation (Azure OpenAI)
    - Send retrieved chunks + question to LLM
    - LLM reads context and generates answer
    - Citations extracted from response
    ↓
[3] Response Formatting
    - Structure answer + citations + scores
    - Return JSON response
---------- RESPONSE ----------
{answer, citations[], scores[]}
```

### Core Architecture Principles Applied

**1. Separation of Concerns**
- **API Layer** (`app.py`): FastAPI routes, request validation, response formatting
- **Retrieval Layer**: TF-IDF vectorization and cosine similarity search
- **LLM Layer** (`llm.py`): Azure OpenAI integration, prompt engineering
- **Data Layer** (`data.txt`): Regulatory documents in structured format

**2. Single Responsibility Principle (SRP)**
- `load_chunks()`: Only loads and parses data
- `initialize_retrieval()`: Only builds TF-IDF index
- `call_llm()`: Only handles LLM API calls
- Route handlers: Only handle HTTP request/response

**3. Dependency Injection**
- LLM module imported and used, not hardcoded
- Configuration via environment variables
- Easy to swap implementations

**4. Error Handling Strategy**
- Graceful degradation on LLM failures
- Detailed logging at each layer
- User-friendly error messages in API responses

**5. Performance Optimization**
- Single TF-IDF index built at startup (not per-request)
- Cosine similarity computed efficiently with scikit-learn
- Top-k retrieval limits token context

### Request/Response Contract

**Application Internal Representation:**
```python
# What the application works with internally
chunk = {
    "doc": "Regulation (EU) 2016/679",
    "section": "Article 5",
    "text": "Personal data shall be processed lawfully..."
}

answer = {
    "text": "Full generated answer",
    "sources": ["Article 5", "Article 6"],
    "scores": [0.543, 0.412]
}
```

**API Request Contract (External):**
```json
POST /ask
{
  "question": "What is GDPR?",
  "top_k": 3
}
```

**API Response Contract (External):**
```json
{
  "answer": "GDPR is Regulation (EU) 2016/679 that...\nCitations: Article 5; Article 6",
  "citations": [
    {"doc": "Regulation (EU) 2016/679", "section": "Article 5"},
    {"doc": "Regulation (EU) 2016/679", "section": "Article 6"}
  ],
  "scores": [0.543, 0.412]
}
```

**Key Differences:**
- Application uses internal `chunk` format
- API transforms to `citations` (array of objects)
- LLM generates text, API structures the response
- Scores track semantic relevance, not answer confidence

## 📊 Data Source & Structure

### Where Data Comes From

**Source:** `data.txt` - A static regulatory document corpus prepared manually

**Format:** Plain text with structured headers
```
[DOC] Regulation (EU) 2016/679 | Article 5 - Principles Relating to Processing
Personal data shall be processed lawfully, fairly and in a transparent manner...

[DOC] Regulation (EU) 2016/679 | Article 6 - Lawfulness of Processing
Processing shall be lawful only if and to the extent that at least one of...
```

**Parsing Process:**
1. Read `data.txt` line by line
2. Identify `[DOC]` headers containing document name and section
3. Extract text between headers as chunk content
4. Filter chunks with text length > 30 characters
5. Store as structured dictionaries with `doc`, `section`, and `text` fields

**Storage:** In-memory list of dictionaries (not database)
- Loaded once at application startup
- Indexed with TF-IDF vectorizer
- Remains in memory during application lifetime

### Data Quality & Coverage

**✅ EU Directive 2015/849** - Anti-Money Laundering (20 articles)
- Customer Due Diligence, Beneficial Ownership, Enhanced Monitoring
- Sanctions Screening, Transaction Reporting, FIU Cooperation
- High-risk jurisdictions, Politically Exposed Persons

**✅ Regulation (EU) 2016/679** - GDPR (5 articles)
- Data Protection Principles, Lawfulness of Processing
- Data Subject Rights, Security Requirements

**✅ Directive (EU) 2015/2366** - PSD2 (5 articles)
- Payment Service Authorization, Strong Customer Authentication
- Unauthorised Transaction Liability

**✅ Directive 2014/65/EU** - MiFID II (5 articles)
- Suitability Assessment, Best Execution, Conflicts of Interest

**Statistics:**
- Total Chunks: 35 regulatory articles/sections
- Vocabulary Size: 536 unique terms (after TF-IDF vectorization)
- Average Chunk Length: ~250 words
- Retrieval Index: Built at startup, O(1) scoring per query

## 🧠 LLM Integration & How It Works

### Azure OpenAI Connection

**What the LLM Does:**
1. Takes the user's question + top-k retrieved chunks
2. Reads chunk context to understand regulatory requirements
3. Generates a natural language answer citing the regulations
4. LLM is NOT trained on this data—just reads it as context

**Important:** This is NOT RAG fine-tuning. This is in-context learning:
- No model training or fine-tuning
- LLM acts as a reasoning engine over the provided context
- All answers must be justified by retrieved chunks
- Citations come from the chunks provided

### Generation Process

```
[Question] "What is customer due diligence?"
   ↓
[Retrieval] TF-IDF finds closest chunks
   - AML Directive Article 5 (score: 0.543)
   - GDPR Article 13 (score: 0.412)
   - PSD2 Article 4 (score: 0.298)
   ↓
[LLM Prompt Construction]
System: "You are a regulatory compliance expert..."
Context: "Article 5 text...\nArticle 13 text...\nArticle 4 text..."
User Question: "What is customer due diligence?"
   ↓
[LLM Generation] Azure OpenAI gpt-4-turbo generates response
Model: gpt-4-turbo-preview
Temperature: 0.2 (low randomness, factual)
   ↓
[Response Parsing]
- Extract answer text
- Identify citations from response
- Format as JSON with scores
```

### Configuration

```env
# Environment variables for LLM
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

**LLM Parameters (in `llm.py`):**
- Model Deployment: `gpt-5-mini` (configured in Azure)
- Max Completion Tokens: `1024` (Azure OpenAI API v2)
- Timeout: `20 seconds`

**⚠️ API v2 Compatibility Notes:**
- Uses `openai==2.21.0` (OpenAI Python SDK v2)
- Parameters: `max_completion_tokens` (not `max_tokens`)
- Temperature parameter removed (model uses default for stability)
- Chat completion format: `messages` array with roles

### Recent API Compatibility Updates (February 2026)

The system was updated to support Azure OpenAI API v2 after discovering compatibility issues with the newer OpenAI SDK. Here are the changes:

**Issue:** 
- OpenAI SDK v2.x changed parameter names and removed support for certain settings
- Legacy code used `max_tokens` which is no longer supported
- Temperature parameter not supported for gpt-5-mini model

**Solution:**
1. **Upgraded openai library** from v1.40.6 to v2.21.0
   - Updated in `requirements.txt` for clarity
   - Better Azure OpenAI integration

2. **Fixed API parameters** in all LLM modules:
   - `llm.py` - Core implementation
   - `llm_azure.py` - Alternative Azure OpenAI module
   - `infrastructure/llm_client.py` - Refactored module
   
   Changes applied:
   - ✅ `max_tokens=1024` → `max_completion_tokens=1024`
   - ✅ Removed `temperature=0.2` parameter
   - ✅ Simplified message structure for gpt-5-mini compatibility

3. **Verified working integration:**
   - Client initialization successful
   - Azure OpenAI API requests processed correctly
   - Response parsing works with updated SDK
   - Application fully functional

## 🎓 Bank Use Cases (Verified)

| Query | Primary | Secondary | Score |
|-------|---------|-----------|-------|
| CDD requirements | AML Art. 5 (0.43) | GDPR Art. 13 (0.24) | 0.43 |
| Payment authentication | PSD2 Art. 38 (0.37) | AML Art. 5 (0.22) | 0.37 |
| Investment suitability | MiFID II Art. 25 (0.35) | AML Art. 6 (0.26) | 0.35 |
| Data protection | GDPR Art. 5 (0.30) | PSD2 Art. 4 (0.21) | 0.30 |
| Cross-regulation | AML Art. 5 (0.35) | Multiple directives ranked | ✅ |

## 📋 Prerequisites

- Python 3.12+
- Azure OpenAI account with API access
- Git

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Muthukumar123/reg-nav-mvp.git
cd reg-nav-mvp
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your Azure OpenAI credentials:

```env
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

## 🚦 Running the Application

### Start the Server

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at `http://localhost:8000`

### Verify Installation

```bash
# Test imports
python -c "import app; print('APP_IMPORT_OK')"

# Test package installation
python -c "import fastapi, uvicorn, pydantic, sklearn, openai; print('OK')"

# Check health endpoint
curl http://localhost:8000/health
```

## 📚 API Endpoints

### Root - `GET /`
Returns API information and available endpoints.

**Response:**
```json
{
  "service": "Regulation Navigator MVP",
  "version": "1.0.0",
  "endpoints": {...},
  "status": "running"
}
```

### Health Check - `GET /health`
Check system health and data availability.

**Response:**
```json
{
  "status": "ok",
  "chunks": 35,
  "index_ready": true
}
```

### Ask Question - `POST /ask`
Submit a regulatory question and receive an answer with citations.

**Request Schema:**
```json
{
  "question": "What is customer due diligence?",
  "top_k": 3
}
```

**Request Validation:**
- `question`: String, 5-1000 characters, required
- `top_k`: Integer, 1-10, optional (default: 3)

**Response Schema:**
```json
{
  "answer": "Answer: Customer due diligence measures include verification of identity...\nCitations: Article 5; Article 13",
  "citations": [
    {
      "doc": "EU Directive 2015/849",
      "section": "Article 5 - Customer Due Diligence Measures"
    },
    {
      "doc": "Regulation (EU) 2016/679",
      "section": "Article 13 - Information to be Provided"
    }
  ],
  "scores": [0.543, 0.412, 0.298]
}
```

**Response Fields:**
- `answer`: String containing AI-generated answer + citations (format: text + "\nCitations: source1; source2")
- `citations`: Array of objects with doc name and section reference
- `scores`: Array of cosine similarity scores (0.0-1.0) for each retrieved chunk

**Error Response (400):**
```json
{
  "detail": "Question must be between 5 and 1000 characters"
}
```

**Error Response (500):**
```json
{
  "detail": "Failed to generate answer: [LLM error details]"
}
```

## 📖 Interactive Documentation

Access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🧪 Testing

### Run All Tests

```bash
python -m unittest discover -s tests -v
```

### Run Specific Test Suite

```bash
# Dependency tests
python -m unittest tests.test_dependencies -v

# Application tests
python -m unittest tests.test_app -v
```

### Test Coverage

The test suite includes:
- **Dependency validation** (4 tests): Package imports and versions
- **Data loading** (3 tests): Chunk parsing and initialization
- **Health endpoint** (1 test): Status validation
- **Ask endpoint** (8 tests): Query handling, LLM integration, error cases
- **Retrieval mechanism** (2 tests): TF-IDF similarity scoring

**Total: 18 tests, 100% passing**

## 🧩 Project Structure

```
reg-nav-mvp/
├── app.py                      # Main FastAPI application (288 lines)
│   ├── load_chunks()          # Parse data.txt
│   ├── ChunkRetriever class   # TF-IDF vectorization & cosine similarity
│   ├── /health endpoint       # Status check
│   └── /ask endpoint          # Main Q&A route
├── llm.py                      # Azure OpenAI integration (158 lines)
│   ├── _get_client()          # Lazy Azure OpenAI client init
│   └── call_llm()             # LLM API call with context
├── data.txt                    # Regulatory documents source (35 chunks)
│   └── Format: [DOC] Name | Section / Text content...
├── requirements.txt            # Dependencies
├── .env                        # Credentials (gitignored)
├── .env.example               # Template
├── .gitignore                 # Don't commit .env, __pycache__/
├── demo_logging.py            # Logging examples
├── LOGGING.md                 # Logging guide
├── README.md                  # This file
└── tests/
    ├── test_dependencies.py   # Import verification
    └── test_app.py           # Integration tests
```

## 🔧 Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Web Framework | FastAPI | 0.115.0 | HTTP API, automatic documentation |
| ASGI Server | Uvicorn | 0.30.6 | Production-grade async server |
| Data Validation | Pydantic | 2.8.2 | Request/response schema validation |
| ML/Retrieval | scikit-learn | 1.5.1 | TF-IDF vectorization, cosine similarity |
| LLM SDK | OpenAI | 1.40.6 | Azure OpenAI API client |
| Environment | python-dotenv | (latest) | .env file loading |

## 📊 Logging and Monitoring

The application includes comprehensive logging at multiple levels:

- **INFO**: Normal operations, API calls, initialization
- **DEBUG**: Detailed tracing, similarity scores, token usage
- **ERROR**: Request failures, LLM errors
- **CRITICAL**: System initialization failures

### View Logs

```bash
# Run with detailed logging
python demo_logging.py
```

See [LOGGING.md](LOGGING.md) for complete logging documentation.

## 🔒 Security

- **Environment Variables**: All sensitive credentials stored in `.env` (gitignored)
- **Input Validation**: Pydantic models validate all API inputs
- **Error Handling**: Graceful error responses without exposing internals
- **Source Control**: No credentials in version control

## 📝 Usage Examples

### Using cURL

```bash
# Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is customer due diligence?",
    "top_k": 2
  }'
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/ask",
    json={
        "question": "What is enhanced due diligence?",
        "top_k": 3
    }
)

result = response.json()
print(result["answer"])
print("Citations:", result["citations"])
```

### Using Swagger UI

1. Open http://localhost:8000/docs
2. Click on `POST /ask` endpoint
3. Click "Try it out"
4. Enter your question
5. Click "Execute"

## 🐛 Troubleshooting

### Issue: "Missing environment variables" error

**Solution**: Ensure `.env` file exists with all required variables:
```bash
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_KEY=...
AZURE_OPENAI_DEPLOYMENT=...
```

### Issue: "NOT FOUND IN SOURCES" response

**Solution**: The query may be too irrelevant to the regulatory documents. Try:
- Reformulating the question to include regulatory terms
- Checking that `data.txt` contains relevant information

### Issue: 502 Bad Gateway on /ask

**Solution**: LLM service error. Check:
- Azure OpenAI credentials are correct
- Deployment name matches your Azure configuration
- Azure OpenAI service is accessible

### Issue: Import errors

**Solution**: Reinstall dependencies:
```bash
pip install -r requirements.txt --upgrade
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is part of a regulatory compliance MVP demonstration.

## � Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
- Retrieval using [scikit-learn](https://scikit-learn.org/)

---

## 💡 Lessons Learned

- **Retrieval quality dominates answer quality** — a perfect LLM with poor retrieval yields poor answers
- **Deterministic prompting significantly reduces hallucinations** — constraints matter more than sophistication
- **Clear architectural separation simplifies future upgrades** — loosely coupled components enable rapid iteration
- **Documentation-first development improves system clarity** — architecture is a design tool, not an afterthought
- **Citation extraction requires explicit prompt engineering** — LLMs need clear instructions to stay grounded

---

## 🚀 Future Improvements

- **Hybrid search** — BM25 + semantic embeddings for better retrieval
- **Retrieval evaluation framework** — automated metrics for retrieval quality
- **LLM output evaluation** — faithfulness scoring and grounding verification
- **Caching and latency optimization** — Redis caching for frequent queries
- **Multi-language support** — queries and regulations in multiple languages
- **Compliance audit tooling** — trace regulatory decisions back to source articles

---

## 👤 Author

Built by an enterprise architect exploring applied AI systems and modern LLM infrastructure, with a focus on reliability, clarity, and real-world deployment patterns.

**Interests:**
- Production-grade AI systems
- RAG architecture and deployment patterns
- Enterprise software design principles applied to AI
- Regulatory technology and compliance automation

**GitHub:** [@Muthukumar123](https://github.com/Muthukumar123)  
**Repository:** [reg-nav-mvp](https://github.com/Muthukumar123/reg-nav-mvp)

---

**Status**: ✅ Production Ready | **Last Updated**: February 16, 2026