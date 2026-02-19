"""
Regulation Navigator MVP - FastAPI Application

ARCHITECTURE OVERVIEW
=====================

This is a Retrieval-Augmented Generation (RAG) system that answers regulatory compliance
questions using a two-stage process:

1. RETRIEVAL STAGE: TF-IDF vectorization finds relevant regulatory chunks
   - Load question text
   - Calculate cosine similarity against pre-built TF-IDF index
   - Return top_k most semantically similar chunks with scores

2. GENERATION STAGE: Azure OpenAI LLM generates answer from retrieved chunks
   - Send question + retrieved chunks as context to LLM
   - LLM reads the regulatory text and generates source-based answer
   - Extract citations from the generated response
   - Format and return JSON response

DATA FLOW
=========

User Query (HTTP POST /ask)
   ↓
Input Validation (Pydantic)
   ↓
TF-IDF Retrieval (ChunkRetriever)
   └─ Cosine similarity against data.txt chunks
   └─ Returns top_k chunks with scores
   ↓
LLM Generation (llm.call_llm)
   └─ Azure OpenAI gpt-4-turbo-preview
   └─ Temperature: 0.2 (practical, low hallucination)
   ↓
Response Formatting
   └─ Structure: {answer, citations[], scores[]}
   ↓
HTTP Response (JSON)

ARCHITECTURE PRINCIPLES APPLIED
===============================

1. SEPARATION OF CONCERNS
   - load_chunks(): Handles data parsing only
   - ChunkRetriever: Handles retrieval logic only
   - llm.call_llm(): Handles LLM calls only
   - Flask route: Handles HTTP concerns only

2. SINGLE RESPONSIBILITY PRINCIPLE
   Each function does ONE thing:
   - load_chunks: Parse data.txt → list of chunks
   - initialize_retrieval: Build TF-IDF index from chunks
   - ask_question route: Validate input → call retrieval → call LLM → format response

3. DEPENDENCY INJECTION
   - llm module imported (not hardcoded)
   - Configuration via environment variables
   - Easy to swap LLM implementations

4. ERROR HANDLING
   - Input validation: Pydantic checks question length
   - Graceful degradation: Return user-friendly error messages
   - Detailed logging: All stages logged for debugging

5. PERFORMANCE OPTIMIZATION
   - Single TF-IDF index built at startup (not per-request)
   - Scikit-learn cosine similarity is optimized
   - Top-k retrieval limits context size for LLM

KEY FILES
=========
- app.py: FastAPI routes + retrieval logic (this file)
- llm.py: Azure OpenAI integration
- data.txt: Source regulatory documents in structured format

DATA SOURCE DETAILS
===================
Source: data.txt (static plain text file)
Format: [DOC] Document_Name | Section_Name / Content_text...
Storage: In-memory list of dicts with keys: doc, section, text
Loading: Once at app startup, remains in memory
Chunks: 35 regulatory articles from 4 EU directives
Index: TF-IDF matrix (35 chunks × 536 vocabulary)

API CONTRACT
============
REQUEST:  POST /ask {"question": "...", "top_k": 3}
RESPONSE: {"answer": "...", "citations": [...], "scores": [...]}

APPLICATION vs API DIFFERENCE
==============================
Application (Internal):
- Works with chunk dicts: {"doc": "...", "section": "...", "text": "..."}
- Similarity scores: Raw cosine similarity values
- Source tracking: List of retrieved chunks

API (External):
- Returns citations array: [{"doc": "...", "section": "..."}]
- Scores array: Parallel to citations for display
- Answer text: Formatted with citation references
- All values serialized to JSON

KEY FEATURES
============
- TF-IDF based retrieval (not full-text search)
- Cosine similarity scoring (semantic relevance)
- Top-k retrieval (configurable context size)
- Azure OpenAI LLM integration (gpt-4-turbo)
- Citation tracking (answer references sources)
- Comprehensive logging (all stages)
- Input validation (Pydantic models)
- Interactive API docs (Swagger UI + ReDoc)
"""

import logging
from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict

from llm import call_llm

# Try to import optional infrastructure modules
try:
    from infrastructure.analytics import analytics
except Exception as e:
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"Could not import analytics: {e}. Analytics disabled.")
    class DummyAnalytics:
        def track_login(self, user): pass
        def track_query(self, q, t, s, r=None): pass
    analytics = DummyAnalytics()

try:
    from infrastructure.query_cache import query_cache
except Exception as e:
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"Could not import query_cache: {e}. Cache disabled.")
    class DummyCache:
        def get(self, k): return None
        def set(self, *args, **kwargs): pass
        def clear(self): pass
    query_cache = DummyCache()

# Configure structured logging with timestamp, logger name, and level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application with title for OpenAPI documentation
app = FastAPI(title="Regulation Navigator MVP")

# Add request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all incoming requests for debugging."""
    request_body = b""
    try:
        request_body = await request.body()
        logger.debug(f"{request.method} {request.url.path} - Body: {request_body[:200]}")
    except:
        pass
    
    # Call the next middleware
    response = await call_next(request)
    logger.debug(f"Response status: {response.status_code}")
    return response

# Add CORS middleware to allow frontend cross-origin requests
# Allow all origins in development mode for easier debugging
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "*",  # Allow all origins in dev mode - remove in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# AUTHENTICATION CONFIGURATION
# ============================================================================

# Hardcoded credentials
VALID_USERNAME = "Muthu"
VALID_PASSWORD_HASH = None  # Will be set below

# SHA256 hash with mod key
MOD_KEY = "Handbook"

def hash_password(password: str, mod_key: str = MOD_KEY) -> str:
    """Hash password using SHA256 with mod key."""
    combined = password + mod_key
    return hashlib.sha256(combined.encode()).hexdigest()

# Calculate and store the valid password hash
VALID_PASSWORD_HASH = hash_password("AIApps@2026")

# In-memory token storage (token -> username, expiry)
ACTIVE_TOKENS: Dict[str, tuple[str, datetime]] = {}

def generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)

def verify_token(token: str) -> str:
    """Verify token and return username if valid."""
    if token not in ACTIVE_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    username, expiry = ACTIVE_TOKENS[token]
    if datetime.now() > expiry:
        del ACTIVE_TOKENS[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    
    return username

# ============================================================================
# DATA LOADING & INITIALIZATION
# ============================================================================

def load_chunks(path="data.txt", include_multilingual=True):
    """Load and parse regulatory document chunks from data file.
    
    DATA SOURCE DETAILS
    ===================
    File: data.txt (static plain text, committed to repo)
    Format: [DOC] DOCUMENT_NAME | SECTION_NAME
            Content text...
            [DOC] Next document...
    
    Multilingual Support:
    - Also loads data_multilingual.txt if available
    - Chunks tagged with language codes: [DOC:EN] [DOC:DE] [DOC:ES] [DOC:FR]
    - Enables language-aware retrieval and LLM grounding
    
    Purpose: Serve as the knowledge base for retrieval.
    
    Parsing Process:
    1. Read file line by line
    2. Detect [DOC] headers with pipe-separated doc name and section
    3. Collect text until next header as chunk content
    4. Filter out chunks with < 30 characters (avoid noise)
    5. Return list of structured chunk dictionaries
    
    Output Format:
    [
        {
            "doc": "Regulation (EU) 2016/679",
            "section": "Article 5 - Principles Relating to Processing",
            "text": "Personal data shall be processed lawfully...",
            "language": "en",
            "source": "data.txt"
        },
        ...
    ]
    
    This is APPLICATION INTERNAL representation.
    API layer will transform to citations JSON.
    
    Args:
        path (str): Path to the data file. Default: "data.txt"
        include_multilingual (bool): Also load multilingual chunks
        
    Returns:
        list: List of chunk dictionaries with keys:
              - 'doc' (str): Document identifier
              - 'section' (str): Section/article name
              - 'text' (str): Chunk content text
              - 'language' (str): Language code (en, de, es, fr, nl, pt)
              - 'source' (str): Source file name
              
    Raises:
        FileNotFoundError: If the data file doesn't exist
        Exception: For other file reading errors
    """
    try:
        logger.info(f"Loading chunks from {path}")
        chunks = []
        current = None
        current_lang = "en"
        current_source = path

        def _parse_lang_from_header(line):
            """Extract language code from [DOC:XX] format."""
            if "[DOC:" in line and "]" in line:
                lang_code = line.split("[DOC:")[1].split("]")[0].lower()
                return lang_code
            return "en"

        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue

                # Check for language markers [LANG:XX]
                if line.startswith("[LANG:"):
                    current_lang = line.split("[LANG:")[1].split("]")[0].lower()
                    continue

                if line.startswith("[DOC"):
                    # Save previous chunk if exists
                    if current:
                        chunks.append(current)

                    # Extract language from [DOC:XX] if present
                    detected_lang = _parse_lang_from_header(line)
                    
                    # Parse header: [DOC] DOC_NAME | SECTION_NAME or [DOC:XX] DOC_NAME | SECTION_NAME
                    header = line.replace("[DOC]", "").replace(f"[DOC:{detected_lang}]", "").strip()
                    parts = [p.strip() for p in header.split("|")]
                    doc = parts[0] if len(parts) > 0 else "UNKNOWN_DOC"
                    section = parts[1] if len(parts) > 1 else "UNKNOWN_SECTION"
                    
                    # Initialize new chunk with metadata and empty text
                    current = {
                        "doc": doc,
                        "section": section,
                        "text": "",
                        "language": detected_lang if detected_lang != "en" else current_lang,
                        "source": current_source
                    }
                else:
                    # Append content to current chunk
                    if current:
                        current["text"] += line + " "

        # Don't forget the last chunk
        if current:
            chunks.append(current)

        # Filter out chunks with minimal text (< 30 chars) to avoid noise
        filtered_chunks = [c for c in chunks if len(c.get("text", "")) > 30]
        logger.info(f"Loaded {len(filtered_chunks)} chunks from {path}")
        
        # Load multilingual chunks if available
        if include_multilingual:
            try:
                multilingual_chunks = load_chunks("data_multilingual.txt", include_multilingual=False)
                filtered_chunks.extend(multilingual_chunks)
                logger.info(f"Added {len(multilingual_chunks)} multilingual chunks. Total: {len(filtered_chunks)}")
            except FileNotFoundError:
                logger.info("Multilingual data file (data_multilingual.txt) not found. Using primary data only.")
            except Exception as e:
                logger.warning(f"Could not load multilingual chunks: {str(e)}")
        
        return filtered_chunks
    
    except FileNotFoundError:
        logger.error(f"Data file not found: {path}")
        raise
    except Exception as e:
        logger.error(f"Error loading chunks from {path}: {str(e)}")
        raise

try:
    CHUNKS = load_chunks()
    logger.info(f"Initialized with {len(CHUNKS)} document chunks")
except Exception as e:
    logger.critical(f"Failed to load data chunks: {str(e)}")
    CHUNKS = []

# ============================================================================
# TF-IDF RETRIEVAL ENGINE INITIALIZATION
# ============================================================================
#
# RETRIEVAL MECHANISM
# ===================
# This system uses TF-IDF (Term Frequency-Inverse Document Frequency) for semantic
# retrieval. Here's how it works:
#
# 1. VECTORIZATION (fit_transform)
#    - Each chunk's text is converted to a TF-IDF vector
#    - TF-IDF scores terms by their frequency in the chunk vs all chunks
#    - Common terms (like "the") get low weights
#    - Specific regulatory terms get high weights
#    - Result: MATRIX is a sparse matrix (35 chunks × 536 terms)
#
# 2. QUERY MATCHING (cosine_similarity)
#    - User question is vectorized using same VECTORIZER
#    - Cosine similarity compares question vector to each chunk vector
#    - Score ranges from 0.0 (no match) to 1.0 (perfect match)
#    - Semantic matching: "processing data" matches "processing personal information"
#
# 3. RANKING (top_k selection)
#    - Scores are sorted and top_k chunks selected
#    - Top_k parameter (default=3) controls context size sent to LLM
#    - Tradeoff: More chunks = more context, but may confuse LLM
#
# PARAMETERS
# ==========
# stop_words=None: Keep all words (don't filter "the", "a", etc)
#                  Regulatory text needs these for proper understanding
# min_df=1: Accept even single-occurrence terms
#          Each regulatory article might use specific terminology once
# analyzer='word': Split on word boundaries (not character or phrase)
# lowercase=True: Normalize to lowercase for matching
# token_pattern: Use standard word pattern regex

try:
    # Initialize TF-IDF vectorizer with minimal filtering
    VECTORIZER = TfidfVectorizer(
        stop_words=None,  # Don't filter stop words - regulatory language needs them
        min_df=1,         # Accept even single-occurrence terms (regulatory specific words)
        analyzer='word',
        lowercase=True,
        token_pattern=r'(?u)\b\w+\b'
    )
    # fit_transform() learns vocabulary from chunk texts and creates sparse matrix
    # Output: MATRIX[i][j] = TF-IDF score for term j in chunk i
    # Sparse format saves memory (most cells are 0)
    MATRIX = VECTORIZER.fit_transform([c["text"] for c in CHUNKS])
    logger.info(f"Built TF-IDF index with shape {MATRIX.shape} (chunks × vocabulary)")
except Exception as e:
    logger.critical(f"Failed to build retrieval index: {str(e)}")
    VECTORIZER = None
    MATRIX = None

# ============================================================================
# REQUEST/RESPONSE MODELS (API CONTRACTS)
# ============================================================================

class LoginRequest(BaseModel):
    """Login request with username and password hash."""
    username: str = Field(..., description="Username")
    password_hash: str = Field(..., description="SHA256 hashed password (password + 'Handbook')")

class LoginResponse(BaseModel):
    """Login response with token."""
    success: bool
    token: Optional[str] = None
    message: str

class AskRequest(BaseModel):
    """Request model for the POST /ask endpoint.
    
    This is the API CONTRACT that clients use to ask questions.
    It gets automatically validated by Pydantic before reaching the handler.
    
    DISTINCTION: APPLICATION vs API
    ===============================
    This is an API-level model (what clients send over HTTP).
    Internally, the application works with chunk dictionaries from load_chunks().
    The handler transforms between these two representations.
    
    Attributes:
        question (str): The regulatory compliance question.
                       - Will be vectorized using VECTORIZER for similarity matching
                       - Must be 5-1000 characters
                       - Example: "What are customer due diligence requirements?"
                       
        top_k (int): Number of relevant chunks to retrieve from data.txt.
                    - Default: 3  (retrieves top 3 most similar chunks)
                    - Range: 1-10 (arbitrary max to avoid huge context)
                    - Higher k = more context for LLM, but may dilute focus
                    - Semantic relevance determined by cosine similarity scores
    """
    question: str = Field(..., min_length=5, max_length=1000,
                          description="Regulatory compliance question (5-1000 chars)")
    top_k: int = Field(default=3, ge=1, le=10,
                       description="Number of sources to retrieve (1-10)")
    language: str = Field(default="en", regex="^[a-z]{2}$",
                         description="Language code (en, de, es, fr, nl, pt)")

class Citation(BaseModel):
    """Citation reference for answer sources.
    
    API model representing where an answer came from (source document + section).
    This is what the API RETURNS to clients (transformed from internal chunks).
    
    Attributes:
        doc (str): Source document/regulation name
                  Example: "Regulation (EU) 2016/679" (GDPR)
        section (str): Specific section/article reference
                      Example: "Article 5 - Principles Relating to Processing"
    """
    doc: str = Field(..., description="Regulation document name")
    section: str = Field(..., description="Article or section name")

class AskResponse(BaseModel):
    """Response model for the POST /ask endpoint.
    
    This is the API CONTRACT that the server returns to clients.
    Contains the generated answer, source citations, and relevance scores.
    
    INTERNAL vs EXTERNAL
    ====================
    The application internally generates answer data.
    This model structures it for JSON serialization to clients.
    
    Attributes:
        answer (str): Generated answer text.
                     - Contains the LLM-generated response
                     - Includes explicit citations like "Article 5; Article 13"
                     - Format: answer_text + "\nCitations: source1; source2; ..."
                     
        citations (list[Citation]): Sources the answer drew from.
                                    - Derived from retrieved chunk metadata
                                    - Parallel to scores array (same order)
                                    - Each citation identifies doc and section
                                    
        scores (list[float]): Semantic relevance scores for each chunk.
                             - Cosine similarity scores from TF-IDF matching
                             - Range: 0.0 (no match) to 1.0 (perfect match)
                             - First score usually highest (most relevant chunk)
                             - Not confidence in answer; just retrieval relevance
    """
    answer: str = Field(..., description="Generated answer with citations")
    citations: list[Citation] = Field(..., description="Sources referenced in answer")
    scores: list[float] = Field(..., description="Relevance scores for each source")

@app.get("/")
def root():
    """Root endpoint providing API information and available endpoints.
    
    Returns service metadata and list of all available API endpoints for
    client discovery and documentation purposes.
    
    Returns:
        dict: API information with service name, version, endpoints, and status
    """
    return {
        "service": "Regulation Navigator MVP",
        "version": "1.0.0",
        "endpoints": {
            "/": "API information (this page)",
            "/auth/login": "POST - Login with username and password hash",
            "/ask": "POST - Ask regulatory questions (requires authentication)",
            "/health": "Health check endpoint",
            "/test-cors": "CORS test endpoint",
            "/docs": "Interactive API documentation (Swagger UI)",
            "/redoc": "Alternative API documentation (ReDoc)"
        },
        "status": "running",
        "authentication": "Required - Login first at /auth/login"
    }

@app.get("/test-cors")
def test_cors():
    """Simple CORS test endpoint to verify connectivity."""
    return {
        "message": "CORS working!",
        "timestamp": str(__import__('datetime').datetime.now()),
        "cors_test": True
    }

@app.get("/health")
def health():
    """Health check endpoint."""
    try:
        logger.debug("Health check requested")
        return {
            "status": "ok",
            "chunks": len(CHUNKS),
            "index_ready": MATRIX is not None
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.get("/analytics")
def get_analytics(authorization: Optional[str] = Header(None)):
    """Get analytics dashboard data."""
    try:
        # Verify token for security
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization token"
            )
        
        token = authorization[len("Bearer "):]
        verify_token(token)
        
        logger.info("Analytics dashboard requested")
        return analytics.get_stats()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

@app.get("/cache-stats")
def get_cache_stats(authorization: Optional[str] = Header(None)):
    """Get query cache performance statistics."""
    try:
        # Verify token for security
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization token"
            )
        
        token = authorization[len("Bearer "):]
        verify_token(token)
        
        logger.info("Cache statistics requested")
        stats = query_cache.get_stats()
        # Add explanatory message
        stats["description"] = f"Query cache reduces LLM calls by caching similar questions. Hit rate: {stats['hit_rate_percent']}%"
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache stats retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache stats")

@app.post("/auth/login", response_model=LoginResponse)
def login(req: LoginRequest):
    """Login endpoint with SHA256 password verification.
    
    Expects password hash: SHA256(password + 'Handbook')
    
    Demo credentials:
    - Username: Muthu
    - Password: AIApps@2026 (hash it with mod key 'Handbook')
    """
    logger.info(f"Login attempt for username: {req.username}")
    
    # Verify username
    if req.username != VALID_USERNAME:
        logger.warning(f"Login failed: Invalid username - {req.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Verify password hash
    if req.password_hash != VALID_PASSWORD_HASH:
        logger.warning(f"Login failed: Invalid password for user - {req.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Generate token
    token = generate_token()
    # Token expires in 2 hours
    expiry = datetime.now() + timedelta(hours=2)
    ACTIVE_TOKENS[token] = (req.username, expiry)
    
    logger.info(f"Login successful for user: {req.username}")
    
    # Track login in analytics
    analytics.track_login(req.username)
    
    return LoginResponse(
        success=True,
        token=token,
        message=f"Welcome, {req.username}!"
    )

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, authorization: Optional[str] = Header(None)):
    """Main endpoint: Answer regulatory questions using RAG (Retrieval-Augmented Generation).
    
    TWO-STAGE ARCHITECTURE
    ======================
    
    STAGE 1: RETRIEVAL
    -----------------
    1. Load question text from HTTP request
    2. Vectorize question using fitted TF-IDF VECTORIZER (same vocab as training)
    3. Compute cosine similarity against all chunks in MATRIX
    4. Rank chunks by similarity (0.0 = no match, 1.0 = perfect match)
    5. Filter out low-relevance chunks (threshold < 0.05)
    6. Select top_k chunks (default=3) as context
    7. Handle not-found case gracefully
    
    STAGE 2: GENERATION
    -------------------
    1. Format retrieved chunks with source attribution
    2. Pass question + chunks toAzure OpenAI LLM (gpt-4-turbo)
    3. LLM reads chunks and generates answer mentioning sources
    4. Extract citations from LLM response
    5. Format response with answer + citations + scores
    
    DATA FLOW
    =========
    
    HTTP Request
    ├─ question: "What is GDPR?"
    └─ top_k: 3
        ↓
    RETRIEVAL STAGE
    ├─ Vectorize question → TF-IDF vector
    ├─ Cosine similarity(qvector, MATRIX) → [0.543, 0.412, ...]
    ├─ Sort by score descending → [idx_1, idx_3, idx_2, ...]
    ├─ Filter score > 0.05 → [idx_1=0.543, idx_3=0.412, idx_2=0.298]
    ├─ Select top_k=3 → All three chunks
    └─ Extract chunks: [GDPR Art5, GDPR Art6, GDPR Art4]
        ↓
    GENERATION STAGE
    ├─ Format sources: "[GDPR | Art5]\ntext...\n\n[GDPR | Art6]\ntext..."
    ├─ Call LLM: {"question": "...", "sources": "..."}
    ├─ LLM returns: "GDPR is Regulation... [Citations: Article 5, Article 6]"
    └─ Parse answer and citations
        ↓
    HTTP Response
    ├─ answer: "GDPR is... [Citations: Article 5, Article 6]"
    ├─ citations: [{"doc": "GDPR", "section": "Article 5"}, ...]
    └─ scores: [0.543, 0.412, 0.298]
    
    ARCHITECTURE PRINCIPLES
    =======================
    
    1. SEPARATION OF CONCERNS
       - Retrieval: TF-IDF cosine similarity (this function)
       - Generation: LLM in llm.py (call_llm)
       - Validation: Pydantic models (requests/responses)
       - Data: load_chunks() parses data.txt
    
    2. ERROR HANDLING STRATEGY
       - Input validation: Pydantic checks question length
       - System validation: Check CHUNKS and MATRIX are initialized
       - Similarity filtering: Reject low-confidence retrievals
       - LLM error handling: Graceful error messages
    
    3. TRANSPARENCY & CITATIONS
       - All answers cite their sources (citations list)
       - Relevance scores show retrieval confidence
       - Sources formatted clearly for debugging
    
    Args:
        req (AskRequest): HTTP request with:
            - question: Regulatory question (5-1000 chars)
            - top_k: Number of sources to retrieve (1-10, default 3)
        
    Returns:
        AskResponse: HTTP response with:
            - answer: LLM-generated answer text + citations
            - citations: List of source documents and sections
            - scores: Similarity scores for each source
              
    Raises:
        HTTPException 503: Service not initialized (data/index missing)
        HTTPException 502: LLM service error (Azure OpenAI unavailable)
        HTTPException 500: Unexpected processing error
    """
    try:
        # ====== AUTHENTICATION PHASE ======
        # Verify Authorization token
        if not authorization:
            logger.warning("Request without authorization token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization token"
            )
        
        # Extract token from "Bearer <token>" format
        if not authorization.startswith("Bearer "):
            logger.warning("Invalid authorization header format")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )
        
        token = authorization[len("Bearer "):]
        username = verify_token(token)
        logger.info(f"Request authenticated for user: {username}")
        
        logger.info(f"Processing question: {req.question[:100]}...")
        logger.debug(f"Request parameters - top_k: {req.top_k}")
        
        # Track query start time for analytics
        query_start_time = datetime.now()
        
        # ====== VALIDATION PHASE ======
        # Ensure system is fully initialized before processing
        if not CHUNKS:
            logger.error("No data chunks available")
            raise HTTPException(status_code=503, detail="Service not initialized: no data loaded")
        
        if VECTORIZER is None or MATRIX is None:
            logger.error("Retrieval index not available")
            raise HTTPException(status_code=503, detail="Service not initialized: index not built")
        
        # ====== RETRIEVAL PHASE ======
        # Convert question to TF-IDF vector and find similar chunks
        logger.debug("Transforming query and computing similarities")
        # VECTORIZER.transform() uses fitted vocabulary from CHUNKS
        # Output: qvector has same dimensions as MATRIX columns (term weights)
        qvector = VECTORIZER.transform([req.question])
        
        # cosine_similarity computes: qvector · chunk_vector / (||qvector|| * ||chunk_vector||)
        # Output: sims array with scores for each chunk (0.0 = no match, 1.0 = perfect match)
        sims = cosine_similarity(qvector, MATRIX).flatten()
        
        # argsort() returns indices that would sort the array
        # [::-1] reverses to descending order (highest similarity first)
        sorted_indices = sims.argsort()[::-1]
        
        # MULTILINGUAL FILTERING
        # If user specified a language preference, filter chunks by language
        # This enables language-aware retrieval for multilingual queries
        if req.language and req.language != "en":
            logger.info(f"Filtering for language: {req.language}")
            # Keep all indices, but prioritize chunks in the requested language
            # First get language-matching chunks, then fall back to English if needed
            lang_matching_indices = [i for i in sorted_indices 
                                    if i < len(CHUNKS) and CHUNKS[i].get("language") == req.language]
            english_indices = [i for i in sorted_indices 
                              if i < len(CHUNKS) and CHUNKS[i].get("language", "en") == "en"]
            # Combine: language matches first, then English fallback
            sorted_indices = lang_matching_indices + [i for i in english_indices if i not in lang_matching_indices]
            logger.debug(f"Language filtering complete: {len(lang_matching_indices)} {req.language} chunks, {len(english_indices)} english chunks")
        
        # Filter to chunks with similarity > 0.05 (removes noise/weak matches)
        # Then take top_k from the filtered list
        idxs = [i for i in sorted_indices if sims[i] > 0.05][:req.top_k]
        
        # Get best similarity score for logging
        best_score = float(sims[idxs[0]]) if len(idxs) else 0.0
        logger.info(f"Retrieved {len(idxs)} chunks, best score: {best_score:.4f}")
        
        # ====== FILTERING PHASE ======
        # Reject queries with no meaningful matches (prevents hallucination)
        if best_score < 0.05 or not idxs:
            logger.info("Query not found in sources (similarity < 0.05), returning NOT FOUND")
            return {
                "answer": "NOT FOUND IN SOURCES.",
                "citations": [],
                "scores": []
            }

        # ====== FORMATTING PHASE ======
        # Prepare retrieved chunks with metadata for LLM context
        sources_blocks = []
        citations = []
        scores = []

        for idx in idxs:
            chunk = CHUNKS[int(idx)]
            score = float(sims[int(idx)])
            
            # Format source block: [DOCUMENT | SECTION]\ntext
            # Include language code in context if multilingual
            lang_info = f" [{chunk.get('language', 'en').upper()}]" if chunk.get('language', 'en') != 'en' else ""
            source_block = f"[{chunk['doc']} | {chunk['section']}{lang_info}]\n{chunk['text'].strip()}"
            sources_blocks.append(source_block)
            
            # Track citation metadata (document + section)
            citations.append({"doc": chunk["doc"], "section": chunk["section"]})
            
            # Store similarity score for response transparency
            scores.append(score)
            logger.debug(f"Retrieved: {chunk['doc']} - {chunk['section']} (score: {score:.4f})")

        # Join all source blocks with spacing for clarity
        sources_text = "\n\n".join(sources_blocks)
        logger.info(f"Prepared {len(citations)} sources for LLM, total chars: {len(sources_text)}")

        # ====== CACHE CHECK PHASE ======
        # Check if this question was recently answered (avoid redundant LLM calls)
        cached_response = query_cache.get(req.question)
        if cached_response:
            logger.info(f"Cache hit for query (savings: ~{query_cache.get_stats()['hits']} queries)")
            llm_answer = cached_response["answer"]
            cache_hit = True
        else:
            cache_hit = False
            # ====== GENERATION PHASE ======
            # Send question + retrieved sources to Azure OpenAI LLM for answer generation
            logger.debug(f"Calling LLM with question + {len(citations)} source chunks")
            try:
                # call_llm() takes question and sources, returns answer string
                # LLM will read sources and generate answer that cites them
                # (see llm.py for configuration details)
                llm_answer = call_llm(req.question, sources_text)
                logger.info("LLM answer generated successfully")
                
                # Cache the response for future similar queries
                query_cache.set(req.question, llm_answer, citations, scores)
            except Exception as llm_error:
                logger.error(f"LLM call failed: {str(llm_error)}")
                raise HTTPException(
                    status_code=502,
                    detail=f"LLM service error: {str(llm_error)}"
                )

        # ====== RESPONSE FORMATTING ======
        # Structure response according to AskResponse model (API contract)
        response = {
            "answer": llm_answer,      # String with full answer + citations
            "citations": citations,     # List of source documents/sections
            "scores": scores            # Similarity scores (relevance confidence)
        }
        
        # Track query in analytics
        query_duration = (datetime.now() - query_start_time).total_seconds()
        regulations_used = [f"{c['doc']} | {c['section']}" for c in citations]
        analytics.track_query(
            question=req.question,
            response_time=query_duration,
            success=True,
            regulations_used=regulations_used
        )
        
        cache_status = "CACHE HIT ✓" if cache_hit else f"LLM call ({query_duration:.2f}s)"
        logger.info(f"Returning response with {len(citations)} citations ({cache_status}) - {query_cache.get_stats()['hit_rate_percent']}% cache rate")
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions (already have proper status codes)
        raise
    except Exception as e:
        # Track failed query in analytics
        query_duration = (datetime.now() - query_start_time).total_seconds()
        analytics.track_query(
            question=req.question,
            response_time=query_duration,
            success=False
        )
        logger.error(f"Unexpected error in /ask endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
