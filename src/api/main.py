"""FastAPI application for EU Banking Regulator LLM system."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.models import (
    QueryRequest,
    QueryResponse,
    ComplianceCheckRequest,
    ComplianceCheckResponse,
    DocumentIngestionRequest,
    DocumentIngestionResponse
)
from src.services.rag_service import get_rag_service
from src.services.document_service import get_ingestion_service
from src.services.vector_db_service import get_vector_db_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("Starting EU Banking Regulator LLM API...")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"LLM Model: {settings.llm_model}")
    
    # Initialize services (lazy initialization)
    try:
        _ = get_vector_db_service()
        logger.info("Vector database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize vector database: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down EU Banking Regulator LLM API...")


# Create FastAPI app
app = FastAPI(
    title="EU Banking Regulator LLM API",
    description="API for querying EU banking regulations using LLM and RAG",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "EU Banking Regulator LLM API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        vector_db = get_vector_db_service()
        stats = vector_db.get_collection_stats()
        
        return {
            "status": "healthy",
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model,
            "vector_db": stats
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/api/query", response_model=QueryResponse)
async def query_regulations(request: QueryRequest) -> QueryResponse:
    """Query EU banking regulations."""
    try:
        logger.info(f"Received query: {request.question}")
        rag_service = get_rag_service()
        response = await rag_service.answer_query(request)
        logger.info(f"Query processed with confidence: {response.confidence}")
        return response
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.post("/api/compliance/check", response_model=ComplianceCheckResponse)
async def check_compliance(request: ComplianceCheckRequest) -> ComplianceCheckResponse:
    """Check compliance of a scenario against EU banking regulations."""
    try:
        logger.info(f"Received compliance check request")
        rag_service = get_rag_service()
        response = await rag_service.check_compliance(request)
        logger.info(f"Compliance check completed with status: {response.status}")
        return response
    except Exception as e:
        logger.error(f"Error checking compliance: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error checking compliance: {str(e)}"
        )


@app.post("/api/documents/ingest", response_model=DocumentIngestionResponse)
async def ingest_document(request: DocumentIngestionRequest) -> DocumentIngestionResponse:
    """Ingest a regulatory document into the knowledge base."""
    try:
        logger.info(f"Received document ingestion request: {request.file_path}")
        ingestion_service = get_ingestion_service()
        response = ingestion_service.ingest_document(request)
        
        if response.success:
            logger.info(
                f"Document ingested successfully: {response.document_id} "
                f"({response.chunks_created} chunks)"
            )
        else:
            logger.warning(f"Document ingestion failed: {response.message}")
        
        return response
    except Exception as e:
        logger.error(f"Error ingesting document: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error ingesting document: {str(e)}"
        )


@app.get("/api/documents/stats")
async def get_document_stats():
    """Get statistics about ingested documents."""
    try:
        vector_db = get_vector_db_service()
        stats = vector_db.get_collection_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting document stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document stats: {str(e)}"
        )


@app.delete("/api/documents/clear")
async def clear_documents():
    """Clear all documents from the knowledge base."""
    try:
        logger.warning("Received request to clear all documents")
        vector_db = get_vector_db_service()
        vector_db.clear_collection()
        logger.info("All documents cleared successfully")
        return {"message": "All documents cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing documents: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
