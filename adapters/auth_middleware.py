"""
FastAPI authentication decorator and security utilities.

Provides easy integration of authentication with FastAPI endpoints.
Handles Bearer token extraction and verification.
"""

import logging
from typing import Optional

from fastapi import HTTPException, Request

from core.auth_interface import AuthUser
from core.auth_interface import AuthenticationService

logger = logging.getLogger(__name__)


class FastAPIAuthAdapter:
    """FastAPI authentication adapter.
    
    Bridges authentication service with FastAPI dependency injection.
    Extracts and verifies Bearer tokens from HTTP headers.
    """
    
    def __init__(self, auth_service: AuthenticationService):
        """Initialize with authentication service.
        
        Args:
            auth_service: The authentication implementation
        """
        self.auth_service = auth_service
        logger.info("FastAPIAuthAdapter initialized")
    
    async def verify_bearer_token(
        self,
        request: Request
    ) -> AuthUser:
        """Verify Bearer token and return user.
        
        This method is used as a dependency in FastAPI routes.
        
        Args:
            request: HTTP request object
            
        Returns:
            AuthUser if token valid
            
        Raises:
            HTTPException: If token invalid or expired
            
        Example:
            from depends import auth_adapter
            
            @app.get("/protected")
            async def protected_route(user: AuthUser = Depends(auth_adapter.verify_bearer_token)):
                return {"message": f"Hello {user.username}"}
        """
        # Extract Bearer token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            logger.debug("Verifying bearer token")
            user = self.auth_service.verify_token(token)
            logger.info(f"Bearer token verified for user: {user.username}")
            return user
            
        except ValueError as e:
            logger.warning(f"Bearer token verification failed: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            logger.error(f"Bearer token verification error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Authentication service error",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    async def verify_bearer_token_optional(
        self,
        credentials: Optional[HTTPAuthCredentials] = Security(security, scopes=[])
    ) -> Optional[AuthUser]:
        """Verify Bearer token - optional (may be None).
        
        For endpoints that work with or without authentication.
        
        Args:
            credentials: HTTP Bearer credentials (optional)
            
        Returns:
            AuthUser if token provided and valid, None otherwise
        """
        if not credentials:
            logger.debug("No credentials provided (optional auth)")
            return None
        
        try:
            return self.auth_service.verify_token(credentials.credentials)
        except Exception:
            # For optional auth, just return None instead of raising
            return None
    
    def require_role(self, required_role: str):
        """Create a dependency that requires specific role.
        
        Args:
            required_role: Role required to access endpoint
            
        Returns:
            Dependency function
            
        Example:
            from depends import auth_adapter
            
            @app.delete("/admin/questions")
            async def admin_delete(user: AuthUser = Depends(auth_adapter.require_role("admin"))):
                return {"message": "Deleted"}
        """
        async def check_role(user: AuthUser = Depends(self.verify_bearer_token)) -> AuthUser:
            if not user.has_role(required_role):
                logger.warning(f"User {user.username} lacks required role: {required_role}")
                raise HTTPException(
                    status_code=403,
                    detail=f"This endpoint requires '{required_role}' role"
                )
            return user
        
        return check_role


class AuthorizationError(Exception):
    """Authorization error (403 Forbidden)."""
    pass


class AuthenticationError(Exception):
    """Authentication error (401 Unauthorized)."""
    pass
