"""
HTTP API adapter - presentation layer.

Converts HTTP requests/responses to domain concepts.
Separates FastAPI concerns from business logic.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Security, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field

from core.entities import ComplianceQuestion, ComplianceAnswer
from core.auth_interface import AuthCredentials, AuthToken, AuthUser, AuthenticationService
from application.compliance_service import ComplianceService

logger = logging.getLogger(__name__)

# ==================== Pydantic Models ====================
# These are HTTP request/response contracts (not domain entities)

class QuestionRequest(BaseModel):
    """HTTP request model for compliance question."""
    question: str = Field(..., min_length=5, max_length=500)
    top_k: int = Field(default=3, ge=1, le=10)
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What are the main data protection requirements?",
                "top_k": 3
            }
        }


class CitationResponse(BaseModel):
    """HTTP response model for citation."""
    doc: str
    section: str


class AnswerResponse(BaseModel):
    """HTTP response model for compliance answer."""
    answer: str
    citations: List[CitationResponse]
    scores: List[float]
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Article 5 of GDPR establishes principles for data processing...",
                "citations": [
                    {"doc": "GDPR", "section": "Article 5"}
                ],
                "scores": [0.456]
            }
        }


# ==================== Authentication Models ====================

class LoginRequest(BaseModel):
    """HTTP request model for login."""
    username: str = Field(..., min_length=5, description="Email or username")
    password: str = Field(..., min_length=8, description="Password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "demo@example.com",
                "password": "demo-password-12345"
            }
        }


class TokenResponse(BaseModel):
    """HTTP response model for authentication token."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int  # Seconds
    user_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 1800,
                "user_id": "user_1"
            }
        }


class UserResponse(BaseModel):
    """HTTP response model for user info."""
    user_id: str
    username: str
    roles: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_1",
                "username": "demo@example.com",
                "roles": ["user"]
            }
        }


# ==================== HTTP API Adapter ====================

class HTTPComplianceAPI:
    """Adapts HTTP requests to domain concepts.
    
    - Single Responsibility: Only converts between HTTP and domain
    - Dependency Inversion: Depends on ComplianceService interface
    - Separation: HTTP concerns (status codes, validation) isolated from business logic
    - Testable: Can test routes independently using FastAPI TestClient
    """
    
    def __init__(
        self,
        compliance_service: ComplianceService,
        auth_service: Optional[AuthenticationService] = None
    ):
        """Initialize with injected services.
        
        Args:
            compliance_service: The orchestration layer
            auth_service: Optional authentication service
        """
        self.service = compliance_service
        self.auth_service = auth_service
        self.router = APIRouter(
            prefix="/api/compliance",
            tags=["compliance"],
            responses={
                400: {"description": "Invalid request"},
                500: {"description": "Internal server error"}
            }
        )
        self.auth_router = APIRouter(
            prefix="/api/auth",
            tags=["authentication"]
        ) if auth_service else None
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Register HTTP routes."""
        # Compliance endpoint
        self.router.add_api_route(
            "/ask",
            self.ask_question,
            methods=["POST"],
            response_model=AnswerResponse,
            summary="Ask a compliance question",
            description="Ask a question about regulations and receive cited answers"
        )
        
        # Auth endpoints (if auth service available)
        if self.auth_service and self.auth_router:
            self.auth_router.add_api_route(
                "/login",
                self.login,
                methods=["POST"],
                response_model=TokenResponse,
                summary="Login with credentials",
                description="Authenticate with username/password and get JWT token"
            )
            
            self.auth_router.add_api_route(
                "/me",
                self.get_current_user,
                methods=["GET"],
                response_model=UserResponse,
                summary="Get current user info",
                description="Get information about the currently authenticated user"
            )
            
            self.auth_router.add_api_route(
                "/refresh",
                self.refresh_token,
                methods=["POST"],
                response_model=TokenResponse,
                summary="Refresh access token",
                description="Get a new access token using a refresh token"
            )
    
    async def ask_question(self, request: QuestionRequest) -> AnswerResponse:
        """Answer a compliance question via HTTP.
        
        Args:
            request: HTTP request with question and top_k
            
        Returns:
            HTTP response with answer and citations
            
        Raises:
            HTTPException: If question is invalid or service fails
        """
        logger.info(f"HTTP request: {request.question[:100]}...")
        
        try:
            # Convert HTTP request to domain entity
            domain_question = ComplianceQuestion(
                question=request.question,
                top_k=request.top_k
            )
            
            # Call business logic
            domain_answer: ComplianceAnswer = self.service.answer_question(domain_question)
            
            # Convert domain response to HTTP response
            citations = [
                CitationResponse(doc=c.doc, section=c.section)
                for c in domain_answer.citations
            ]
            
            http_response = AnswerResponse(
                answer=domain_answer.answer,
                citations=citations,
                scores=domain_answer.scores
            )
            
            logger.info(f"HTTP response: {len(citations)} citations, score={domain_answer.scores[0] if domain_answer.scores else 0:.3f}")
            
            return http_response
            
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        
        except RuntimeError as e:
            logger.error(f"Service error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
    # ==================== Authentication Endpoints ====================
    
    async def login(self, request: LoginRequest) -> TokenResponse:
        """Authenticate user and return JWT token.
        
        Args:
            request: Login credentials
            
        Returns:
            JWT access token
            
        Raises:
            HTTPException: If credentials invalid
        """
        if not self.auth_service:
            raise HTTPException(status_code=401, detail="Authentication not enabled")
        
        logger.info(f"Login attempt: {request.username}")
        
        try:
            credentials = AuthCredentials(
                username=request.username,
                password=request.password
            )
            auth_token: AuthToken = self.auth_service.authenticate(credentials)
            
            logger.info(f"Login successful: {request.username}")
            
            return TokenResponse(
                access_token=auth_token.token,
                token_type=auth_token.token_type,
                expires_in=auth_token.expires_in,
                user_id=auth_token.user_id
            )
            
        except ValueError as e:
            logger.warning(f"Login failed - invalid credentials: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid username or password")
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise HTTPException(status_code=500, detail="Authentication service error")
    
    async def get_current_user(
        self,
        request: Request
    ) -> UserResponse:
        """Get current authenticated user information.
        
        Args:
            request: HTTP request object
            
        Returns:
            Currently authenticated user info
            
        Raises:
            HTTPException: If not authenticated
        """
        if not self.auth_service:
            raise HTTPException(status_code=401, detail="Authentication not enabled")
        
        # Extract Bearer token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            user: AuthUser = self.auth_service.verify_token(token)
            
            return UserResponse(
                user_id=user.user_id,
                username=user.username,
                roles=user.roles
            )
            
        except ValueError as e:
            logger.warning(f"Token verification failed: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        except Exception as e:
            logger.error(f"Verification error: {str(e)}")
            raise HTTPException(status_code=500, detail="Authentication service error")
    
    async def refresh_token(
        self,
        request: Request
    ) -> TokenResponse:
        """Refresh an access token.
        
        Args:
            request: HTTP request object with refresh token in Authorization header
            
        Returns:
            New access token
            
        Raises:
            HTTPException: If token invalid
        """
        if not self.auth_service:
            raise HTTPException(status_code=401, detail="Authentication not enabled")
        
        # Extract Bearer token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Refresh token required")
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            new_token: AuthToken = self.auth_service.refresh_token(token)
            
            return TokenResponse(
                access_token=new_token.token,
                token_type=new_token.token_type,
                expires_in=new_token.expires_in,
                user_id=new_token.user_id
            )
            
        except ValueError as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        except Exception as e:
            logger.error(f"Refresh error: {str(e)}")
            raise HTTPException(status_code=500, detail="Token refresh failed")
    
    # ==================== Routers ====================
    
    def get_router(self) -> APIRouter:
        """Get the router for FastAPI integration.
        
        Returns:
            APIRouter configured with compliance endpoints
        """
        return self.router
    
    def get_auth_router(self) -> Optional[APIRouter]:
        """Get the authentication router.
        
        Returns:
            APIRouter configured with auth endpoints (None if auth disabled)
        """
        return self.auth_router
