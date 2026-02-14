"""
Authentication interfaces - core contracts.

Defines authentication service contracts following SOLID principles.
Separates authentication concerns from business logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthToken:
    """Authentication token representation.
    
    Immutable value object representing an issued token.
    """
    token: str          # JWT token or similar
    token_type: str     # "Bearer", "Basic", etc
    expires_in: int     # Seconds until expiration
    user_id: str        # Associated user ID
    
    def __post_init__(self):
        if not self.token or len(self.token) < 10:
            raise ValueError("Invalid token")
        if self.expires_in < 0:
            raise ValueError("Token expiration must be positive")


@dataclass
class AuthCredentials:
    """User credentials for authentication.
    
    Value object representing login credentials.
    """
    username: str       # User email or username
    password: str       # User password
    
    def __post_init__(self):
        if not self.username or not self.password:
            raise ValueError("Username and password required")


@dataclass
class AuthUser:
    """Authenticated user information.
    
    Value object representing an authenticated user.
    """
    user_id: str        # Unique user ID
    username: str       # User email or username
    roles: list         # List of roles (["admin", "user"])
    
    def __post_init__(self):
        if not self.user_id or not self.username:
            raise ValueError("User ID and username required")
    
    def has_role(self, role: str) -> bool:
        """Check if user has role."""
        return role in self.roles


class AuthenticationService(ABC):
    """Abstract authentication service.
    
    Contract for authentication implementations.
    Supports different auth methods: JWT, OAuth2, API keys, etc.
    
    SOLID:
    - Single Responsibility: Only handles authentication
    - Liskov Substitution: All implementations work the same
    - Dependency Inversion: Depends on this interface
    """
    
    @abstractmethod
    def authenticate(self, credentials: AuthCredentials) -> AuthToken:
        """Authenticate user with credentials.
        
        Args:
            credentials: Username/password or similar
            
        Returns:
            AuthToken with JWT or similar
            
        Raises:
            ValueError: If credentials invalid
            RuntimeError: If service fails
        """
        raise NotImplementedError
    
    @abstractmethod
    def verify_token(self, token: str) -> AuthUser:
        """Verify and decode authentication token.
        
        Args:
            token: The token to verify
            
        Returns:
            AuthUser if valid
            
        Raises:
            ValueError: If token invalid or expired
            RuntimeError: If verification fails
        """
        raise NotImplementedError
    
    @abstractmethod
    def refresh_token(self, token: str) -> AuthToken:
        """Refresh an authentication token.
        
        Args:
            token: The token to refresh
            
        Returns:
            New AuthToken
            
        Raises:
            ValueError: If token invalid
            RuntimeError: If refresh fails
        """
        raise NotImplementedError
    
    @abstractmethod
    def create_user(self, username: str, password: str, roles: list = None) -> str:
        """Create a new user.
        
        Args:
            username: User email or username
            password: User password (will be hashed)
            roles: List of roles to assign
            
        Returns:
            User ID
            
        Raises:
            ValueError: If user invalid
            RuntimeError: If creation fails
        """
        raise NotImplementedError


class PasswordHasher(ABC):
    """Abstract password hashing service.
    
    Contract for password hashing implementations.
    Supports: bcrypt, argon2, scrypt, etc.
    """
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash a password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        raise NotImplementedError
    
    @abstractmethod
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash.
        
        Args:
            password: Plain text password to verify
            hashed: Previously hashed password
            
        Returns:
            True if password matches
        """
        raise NotImplementedError
