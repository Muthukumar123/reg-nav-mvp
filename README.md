# Regulation Navigator MVP

A FastAPI-based Retrieval-Augmented Generation (RAG) application for answering regulatory compliance questions using Azure OpenAI. The system retrieves relevant regulatory text chunks and provides precise, citation-backed answers.

## 🎯 Current Status: Enterprise Bank-Ready MVP

- ✅ **Phase 1 Complete:** Retrieval quality improvements & strict refusal behavior implemented
- ✅ **Phase 2 Complete:** Real EU Directive 2015/849 integrated (20 articles)
- ✅ **Phase 3 Complete:** Multi-Directive expansion (GDPR, PSD2, MiFID II)
- ✅ **Enterprise Coverage:** 35 articles, 536 vocabulary terms, 4 major EU regulations
- ✅ **Production Deployment:** Ready for bank pitch and compliance team demos

## 📊 Integrated Regulations (35 articles, 536 vocabulary terms)

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
  "chunks": 3,
  "index_ready": true
}
```

### Ask Question - `POST /ask`
Submit a regulatory question and receive an answer with citations.

**Request:**
```json
{
  "question": "What is customer due diligence?",
  "top_k": 3
}
```

**Response:**
```json
{
  "answer": "Answer: Customer due diligence measures include...\nCitations: AMLD_EXCERPT (Article 13)",
  "citations": [
    {"doc": "AMLD_EXCERPT", "section": "Article 13"}
  ],
  "scores": [0.5001]
}
```

**Parameters:**
- `question` (required): The regulatory question to answer
- `top_k` (optional, default=3): Number of source chunks to retrieve

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
├── app.py                  # Main FastAPI application
├── llm.py                  # Azure OpenAI client and LLM calls
├── data.txt                # Regulatory document chunks
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── .env.example           # Environment template
├── .gitignore             # Git ignore rules
├── demo_logging.py        # Logging demonstration script
├── LOGGING.md             # Logging documentation
├── README.md              # This file
└── tests/
    ├── test_dependencies.py  # Dependency smoke tests
    └── test_app.py           # Application tests
```

## 🔧 Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Web Framework | FastAPI | 0.115.0 |
| ASGI Server | Uvicorn | 0.30.6 |
| Data Validation | Pydantic | 2.8.2 |
| ML/Retrieval | scikit-learn | 1.5.1 |
| LLM Integration | OpenAI SDK | 1.40.6 |
| Environment | python-dotenv | (latest) |

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

## 👤 Author

**Muthukumar123**

- GitHub: [@Muthukumar123](https://github.com/Muthukumar123)
- Repository: [reg-nav-mvp](https://github.com/Muthukumar123/reg-nav-mvp)

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
- Retrieval using [scikit-learn](https://scikit-learn.org/)

---

**Status**: ✅ Production Ready | **Last Updated**: February 14, 2026