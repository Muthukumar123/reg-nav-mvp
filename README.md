# EU Banking Regulator LLM System

A comprehensive LLM-powered system for navigating and querying EU banking regulations. This MVP provides regulatory compliance checking, intelligent Q&A, and document management capabilities for banking institutions and regulators.

## 🎯 Features

- **Intelligent Regulatory Q&A**: Ask questions about EU banking regulations and get accurate, referenced answers
- **Compliance Checking**: Analyze business scenarios for regulatory compliance
- **RAG (Retrieval-Augmented Generation)**: Combines vector search with LLM generation for accurate, contextual responses
- **Multi-Regulation Support**: Covers CRR, CRD, MiFID II, GDPR, AML, PSD2, BRRD, and more
- **Document Ingestion**: Import and index regulatory documents (PDF, DOCX, TXT)
- **RESTful API**: FastAPI-based API for easy integration
- **Multiple LLM Providers**: Support for OpenAI and Anthropic Claude

## 🏗️ Architecture

```
┌─────────────────┐
│   FastAPI API   │
└────────┬────────┘
         │
    ┌────▼─────┐
    │   RAG    │
    │ Service  │
    └──┬────┬──┘
       │    │
   ┌───▼─┐ ┌▼────────┐
   │ LLM │ │ Vector  │
   │     │ │   DB    │
   └─────┘ └─────────┘
```

## 📋 Prerequisites

- Python 3.9+
- OpenAI API key OR Anthropic API key
- 4GB+ RAM (for embedding models)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/Muthukumar123/reg-nav-mvp.git
cd reg-nav-mvp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# Required: Either OPENAI_API_KEY or ANTHROPIC_API_KEY
```

Example `.env` configuration:
```bash
OPENAI_API_KEY=sk-your-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.3
```

### 3. Seed Database

Load sample EU banking regulations:

```bash
python -m src.utils.seed_data
```

### 4. Start the API

```bash
python -m src.api.main
```

The API will be available at `http://localhost:8000`

## 📚 Usage

### Interactive CLI

```bash
# Interactive query mode
python cli.py query

# Compliance checking mode
python cli.py compliance
```

### Run Examples

```bash
python examples.py
```

### API Endpoints

#### Query Regulations
```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the minimum capital requirements for EU banks?",
    "regulation_types": ["Capital Requirements Regulation"],
    "include_references": true,
    "max_results": 5
  }'
```

#### Check Compliance
```bash
curl -X POST "http://localhost:8000/api/compliance/check" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "We want to process customer data for marketing purposes",
    "regulation_types": ["General Data Protection Regulation"],
    "detailed_analysis": true
  }'
```

#### Ingest Document
```bash
curl -X POST "http://localhost:8000/api/documents/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "./data/regulatory_docs/document.pdf",
    "regulation_type": "Capital Requirements Regulation",
    "title": "CRR Article 123",
    "metadata": {"article": "123"}
  }'
```

#### Get System Stats
```bash
curl "http://localhost:8000/api/documents/stats"
```

## 📖 Supported Regulations

- **CRR** - Capital Requirements Regulation
- **CRD** - Capital Requirements Directive  
- **MiFID II** - Markets in Financial Instruments Directive
- **GDPR** - General Data Protection Regulation
- **AML** - Anti-Money Laundering Directive
- **PSD2** - Payment Services Directive 2
- **EMIR** - European Market Infrastructure Regulation
- **BRRD** - Bank Recovery and Resolution Directive
- **SSM** - Single Supervisory Mechanism
- **SRM** - Single Resolution Mechanism

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## 🏛️ Project Structure

```
reg-nav-mvp/
├── src/
│   ├── api/           # FastAPI endpoints
│   ├── models/        # Pydantic data models
│   ├── services/      # Business logic
│   │   ├── llm_service.py       # LLM integration
│   │   ├── vector_db_service.py # Vector database
│   │   ├── rag_service.py       # RAG implementation
│   │   └── document_service.py  # Document ingestion
│   ├── utils/         # Utilities
│   └── config.py      # Configuration
├── tests/             # Test suite
├── data/              # Data storage
│   ├── vector_db/     # Vector database storage
│   └── regulatory_docs/ # Document storage
├── cli.py             # Command-line interface
├── examples.py        # Usage examples
├── requirements.txt   # Dependencies
└── README.md         # This file
```

## 🔧 Configuration Options

### LLM Settings

- `LLM_PROVIDER`: `openai` or `anthropic`
- `LLM_MODEL`: Model name (e.g., `gpt-4-turbo-preview`, `claude-3-opus-20240229`)
- `LLM_TEMPERATURE`: 0.0-1.0 (lower = more deterministic)
- `LLM_MAX_TOKENS`: Maximum response length

### Vector Database

- `VECTOR_DB_PATH`: Path to store vector database
- `EMBEDDING_MODEL`: Sentence transformer model for embeddings

### API

- `API_HOST`: API host address (default: `0.0.0.0`)
- `API_PORT`: API port (default: `8000`)
- `API_RELOAD`: Enable hot reload for development

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is provided as-is for educational and development purposes.

## ⚠️ Disclaimer

This system is an MVP for demonstration purposes. For production use in regulated environments:
- Ensure compliance with data protection regulations
- Validate all regulatory information with official sources
- Implement proper security measures
- Conduct thorough testing and audits
- Consult with legal and compliance experts

## 📧 Support

For questions and support, please open an issue on GitHub.

## 🔮 Future Enhancements

- [ ] Multi-language support (French, German, Spanish)
- [ ] Advanced analytics and reporting
- [ ] Integration with regulatory databases
- [ ] Real-time regulation updates
- [ ] Enhanced compliance workflows
- [ ] Audit trail and logging
- [ ] User authentication and authorization
- [ ] Document comparison and change detection
- [ ] Regulatory impact assessment
- [ ] Export capabilities (PDF reports, Excel)

---

**Built with ❤️ for EU Banking Compliance**