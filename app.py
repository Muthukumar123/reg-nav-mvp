"""
Regulation Navigator MVP - FastAPI Application

A Retrieval-Augmented Generation (RAG) system that answers regulatory compliance
questions using document retrieval and Azure OpenAI LLM integration.

Key Features:
- TF-IDF based retrieval of relevant regulatory documents
- Azure OpenAI LLM for generating source-based answers
- Comprehensive logging and exception handling
- Interactive Swagger/ReDoc API documentation
- Citation tracking for answer transparency
"""

import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from llm import call_llm

# Configure structured logging with timestamp, logger name, and level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application with title for OpenAPI documentation
app = FastAPI(title="Regulation Navigator MVP")

# ============================================================================
# DATA LOADING & INITIALIZATION
# ============================================================================

def load_chunks(path="data.txt"):
    """Load and parse regulatory document chunks from data file.
    
    Reads a text file containing structured regulatory documents and extracts
    chunks with metadata. Each chunk is identified by a [DOC] header with format:
    [DOC] DOCUMENT_NAME | SECTION_NAME
    
    Only chunks with text longer than 30 characters are retained to avoid empties.
    
    Args:
        path (str): Path to the data file. Default: "data.txt"
        
    Returns:
        list: List of chunk dictionaries with keys:
              - 'doc' (str): Document identifier
              - 'section' (str): Section/article name
              - 'text' (str): Chunk content text
              
    Raises:
        FileNotFoundError: If the data file doesn't exist
        Exception: For other file reading errors
    """
    try:
        logger.info(f"Loading chunks from {path}")
        chunks = []
        current = None

        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue

                if line.startswith("[DOC]"):
                    # Save previous chunk if exists
                    if current:
                        chunks.append(current)

                    # Parse header: [DOC] DOC_NAME | SECTION_NAME
                    header = line[len("[DOC]"):].strip()
                    parts = [p.strip() for p in header.split("|")]
                    doc = parts[0] if len(parts) > 0 else "UNKNOWN_DOC"
                    section = parts[1] if len(parts) > 1 else "UNKNOWN_SECTION"
                    # Initialize new chunk with metadata and empty text
                    current = {"doc": doc, "section": section, "text": ""}
                else:
                    # Append content to current chunk
                    if current:
                        current["text"] += line + " "

        # Don't forget the last chunk
        if current:
            chunks.append(current)

        # Filter out chunks with minimal text (< 30 chars) to avoid noise
        filtered_chunks = [c for c in chunks if len(c["text"]) > 30]
        logger.info(f"Loaded {len(filtered_chunks)} chunks from {path}")
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

# ---------- Build a simple retrieval index ----------
try:
    # Initialize TF-IDF vectorizer with English stop words filtered out
    # TF-IDF converts text into numeric vectors for efficient similarity matching
    VECTORIZER = TfidfVectorizer(stop_words="english")
    # fit_transform() learns vocabulary and creates sparse matrix (memory efficient)
    MATRIX = VECTORIZER.fit_transform([c["text"] for c in CHUNKS])
    logger.info(f"Built TF-IDF index with shape {MATRIX.shape}")
except Exception as e:
    logger.critical(f"Failed to build retrieval index: {str(e)}")
    VECTORIZER = None
    MATRIX = None

class AskRequest(BaseModel):
    """Request model for the /ask endpoint.
    
    Attributes:
        question (str): The regulatory compliance question to answer.
                       Will be converted to TF-IDF vectors for similarity matching.
        top_k (int): Number of document chunks to retrieve for context (default: 3).
                    More chunks increase context but may dilute answer quality.
    """
    question: str  # Required field - the user's regulatory question
    top_k: int = 3  # Optional field - controls retrieval scope

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
            "/health": "Health check endpoint",
            "/ask": "POST - Ask regulatory questions",
            "/docs": "Interactive API documentation (Swagger UI)",
            "/redoc": "Alternative API documentation (ReDoc)"
        },
        "status": "running"
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

@app.post("/ask")
def ask(req: AskRequest):
    """Answer regulatory questions using Retrieval-Augmented Generation (RAG).
    
    Main request processing pipeline:
    1. Validate system initialization (data loaded, index built)
    2. Convert user question to TF-IDF vector
    3. Compute cosine similarity with all document chunks
    4. Filter irrelevant queries using 0.12 similarity threshold
    5. Retrieve top-k most relevant chunks from documents
    6. Format source documents and send to Azure OpenAI LLM
    7. Return LLM-generated answer with citations and scores
    
    Args:
        req (AskRequest): Request containing question and top_k parameters
        
    Returns:
        dict: Response containing:
              - answer (str): LLM-generated answer with inline citations
              - citations (list): Documents and sections used as sources
              - scores (list): Cosine similarity scores for each source
              
    Raises:
        HTTPException:
            - 503: Service not initialized (no data or index)
            - 502: LLM service error (Azure OpenAI issue)
            - 500: Unexpected processing error
    """
    try:
        logger.info(f"Processing question: {req.question[:100]}...")
        logger.debug(f"Request parameters - top_k: {req.top_k}")
        
        # Validate system initialization before processing
        if not CHUNKS:
            logger.error("No data chunks available")
            raise HTTPException(status_code=503, detail="Service not initialized: no data loaded")
        
        if VECTORIZER is None or MATRIX is None:
            logger.error("Retrieval index not available")
            raise HTTPException(status_code=503, detail="Service not initialized: index not built")
        
        # RETRIEVAL PHASE: Convert question to TF-IDF vector and rank documents
        logger.debug("Transforming query and computing similarities")
        # Transform question using fitted vectorizer vocabulary
        qv = VECTORIZER.transform([req.question])
        # Compute cosine similarity between query and all chunks (0-1 scale)
        sims = cosine_similarity(qv, MATRIX).flatten()
        # Get indices of top-k chunks sorted by similarity (descending)
        idxs = sims.argsort()[::-1][: max(1, req.top_k)]

        # Extract best similarity score for relevance filtering
        best_score = float(sims[idxs[0]]) if len(idxs) else 0.0
        logger.info(f"Best similarity score: {best_score:.4f}")
        
        # FILTERING PHASE: Check relevance threshold (0.12) to avoid spurious answers
        # Threshold prevents the LLM from generating answers for questions
        # that are not related to regulatory documents at all
        if best_score < 0.12:
            logger.info("Query below relevance threshold, returning NOT FOUND")
            return {
                "answer": "NOT FOUND IN SOURCES.",
                "citations": [],
                "scores": []
            }

        # FORMATTING PHASE: Build source context for LLM
        # Organize retrieved chunks with metadata for clear attribution
        sources_blocks = []
        citations = []
        scores = []

        # Iterate through top-k chunks in ranking order
        for i in idxs:
            c = CHUNKS[int(i)]
            score = float(sims[int(i)])
            # Format as: [DOC_NAME | SECTION]\nCHUNK_TEXT
            sources_blocks.append(f"[{c['doc']} | {c['section']}]\n{c['text'].strip()}")
            # Track which sources are used for citation
            citations.append({"doc": c["doc"], "section": c["section"]})
            # Store similarity score for transparency
            scores.append(score)
            logger.debug(f"Retrieved: {c['doc']} - {c['section']} (score: {score:.4f})")

        # Concatenate all source blocks with spacing for clarity
        sources_text = "\n\n".join(sources_blocks)
        logger.info(f"Calling LLM with {len(citations)} source chunks")

        # LLM PHASE: Send question + sources to Azure OpenAI for answer generation
        try:
            llm_answer = call_llm(req.question, sources_text)
            logger.info("LLM call successful")
        except Exception as llm_error:
            logger.error(f"LLM call failed: {str(llm_error)}")
            raise HTTPException(
                status_code=502,
                detail=f"LLM service error: {str(llm_error)}"
            )

        return {
            "answer": llm_answer,
            "citations": citations,
            "scores": scores
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /ask endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
