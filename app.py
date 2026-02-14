import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from llm import call_llm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Regulation Navigator MVP")

# ---------- Load + parse data.txt ----------
def load_chunks(path="data.txt"):
    """Load and parse regulatory document chunks from data file."""
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
                    if current:
                        chunks.append(current)

                    header = line[len("[DOC]"):].strip()
                    parts = [p.strip() for p in header.split("|")]
                    doc = parts[0] if len(parts) > 0 else "UNKNOWN_DOC"
                    section = parts[1] if len(parts) > 1 else "UNKNOWN_SECTION"
                    current = {"doc": doc, "section": section, "text": ""}
                else:
                    if current:
                        current["text"] += line + " "

        if current:
            chunks.append(current)

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
    VECTORIZER = TfidfVectorizer(stop_words="english")
    MATRIX = VECTORIZER.fit_transform([c["text"] for c in CHUNKS])
    logger.info(f"Built TF-IDF index with shape {MATRIX.shape}")
except Exception as e:
    logger.critical(f"Failed to build retrieval index: {str(e)}")
    VECTORIZER = None
    MATRIX = None

class AskRequest(BaseModel):
    question: str
    top_k: int = 3

@app.get("/")
def root():
    """Root endpoint with API information."""
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
    """Answer regulatory questions using retrieval and LLM."""
    try:
        logger.info(f"Processing question: {req.question[:100]}...")
        logger.debug(f"Request parameters - top_k: {req.top_k}")
        
        # Validate prerequisites
        if not CHUNKS:
            logger.error("No data chunks available")
            raise HTTPException(status_code=503, detail="Service not initialized: no data loaded")
        
        if VECTORIZER is None or MATRIX is None:
            logger.error("Retrieval index not available")
            raise HTTPException(status_code=503, detail="Service not initialized: index not built")
        
        # Retrieve top_k chunks
        logger.debug("Transforming query and computing similarities")
        qv = VECTORIZER.transform([req.question])
        sims = cosine_similarity(qv, MATRIX).flatten()
        idxs = sims.argsort()[::-1][: max(1, req.top_k)]

        best_score = float(sims[idxs[0]]) if len(idxs) else 0.0
        logger.info(f"Best similarity score: {best_score:.4f}")
        
        if best_score < 0.12:
            logger.info("Query below relevance threshold, returning NOT FOUND")
            return {
                "answer": "NOT FOUND IN SOURCES.",
                "citations": [],
                "scores": []
            }

        # Build sources text for the LLM
        sources_blocks = []
        citations = []
        scores = []

        for i in idxs:
            c = CHUNKS[int(i)]
            score = float(sims[int(i)])
            sources_blocks.append(f"[{c['doc']} | {c['section']}]\n{c['text'].strip()}")
            citations.append({"doc": c["doc"], "section": c["section"]})
            scores.append(score)
            logger.debug(f"Retrieved: {c['doc']} - {c['section']} (score: {score:.4f})")

        sources_text = "\n\n".join(sources_blocks)
        logger.info(f"Calling LLM with {len(citations)} source chunks")

        # Call the LLM with ONLY the retrieved sources
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
