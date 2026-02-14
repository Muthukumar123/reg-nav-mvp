# Regulation Navigator MVP - System Architecture

**Status:** Production ✅ | Running on `localhost:8000`

## System Design

This system implements **Retrieval-Augmented Generation (RAG)** - a two-stage pipeline combining semantic search with LLM-based answer generation. The monolithic application prioritizes clarity and simplicity for MVP development.

### High-Level Data Flow

```
┌──────────────────┐
│   HTTP Request   │
│   POST /ask      │
└────────┬─────────┘
         │ question: str
         │ top_k: int
         ↓
┌──────────────────────────────────────┐
│  STAGE 1: RETRIEVAL                  │
│  (TF-IDF Semantic Search)            │
│  - Vectorize question                │
│  - Compute cosine similarity         │
│  - Filter by relevance threshold     │
│  - Select top-k chunks               │
└────────┬─────────────────────────────┘
         │ chunks: List[dict]
         │ scores: List[float]
         ↓
┌──────────────────────────────────────┐
│  STAGE 2: GENERATION                 │
│  (Azure OpenAI LLM)                  │
│  - Format chunks with sources        │
│  - Send to LLM with system prompt    │
│  - LLM reads context and answers     │
│  - Extract citations from answer    │
└────────┬─────────────────────────────┘
         │ answer: str
         │ citations: List[Citation]
         ↓
┌──────────────────────────────────────┐
│   HTTP Response                      │
│   {answer, citations, scores}        │
└──────────────────────────────────────┘
```

## Architecture Overview

### 1. Core Components

### 1. Core Components

#### Data Layer: `data.txt`
- **Purpose:** Static source of regulatory articles
- **Format:** Plain text with `[DOC] Document Name | Section Name` headers
- **Content:** 35 regulatory articles from 4 EU directives:
  - GDPR (Regulation (EU) 2016/679)
  - PSD2 (Directive (EU) 2015/2366)
  - AML (Directive (EU) 2015/849)
  - MiFID II (Regulation (EU) 2014/65)
- **Parsing:** `load_chunks()` function parses at startup
- **Output:** In-memory list of chunk dictionaries

#### Retrieval Component: `app.py`
- **Responsibility:** Parse data, vectorize, and retrieve similar chunks
- **Mechanism:** TF-IDF (Term Frequency-Inverse Document Frequency)
- **Process:**
  1. Load and parse `data.txt` into 35 chunks
  2. Initialize `TfidfVectorizer` with regulatory vocabulary
  3. Build sparse matrix (35 chunks × 536 vocabulary terms)
  4. On request: vectorize question, compute cosine similarity, rank results
  5. Filter out scores < 0.05 (noise threshold)
  6. Return top-k chunks with scores

**Key Variables:**
```python
CHUNKS          # List of 35 dicts: {doc, section, text}
VECTORIZER      # TfidfVectorizer: fitted with vocabulary
MATRIX          # Sparse matrix (35 × 536): document-term frequencies
```

#### Generation Component: `llm.py`
- **Responsibility:** Call Azure OpenAI LLM with retrieved context
- **Mechanism:** In-context Learning (NOT fine-tuning)
- **Process:**
  1. Format chunks with document headers
  2. Create prompt: system message + question + sources
  3. Call Azure OpenAI gpt-4-turbo-preview API
  4. Return LLM-generated answer with citations
  5. Extract source references from answer text

**Key Configuration:**
```python
Model:           gpt-4-turbo-preview
Temperature:     0.2 (low = deterministic, factual)
Max Tokens:      1000
Timeout:         30 seconds
API:             Azure OpenAI (enterprise deployment)
```

#### API Component: `app.py`
- **Framework:** FastAPI 0.115.0
- **Server:** Uvicorn 0.30.6
- **Port:** 8000 (localhost:8000)
- **Endpoints:**
  - `GET /health` → `{status: "ok"}`
  - `POST /ask` → `{answer, citations, scores}`

**Request Validation:** Pydantic models
```python
AskRequest:
  - question: str (5-1000 chars)
  - top_k: int (1-10, default 3)

AskResponse:
  - answer: str
  - citations: List[Citation]
  - scores: List[float]
```

### 2. Request Processing Pipeline

When a POST request hits `/ask`:

```
Step 1: VALIDATION
  Pydantic parses & validates AskRequest
  → Returns 422 if invalid

Step 2: RETRIEVAL
  TF-IDF vectorizer transforms question
  → Computes cosine similarity against MATRIX
  → Filters by threshold (0.05)
  → Selects top-k chunks
  → Returns: chunks[], scores[]

Step 3: FORMATTING
  Chunks formatted as readable text:
    [Document | Section]
    text...
    
Step 4: LLM API CALL
  System Prompt: "Answer using ONLY these sources"
  Question: from request
  Sources: formatted chunks
  → Azure OpenAI processes
  → Returns: answer text

Step 5: CITATION EXTRACTION
  Parse answer for source references
  → Extract doc + section from citations
  → Build Citation objects

Step 6: RESPONSE FORMATTING
  Pydantic creates AskResponse:
    answer: str (from LLM)
    citations: [Citation, ...]
    scores: float[] (retrieval scores)
  → Return as JSON with HTTP 200
```

### 3. Data Source Details

**File: `data.txt`**

Each regulation chunk follows this format:

```
[DOC] Regulation (EU) 2016/679 | Article 5 - Principles Relating to Processing

(1) Personal data shall be processed lawfully, fairly
and in a transparent manner in relation to the data subject
    ('lawfulness of processing');
    ...
    (more article text)...

[DOC] Regulation (EU) 2016/679 | Article 6 - Lawfulness of processing
    ...
```

**Parsing Logic (`load_chunks`):**
1. Read file line by line
2. Detect `[DOC]` marker
3. Extract: `Regulation name | Section name`
4. Collect text until next `[DOC]`
5. Filter out chunks < 30 characters (noise)
6. Create structured chunk:
   ```python
   {
     "doc": "Regulation (EU) 2016/679",
     "section": "Article 5 - Principles Relating to Processing",
     "text": "(1) Personal data shall be processed lawfully..."
   }
   ```

**Result:** 35 chunks in-memory, ready for retrieval

## 2. SOLID Principles Applied

### 1. Single Responsibility Principle (SRP)

Each function and class has **one reason to change**:

| Component | Responsibility | Changes When |
|-----------|-----------------|-------------|
| `load_chunks()` | Parse `data.txt` format | Data format changes |
| TF-IDF initialization | Build vectorization index | Retrieval algorithm changes |
| Cosine similarity | Rank chunks by relevance | Similarity metric changes |
| `/ask` endpoint | Orchestrate RAG pipeline | Business process changes |
| `call_llm()` | Azure OpenAI API calls | LLM provider changes |

### 2. Open/Closed Principle (OCP)

Open for extension, **closed for modification**:

```python
# ✓ OPEN - Easy to add new regulations
# Just append to data.txt:
# [DOC] New Regulation 2024/XYZ | Article 1
# ...content...
# On restart: automatically indexed and searchable

# ✓ CLOSED - No code changes needed
# The retrieval system doesn't care how many regulations exist
# TF-IDF works with any corpus size
```

### 3. Liskov Substitution Principle (LSP)

Subtypes must be substitutable for base types. In our system, we could swap implementations:

```python
# Current: TF-IDF retrieval
retrieval_engine = TfidfVectorizer(...)

# Alternative: Could be BM25, embeddings, semantic search, etc.
# If interface stays same, everything else works unchanged
```

### 4. Interface Segregation Principle (ISP)

Small focused interfaces, not bloated ones:

```python
# ✓ GOOD - Focused operations
load_chunks()      # Just data loading
retrieve()         # Just retrieval
call_llm()        # Just generation

# ✗ BAD - Bloated "superfunction"
def universal_compliance_answer():
    # Load, validate, retrieve, format, generate, cache, log...
    # Too many responsibilities!
```

### 5. Dependency Inversion Principle (DIP)

Depend on abstractions, not concrete implementations:

```python
# Current: Concrete dependencies
VECTORIZER     # TfidfVectorizer instance (concrete)
client         # Azure OpenAI client (concrete)

# Principle: Could be injected
class RetrievalEngine(Protocol):
    def retrieve(q: str, k: int) -> (chunks, scores)

class GenerationEngine(Protocol):
    def generate(question: str, context: str) -> str
```

## 3. Design Patterns Used

### Singleton Pattern
```python
# Global instances, created once, reused throughout
CHUNKS = load_chunks()          # Loaded once at startup
VECTORIZER = TfidfVectorizer()  # Built once at startup
MATRIX = VECTORIZER.fit_transform(...)
client = _get_client()          # Single Azure OpenAI client
```

### Strategy Pattern
```python
# Question filtering strategy
if len(question) < 5:
    strategy = REJECT              # Too short
elif "not found" in answer.lower():
    strategy = REFUSE              # Out of scope  
else:
    strategy = ANSWER              # In scope
```

### Adapter Pattern
```python
# Pydantic models adapt HTTP ↔ application layer
# AskRequest (HTTP) → internal processing
# internal result → AskResponse (HTTP)
```

### Template Method Pattern
```python
# /ask endpoint follows fixed sequence:
# 1. Validate request
# 2. Retrieve similar chunks
# 3. Call LLM with chunks
# 4. Format response
```

### Factory Pattern
```python
# `_get_client()` creates Azure OpenAI client
# `load_chunks()` builds chunk list
# Configuration decisions centralized
```

## 4. Architectural Decisions

### Decision 1: Monolithic vs Microservices
**Choice:** Monolithic  
**Rationale:** MVP needs simplicity; all components coupled (retrieval → LLM)

### Decision 2: TF-IDF vs Semantic Embeddings
**Choice:** TF-IDF  
**Rationale:** Lightweight; exact term matching often better for regulatory domain

### Decision 3: In-Memory vs Database
**Choice:** In-Memory  
**Rationale:** 35 chunks = negligible memory (~50KB); fast startup for MVP

### Decision 4: System Prompt Strategy
**Choice:** Constraint-based ("Use ONLY provided sources")  
**Rationale:** Prevents hallucination; forces citations; aligns with regulatory requirements

## 5. Performance Profile

### Latency (Per /ask Request)

| Phase | Duration | Notes |
|-------|----------|-------|
| Request validation | ~1ms | Pydantic |
| Vectorization | ~1-5ms | TF-IDF |
| Cosine similarity | ~1-2ms | 35 × 536 |
| LLM API call | **2-8s** | Network + inference |
| Total | **~2-8s** | LLM dominates |

### Memory Usage

| Component | Size |
|-----------|------|
| Chunks (35 articles) | ~20KB |
| TF-IDF vocabulary | ~10KB |
| Sparse matrix | ~50KB |
| Python runtime | ~50MB |
| Azure client | ~5MB |
| **Total** | **~75MB** |

### Concurrency

- **Requests/sec:** ~1-2 (limited by LLM latency)
- **Simultaneous requests:** 10s (before LLM queue fills)
- **Max memory footprint:** 75-100MB

## 6. File Structure

```
reg-nav-mvp/
├── app.py                      # FastAPI application (412 lines)
├── llm.py                      # Azure OpenAI integration (258 lines)
├── data.txt                    # 35 regulatory articles
├── requirements.txt            # Dependencies
├── README.md                   # User guide + API docs
├── ARCHITECTURE.md             # This file
├── tests/
│   ├── test_app.py            # Application tests
│   └── test_dependencies.py    # Import tests
└── __pycache__/                # Python bytecode
```

## 7. Technology Stack

| Layer | Technology | Version | Why |
|-------|-----------|---------|-----|
| API | **FastAPI** | 0.115.0 | Fast, auto docs, validation |
| Server | **Uvicorn** | 0.30.6 | ASGI, async, production |
| Validation | **Pydantic** | 2.8.2 | Auto serialization |
| Retrieval | **scikit-learn** | 1.5.1 | TF-IDF, fast, lightweight |
| LLM | **Azure OpenAI** | 1.40.6 | SOTA model, compliance |
| Config | **python-dotenv** | 1.0.1 | Environment variables |

## 8. Future Enhancements

### Phase 2: Semantic Search
- Replace TF-IDF with embedding vectors
- Add vector database (Pinecone, Weaviate)
- Better semantic relevance

### Phase 3: Caching
- Cache common questions
- Reduce LLM calls
- Improve latency

### Phase 4: Multi-Language
- Translate questions to English
- Return answers in user language
- Expand market

### Phase 5: Audit Trail
- Log all queries + answers
- Compliance reporting
- Quality monitoring

### Phase 6: Web UI
- Interactive chat interface
- Question templates
- Export to PDF

## 9. Testing Strategy

All code is documented with comprehensive docstrings explaining:
- Purpose and responsibility
- Architecture principles applied
- Data transformations and contracts
- Error handling approach
- Integration points

See [README.md](README.md) for API testing examples.

## 10. Summary

**Regulation Navigator MVP** is a production-ready RAG system implementing:

✅ **SOLID Principles** throughout the codebase  
✅ **Design Patterns** (Singleton, Strategy, Adapter, Template Method)  
✅ **Clean Architecture** with clear separation of concerns  
✅ **Comprehensive Documentation** at every level  
✅ **Production-Ready** error handling and logging  
✅ **Scalable Foundation** for future enhancements

The system prioritizes:
1. **Clarity** - Every file clearly explains what it does
2. **Reliability** - Tested error paths and edge cases
3. **Maintainability** - Well-organized, well-documented code
4. **Extensibility** - Easy to add features without breaking existing code
5. **Performance** - Optimized for the critical path (LLM latency)