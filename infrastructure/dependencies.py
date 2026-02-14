"""
Dependency injection container - wiring and configuration.

Assembles all components following factory pattern and singleton pattern.
Centralizes infrastructure setup and configuration.
"""

import logging
import os
from pathlib import Path

from infrastructure.retrieval import TfidfRetrievalEngine
from infrastructure.data_loader import RegulatoryDocumentLoader
from infrastructure.llm_client import AzureOpenAIModel
from infrastructure.jwt_auth import JWTAuthenticationService, BcryptPasswordHasher
from application.compliance_service import ComplianceService
from adapters.http_api import HTTPComplianceAPI

logger = logging.getLogger(__name__)

# ==================== Configuration ====================

class ComplianceConfig:
    """Configuration for compliance service."""
    
    # Data source
    DATA_FILE: str = os.getenv("DATA_FILE", "data.txt")
    
    # Retrieval engine parameters
    RETRIEVAL_MIN_SIMILARITY: float = float(os.getenv("RETRIEVAL_MIN_SIMILARITY", "0.05"))
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "3"))
    
    # LLM parameters
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    
    # Azure credentials (from environment)
    # Note: llm_client.py expects AZURE_OPENAI_KEY, not AZURE_OPENAI_API_KEY
    AZURE_OPENAI_KEY: str = os.getenv("AZURE_OPENAI_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
    
    # Authentication settings
    AUTH_ENABLED: bool = os.getenv("AUTH_ENABLED", "false").lower() == "true"
    AUTH_SECRET_KEY: str = os.getenv("AUTH_SECRET_KEY", "dev-secret-key-change-in-production-min-32-chars--12345678901")
    AUTH_ALGORITHM: str = os.getenv("AUTH_ALGORITHM", "HS256")
    AUTH_ACCESS_TOKEN_EXPIRE: int = int(os.getenv("AUTH_ACCESS_TOKEN_EXPIRE", "30"))  # minutes
    AUTH_REFRESH_TOKEN_EXPIRE: int = int(os.getenv("AUTH_REFRESH_TOKEN_EXPIRE", "7"))  # days


# ==================== Singleton Container ====================

class ComplianceContainer:
    """Service container - singleton pattern.
    
    Demonstrates:
    - Singleton pattern: Services created once and reused
    - Factory pattern: create_* methods build components
    - Lazy initialization: Services built on-demand
    - Configurability: All parameters in one place
    
    Usage:
        container = ComplianceContainer()
        service = container.get_compliance_service()
        service.initialize("data.txt")
    """
    
    _instance = None
    _retrieval_engine = None
    _language_model = None
    _data_loader = None
    _service = None
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ComplianceContainer, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset singleton (for testing)."""
        cls._instance = None
        cls._retrieval_engine = None
        cls._language_model = None
        cls._data_loader = None
        cls._service = None
    
    def get_retrieval_engine(self) -> TfidfRetrievalEngine:
        """Get or create TF-IDF retrieval engine (singleton).
        
        Returns:
            TfidfRetrievalEngine configured with thresholds
        """
        if ComplianceContainer._retrieval_engine is None:
            logger.info("Creating TfidfRetrievalEngine")
            ComplianceContainer._retrieval_engine = TfidfRetrievalEngine(
                min_similarity_threshold=ComplianceConfig.RETRIEVAL_MIN_SIMILARITY
            )
        return ComplianceContainer._retrieval_engine
    
    def get_language_model(self) -> AzureOpenAIModel:
        """Get or create Azure OpenAI language model (singleton).
        
        Returns:
            AzureOpenAIModel configured with Azure credentials
            
        Raises:
            ValueError: If Azure credentials not configured
        """
        if ComplianceContainer._language_model is None:
            logger.info("Creating AzureOpenAIModel")
            
            # Validate Azure credentials
            if not all([
                ComplianceConfig.AZURE_OPENAI_KEY,
                ComplianceConfig.AZURE_OPENAI_ENDPOINT,
                ComplianceConfig.AZURE_OPENAI_DEPLOYMENT
            ]):
                raise ValueError(
                    "Azure OpenAI credentials not configured. "
                    "Set AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, "
                    "and AZURE_OPENAI_DEPLOYMENT environment variables."
                )
            
            # AzureOpenAIModel reads configuration from environment variables
            ComplianceContainer._language_model = AzureOpenAIModel()
        return ComplianceContainer._language_model
    
    def get_data_loader(self) -> RegulatoryDocumentLoader:
        """Get or create regulatory document loader (singleton).
        
        Returns:
            RegulatoryDocumentLoader
        """
        if ComplianceContainer._data_loader is None:
            logger.info("Creating RegulatoryDocumentLoader")
            ComplianceContainer._data_loader = RegulatoryDocumentLoader()
        return ComplianceContainer._data_loader
    
    def get_compliance_service(self) -> ComplianceService:
        """Get or create compliance service (singleton).
        
        Demonstrates Dependency Inversion:
        - Service depends on interfaces (RetrievalEngine, LanguageModel, DataLoader)
        - Concrete implementations injected via constructor
        - Easy to swap implementations without changing service
        
        Returns:
            ComplianceService with all dependencies injected
        """
        if ComplianceContainer._service is None:
            logger.info("Creating ComplianceService")
            
            ComplianceContainer._service = ComplianceService(
                retrieval_engine=self.get_retrieval_engine(),
                language_model=self.get_language_model(),
                data_loader=self.get_data_loader()
            )
        return ComplianceContainer._service
    
    def get_http_api(self) -> HTTPComplianceAPI:
        """Get HTTP API adapter.
        
        Returns:
            HTTPComplianceAPI with service injected
        """
        return HTTPComplianceAPI(self.get_compliance_service())
    
    def get_auth_service(self) -> JWTAuthenticationService:
        """Get or create JWT authentication service (singleton).
        
        Returns:
            JWTAuthenticationService configured with JWT settings
        """
        if not hasattr(ComplianceContainer, '_auth_service'):
            logger.info("Creating JWTAuthenticationService")
            ComplianceContainer._auth_service = JWTAuthenticationService(
                secret_key=ComplianceConfig.AUTH_SECRET_KEY,
                algorithm=ComplianceConfig.AUTH_ALGORITHM,
                access_token_expire_minutes=ComplianceConfig.AUTH_ACCESS_TOKEN_EXPIRE,
                refresh_token_expire_days=ComplianceConfig.AUTH_REFRESH_TOKEN_EXPIRE,
                password_hasher=BcryptPasswordHasher()
            )
            
            # Create default test user (development only!)
            if isinstance(ComplianceContainer._auth_service, JWTAuthenticationService):
                try:
                    ComplianceContainer._auth_service.create_user(
                        username="demo@example.com",
                        password="demo-password-12345",
                        roles=["user"]
                    )
                    logger.info("Demo user created for testing")
                except ValueError as e:
                    # User already exists
                    logger.debug(f"Demo user already exists: {str(e)}")
        
        return ComplianceContainer._auth_service


# ==================== Initialization Helper ====================

def initialize_compliance_service(data_source: str = None) -> ComplianceService:
    """Initialize compliance service with data.
    
    This is the primary initialization function for the application.
    
    Args:
        data_source: Path to regulatory data file
                    (defaults to ComplianceConfig.DATA_FILE)
    
    Returns:
        Initialized ComplianceService ready for use
        
    Raises:
        FileNotFoundError: If data file not found
        ValueError: If data is invalid
    """
    if data_source is None:
        data_source = ComplianceConfig.DATA_FILE
    
    # Validate data file exists
    if not Path(data_source).exists():
        raise FileNotFoundError(f"Data file not found: {data_source}")
    
    logger.info(f"Initializing compliance service from {data_source}")
    
    # Get singleton container
    container = ComplianceContainer()
    
    # Get service
    service = container.get_compliance_service()
    
    # Initialize with data
    service.initialize(data_source)
    
    logger.info("Compliance service initialized successfully")
    
    return service
