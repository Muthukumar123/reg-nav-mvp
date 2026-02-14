"""
REFACTORING_GUIDE.md - Practical Usage of the Refactored Architecture

This guide shows how to use the new SOLID-compliant codebase
and demonstrates the layered architecture in action.
"""

# Refactored Compliance Q&A System - Usage Guide

## 1. Quick Start

### Start the API Server

```bash
# Activate environment
source venv/bin/activate

# Set Azure credentials
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="your-endpoint"
export AZURE_OPENAI_DEPLOYMENT="your-deployment"

# Run refactored application
python -m uvicorn app_refactored:app --reload --port 8000
```

Server will start at `http://localhost:8000`

### Make a Request

```bash
curl -X POST http://localhost:8000/api/compliance/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main data protection requirements?",
    "top_k": 3
  }'
```

## 2. Using the Refactored Code Programmatically

### Example 1: Direct Service Usage

```python
from infrastructure.dependencies import initialize_compliance_service

# Initialize service (loads and indexes data)
service = initialize_compliance_service("data.txt")

# Create a question
from core.entities import ComplianceQuestion
question = ComplianceQuestion(
    question="What is GDPR Article 5?",
    top_k=3
)

# Get answer
answer = service.answer_question(question)

# Use result
print(f"Answer: {answer.answer}")
print(f"Citations: {[f'{c.doc}|{c.section}' for c in answer.citations]}")
print(f"Scores: {answer.scores}")
```

### Example 2: Using Container with Different Implementations

```python
from infrastructure.dependencies import ComplianceContainer
from infrastructure.retrieval import TfidfRetrievalEngine
from infrastructure.llm_client import AzureOpenAIModel
from infrastructure.data_loader import RegulatoryDocumentLoader
from application.compliance_service import ComplianceService

# Get singleton container
container = ComplianceContainer()

# Manually create service (same as container does internally)
service = ComplianceService(
    retrieval_engine=container.get_retrieval_engine(),
    language_model=container.get_language_model(),
    data_loader=container.get_data_loader()
)

# Initialize with data
service.initialize("data.txt")

# Answer questions
from core.entities import ComplianceQuestion
q = ComplianceQuestion(question="What about PSD2?", top_k=3)
answer = service.answer_question(q)
```

### Example 3: Command-Line Tool

```python
#!/usr/bin/env python

import sys
import logging
from infrastructure.dependencies import initialize_compliance_service
from core.entities import ComplianceQuestion

logging.basicConfig(level=logging.INFO)

# Initialize
service = initialize_compliance_service("data.txt")

# Process questions from stdin
print("Enter compliance questions (type 'quit' to exit):")
while True:
    question_text = input("> ").strip()
    if question_text.lower() == "quit":
        break
    
    try:
        question = ComplianceQuestion(question=question_text, top_k=3)
        answer = service.answer_question(question)
        
        print(f"\n📋 Answer: {answer.answer}\n")
        print("📚 Sources:")
        for citation, score in zip(answer.citations, answer.scores):
            print(f"   • {citation.doc} | {citation.section} (score: {score:.3f})")
        print()
    except Exception as e:
        print(f"Error: {e}\n")
```

### Example 4: Batch Processing

```python
import json
from infrastructure.dependencies import initialize_compliance_service
from core.entities import ComplianceQuestion

# Initialize
service = initialize_compliance_service("data.txt")

# Sample questions
questions = [
    "What is GDPR?",
    "What is PSD2?",
    "What is MiFID II?",
    "Tell me a joke",  # Should be rejected (out of scope)
]

# Process batch
results = []
for q_text in questions:
    try:
        question = ComplianceQuestion(q_text, top_k=3)
        answer = service.answer_question(question)
        
        results.append({
            "question": q_text,
            "answer": answer.answer,
            "num_citations": len(answer.citations),
            "avg_score": sum(answer.scores) / len(answer.scores) if answer.scores else 0
        })
    except Exception as e:
        results.append({
            "question": q_text,
            "error": str(e)
        })

# Save results
with open("batch_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Processed {len(results)} questions, saved to batch_results.json")
```

## 3. Testing the Refactored Code

### Unit Test: Infrastructure Layer

```python
# tests/test_retrieval.py
import pytest
from core.entities import RegulatoryChunk
from infrastructure.retrieval import TfidfRetrievalEngine

def test_tfidf_retrieval():
    """Test TF-IDF retrieval engine."""
    # Create engine
    engine = TfidfRetrievalEngine(min_similarity_threshold=0.05)
    
    # Create sample chunks
    chunks = [
        RegulatoryChunk("GDPR", "Article 5", "Data protection principles..."),
        RegulatoryChunk("PSD2", "Article 38", "Security requirements..."),
        RegulatoryChunk("GDPR", "Article 6", "Lawful basis..."),
    ]
    
    # Index chunks
    engine.index_chunks(chunks)
    
    # Retrieve
    results, scores = engine.retrieve("data protection", top_k=1)
    
    # Assertions
    assert len(results) == 1
    assert results[0].doc == "GDPR"
    assert len(scores) == 1
    assert 0 <= scores[0] <= 1

def test_out_of_scope_question():
    """Test that out-of-scope questions are rejected."""
    engine = TfidfRetrievalEngine(min_similarity_threshold=0.05)
    
    chunks = [
        RegulatoryChunk("GDPR", "Article 5", "Data protection..."),
    ]
    engine.index_chunks(chunks)
    
    # Out of scope
    is_in_scope = engine.is_question_in_scope("Tell me a joke", threshold=0.05)
    
    assert is_in_scope == False
```

### Unit Test: Application Layer (with Mocks)

```python
# tests/test_compliance_service.py
from unittest.mock import Mock
from core.entities import RegulatoryChunk, ComplianceQuestion, Citation
from core.interfaces import RetrievalEngine
from application.compliance_service import ComplianceService

def test_service_orchestration():
    """Test that service correctly orchestrates components."""
    # Create mocks
    mock_retrieval = Mock(spec=RetrievalEngine)
    mock_llm = Mock()
    mock_loader = Mock()
    
    # Setup mock behavior
    chunk = RegulatoryChunk("GDPR", "Article 5", "Data protection...")
    mock_retrieval.is_question_in_scope.return_value = True
    mock_retrieval.retrieve.return_value = ([chunk], [0.45])
    mock_llm.generate_answer.return_value = "Article 5 requires..."
    mock_loader.load.return_value = [chunk]
    
    # Create service with mocks
    service = ComplianceService(
        retrieval_engine=mock_retrieval,
        language_model=mock_llm,
        data_loader=mock_loader
    )
    
    # Initialize
    service.initialize("data.txt")
    
    # Call service
    question = ComplianceQuestion("What is GDPR?", top_k=3)
    answer = service.answer_question(question)
    
    # Verify
    assert answer.answer == "Article 5 requires..."
    assert len(answer.citations) == 1
    assert answer.citations[0].doc == "GDPR"
```

### Integration Test: Full Stack

```python
# tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from app_refactored import app
from infrastructure.dependencies import ComplianceContainer

@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)

def test_api_ask_question(client):
    """Test the full API endpoint."""
    response = client.post(
        "/api/compliance/ask",
        json={
            "question": "What is GDPR?",
            "top_k": 3
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "answer" in data
    assert "citations" in data
    assert "scores" in data
    assert isinstance(data["citations"], list)

def test_api_validation(client):
    """Test API input validation."""
    # Too short question
    response = client.post(
        "/api/compliance/ask",
        json={"question": "hi", "top_k": 3}
    )
    assert response.status_code == 400
    
    # Invalid top_k
    response = client.post(
        "/api/compliance/ask",
        json={"question": "What is GDPR?", "top_k": 100}
    )
    assert response.status_code == 400
```

## 4. Architecture in Pictures

### Method Call Flow

```
User Code
   ↓
   ComplianceService.answer_question(ComplianceQuestion)
   ├─→ RetrievalEngine.is_question_in_scope()
   │   └─→ TfidfRetrievalEngine (concrete implementation)
   │
   ├─→ RetrievalEngine.retrieve()
   │   └─→ TfidfRetrievalEngine (concrete implementation)
   │
   ├─→ LanguageModel.generate_answer()
   │   └─→ AzureOpenAIModel (concrete implementation)
   │
   └─→ ComplianceAnswer (domain entity)
```

### Dependency Injection Points

```
ComplianceContainer (DI)
├─ Creates TfidfRetrievalEngine
├─ Creates AzureOpenAIModel
├─ Creates RegulatoryDocumentLoader
└─ Wires into ComplianceService

HTTPComplianceAPI
├─ Receives ComplianceService (injected)
└─ Receives FastAPI Router

App (FastAPI)
├─ Receives HTTPComplianceAPI (injected via lifespan)
└─ Routes HTTP requests through adapter
```

## 5. Key Improvements Over Original

### Original (Monolithic)

```python
# Old app.py - Everything mixed together
@app.post("/ask")
def ask_question(question: str, top_k: int):
    # Validation here
    # Retrieval here
    # LLM calling here
    # Response formatting here
    # All in one function!
```

**Problems**:
- Hard to test (need Azure OpenAI credentials for unit tests)
- Hard to reuse (coupled to FastAPI)
- Hard to extend (add new retrieval = modify app.py)
- Hard to maintain (one file does everything)

### Refactored (Layered + SOLID)

```python
# New architecture - Clear separation
# Layer 1: Domain
ComplianceQuestion → ComplianceAnswer

# Layer 2: Application
ComplianceService orchestrates

# Layer 3: Infrastructure
TfidfRetrievalEngine
AzureOpenAIModel
RegulatoryDocumentLoader

# Layer 4: Presentation
HTTPComplianceAPI
FastAPI routes
```

**Benefits**:
- ✅ Easy to test (mock interfaces, no external calls)
- ✅ Easy to reuse (service works anywhere)
- ✅ Easy to extend (add new implementations)
- ✅ Easy to maintain (single responsibility per class)

## 6. Extending the System

### Add New Retrieval Engine

```python
# 1. Create new class
from core.interfaces import RetrievalEngine

class EmbeddingsRetrievalEngine(RetrievalEngine):
    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model)
        self.chunks = []
        self.embeddings = None
    
    def index_chunks(self, chunks):
        self.chunks = chunks
        texts = [c.text for c in chunks]
        self.embeddings = self.model.encode(texts)
    
    def retrieve(self, question, top_k):
        query_embedding = self.model.encode(question)
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        top_indices = similarities.argsort()[-top_k:][::-1]
        return [self.chunks[i] for i in top_indices], similarities[top_indices].tolist()
    
    def is_question_in_scope(self, question, threshold):
        query_embedding = self.model.encode(question)
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        return max(similarities) > threshold

# 2. Update container (optional - use composition)
service = ComplianceService(
    retrieval_engine=EmbeddingsRetrievalEngine(),  # Swap here
    language_model=container.get_language_model(),
    data_loader=container.get_data_loader()
)

# 3. No changes needed to:
# - HTTPComplianceAPI
# - ComplianceService
# - FastAPI app
# Everything works!
```

### Add New LLM Provider

```python
# 1. Create new class
from core.interfaces import LanguageModel

class AnthropicModel(LanguageModel):
    def __init__(self, api_key: str):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)
    
    def generate_answer(self, question: str, context: str) -> str:
        system_prompt = """You are a compliance assistant. 
        ONLY use the provided regulatory sources to answer questions.
        ALWAYS cite which article or regulation you're referencing.
        Never make up regulations or compliance requirements."""
        
        response = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
            ]
        )
        
        return response.content[0].text

# 2. Use new implementation
service = ComplianceService(
    retrieval_engine=container.get_retrieval_engine(),
    language_model=AnthropicModel(api_key=os.getenv("ANTHROPIC_API_KEY")),
    data_loader=container.get_data_loader()
)
```

## 7. Production Deployment

### Using Gunicorn + Uvicorn

```bash
# Install
pip install gunicorn

# Run with 4 workers
gunicorn app_refactored:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

### Using Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "app_refactored:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000"]
```

## 8. Monitoring and Debugging

### Check Service Health

```python
from infrastructure.dependencies import initialize_compliance_service
from core.entities import ComplianceQuestion

service = initialize_compliance_service("data.txt")

# Test retrieval
q = ComplianceQuestion("test query", top_k=1)
answer = service.answer_question(q)

print(f"✓ Service working: {len(answer.citations)} citations")
print(f"✓ Answer received: {answer.answer[:100]}...")
```

### View Configuration

```python
from infrastructure.dependencies import ComplianceConfig

print(f"Data file: {ComplianceConfig.DATA_FILE}")
print(f"Min similarity: {ComplianceConfig.RETRIEVAL_MIN_SIMILARITY}")
print(f"LLM model: {ComplianceConfig.LLM_MODEL}")
print(f"LLM temperature: {ComplianceConfig.LLM_TEMPERATURE}")
```

### Enable Debug Logging

```python
import logging

# Set all layers to DEBUG
logging.getLogger("core").setLevel(logging.DEBUG)
logging.getLogger("infrastructure").setLevel(logging.DEBUG)
logging.getLogger("application").setLevel(logging.DEBUG)
logging.getLogger("adapters").setLevel(logging.DEBUG)
```

## 9. Performance Tips

### Cache Indexing

```python
# Don't re-index on every request
service = initialize_compliance_service("data.txt")  # Indexes once

# All requests reuse the index
for i in range(1000):
    q = ComplianceQuestion("What is GDPR?", top_k=3)
    answer = service.answer_question(q)
```

### Parallel LLM Calls

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def process_questions_parallel(questions, service):
    with ThreadPoolExecutor(max_workers=4) as executor:
        loop = asyncio.get_event_loop()
        
        tasks = [
            loop.run_in_executor(
                executor,
                service.answer_question,
                ComplianceQuestion(q, top_k=3)
            )
            for q in questions
        ]
        
        answers = await asyncio.gather(*tasks)
        return answers
```

## 10. Conclusion

The refactored architecture provides:
- ✅ **SOLID principles** for professional code
- ✅ **Separation of concerns** for maintainability
- ✅ **Dependency injection** for testability
- ✅ **Design patterns** for extensibility
- ✅ **Production-ready** error handling and logging

This is enterprise-grade software engineering for compliance Q&A.

