"""
Refactored FastAPI application using clean architecture.

Shows how layered, SOLID-compliant code integrates with FastAPI.
All business logic isolated in application and infrastructure layers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from infrastructure.dependencies import (
    initialize_compliance_service, ComplianceContainer, ComplianceConfig
)
from adapters.http_api import HTTPComplianceAPI

# ==================== Logging Setup ====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== Application Lifecycle ====================

compliance_service = None
compliance_api = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup/shutdown.
    
    Demonstrates:
    - Startup: Initialize all services and load data
    - Shutdown: Cleanup resources
    - Dependency management: One initialization point
    """
    # ===== STARTUP =====
    global compliance_service, compliance_api
    
    logger.info("FastAPI application starting up...")
    
    try:
        # Initialize compliance service
        compliance_service = initialize_compliance_service(ComplianceConfig.DATA_FILE)
        
        # Create HTTP API adapter with authentication
        container = ComplianceContainer()
        
        # Initialize auth service if enabled
        if ComplianceConfig.AUTH_ENABLED:
            try:
                auth_service = container.get_auth_service()
                logger.info("Authentication enabled")
            except Exception as e:
                logger.warning(f"Auth service initialization failed, continuing without auth: {str(e)}")
                auth_service = None
        else:
            auth_service = None
            logger.info("Authentication disabled")
        
        # Create HTTP API adapter (with auth if available)
        compliance_api = HTTPComplianceAPI(
            compliance_service=compliance_service,
            auth_service=auth_service
        )
        
        # Mount routers after API is initialized
        app.include_router(compliance_api.get_router())
        logger.info("Compliance router mounted at /api/compliance")
        
        auth_router = compliance_api.get_auth_router()
        if auth_router and ComplianceConfig.AUTH_ENABLED and auth_service:
            app.include_router(auth_router)
            logger.info("Authentication router mounted at /api/auth")
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise
    
    yield
    
    # ===== SHUTDOWN =====
    logger.info("FastAPI application shutting down...")
    ComplianceContainer.reset()
    logger.info("Application shutdown complete")


# ==================== FastAPI Application ====================

app = FastAPI(
    title="Compliance Q&A API",
    description="RAG system for regulatory compliance questions",
    version="2.0",
    lifespan=lifespan
)

# ==================== CORS Configuration ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Routes ====================

@app.get("/health", tags=["health"])
async def health() -> dict:
    """Health check endpoint.
    
    Returns:
        Service status
    """
    return {
        "status": "healthy",
        "service": "compliance-qa",
        "version": "2.0",
        "auth_enabled": ComplianceConfig.AUTH_ENABLED
    }


@app.get("/info", tags=["info"])
async def info() -> dict:
    """Service information endpoint.
    
    Returns:
        Configuration and data statistics
    """
    if compliance_service is None:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    info_dict = {
        "service": "Regulatory Compliance Q&A",
        "version": "2.0",
        "architecture": "Clean Architecture with SOLID Principles",
        "data_file": ComplianceConfig.DATA_FILE,
        "retrieval_min_similarity": ComplianceConfig.RETRIEVAL_MIN_SIMILARITY,
        "llm_model": ComplianceConfig.LLM_MODEL,
        "llm_temperature": ComplianceConfig.LLM_TEMPERATURE,
        "auth_enabled": ComplianceConfig.AUTH_ENABLED
    }
    
    return info_dict


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler.
    
    Formats errors consistently across all endpoints.
    """
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "detail": exc.detail
        }
    )


# ==================== Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Compliance Q&A API...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
