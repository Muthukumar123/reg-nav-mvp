"""
JWT authentication implementation - infrastructure layer.

OAuth2 JWT-based authentication with password hashing.
Follows FastAPI security best practices.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from passlib.context import CryptContext

from core.auth_interface import (
    AuthenticationService, PasswordHasher, AuthToken, AuthCredentials, AuthUser
)

logger = logging.getLogger(__name__)


class BcryptPasswordHasher(PasswordHasher):
    """Bcrypt-based password hashing.
    
    Uses passlib with bcrypt for secure password storage.
    Single Responsibility: Only handles password hashing
    """
    
    def __init__(self):
        """Initialize bcrypt context."""
        self.crypt_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto"
        )
        logger.info("BcryptPasswordHasher initialized")
    
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Bcrypt hash
        """
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        return self.crypt_context.hash(password)
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against bcrypt hash.
        
        Args:
            password: Plain text password to check
            hashed: Bcrypt hash to check against
            
        Returns:
            True if password matches
        """
        try:
            return self.crypt_context.verify(password, hashed)
        except Exception as e:
            logger.error(f"Password verification failed: {str(e)}")
            return False


class JWTAuthenticationService(AuthenticationService):
    """JWT-based OAuth2 authentication.
    
    Issues JWT tokens for OAuth2 Bearer token authentication.
    Supports token verification and refresh.
    
    Single Responsibility: Only handles JWT authentication
    Liskov Substitution: Can swap for other auth methods
    """
    
    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
        password_hasher: PasswordHasher = None
    ):
        """Initialize JWT authentication service.
        
        Args:
            secret_key: Secret key for signing tokens (from env or config)
            algorithm: JWT algorithm (HS256, HS512, RS256, etc)
            access_token_expire_minutes: Access token expiration (minutes)
            refresh_token_expire_days: Refresh token expiration (days)
            password_hasher: Password hashing implementation
        """
        # Get secret from environment if not provided
        self.secret_key = secret_key or os.getenv("AUTH_SECRET_KEY", "")
        if not self.secret_key:
            raise ValueError("AUTH_SECRET_KEY environment variable or secret_key parameter required")
        
        if len(self.secret_key) < 32:
            logger.warning("Secret key is short, use at least 32 characters in production")
        
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.password_hasher = password_hasher or BcryptPasswordHasher()
        
        # In-memory user store (replace with database in production)
        self.users = {}  # user_id → {"username": ..., "password_hash": ..., "roles": [...]}
        self.refresh_tokens = {}  # token → {"user_id": ..., "expires": ...}
        
        logger.info(f"JWTAuthenticationService initialized with {self.algorithm}")
    
    def authenticate(self, credentials: AuthCredentials) -> AuthToken:
        """Authenticate user with username/password.
        
        Args:
            credentials: Username and password
            
        Returns:
            AuthToken with JWT access token
            
        Raises:
            ValueError: If credentials invalid
        """
        logger.info(f"Authenticating user: {credentials.username}")
        
        try:
            # Find user
            user = None
            user_id = None
            for uid, user_data in self.users.items():
                if user_data["username"] == credentials.username:
                    user = user_data
                    user_id = uid
                    break
            
            if not user:
                logger.warning(f"User not found: {credentials.username}")
                raise ValueError("Invalid username or password")
            
            # Verify password
            if not self.password_hasher.verify_password(credentials.password, user["password_hash"]):
                logger.warning(f"Invalid password for user: {credentials.username}")
                raise ValueError("Invalid username or password")
            
            # Create access token
            access_token = self._create_access_token(user_id, user["username"], user["roles"])
            
            logger.info(f"User authenticated successfully: {credentials.username}")
            
            return access_token
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise RuntimeError("Authentication service error")
    
    def verify_token(self, token: str) -> AuthUser:
        """Verify and decode JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            AuthUser with decoded information
            
        Raises:
            ValueError: If token invalid or expired
        """
        try:
            # Decode and verify
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Extract user info
            user_id = payload.get("sub")
            username = payload.get("username")
            roles = payload.get("roles", [])
            
            if not user_id or not username:
                raise ValueError("Token missing required claims")
            
            logger.debug(f"Token verified for user: {username}")
            
            return AuthUser(user_id=user_id, username=username, roles=roles)
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise ValueError("Token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise ValueError("Invalid token")
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise RuntimeError("Token verification failed")
    
    def refresh_token(self, token: str) -> AuthToken:
        """Refresh an access token.
        
        Args:
            token: Refresh token
            
        Returns:
            New AuthToken
            
        Raises:
            ValueError: If token invalid
        """
        try:
            # Verify refresh token
            if token not in self.refresh_tokens:
                raise ValueError("Invalid refresh token")
            
            token_data = self.refresh_tokens[token]
            
            # Check expiration
            if datetime.utcnow() > token_data["expires"]:
                del self.refresh_tokens[token]
                raise ValueError("Refresh token expired")
            
            # Get user info
            user_id = token_data["user_id"]
            if user_id not in self.users:
                raise ValueError("User not found")
            
            user_data = self.users[user_id]
            
            # Create new access token
            new_token = self._create_access_token(
                user_id,
                user_data["username"],
                user_data["roles"]
            )
            
            logger.info(f"Token refreshed for user: {user_id}")
            
            return new_token
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise RuntimeError("Token refresh failed")
    
    def create_user(self, username: str, password: str, roles: list = None) -> str:
        """Create a new user.
        
        Args:
            username: User email or username
            password: Plain text password (will be hashed)
            roles: List of roles
            
        Returns:
            User ID
            
        Raises:
            ValueError: If user invalid
        """
        logger.info(f"Creating user: {username}")
        
        try:
            # Validate
            if not username or "@" not in username:
                raise ValueError("Username must be valid email")
            
            if not password or len(password) < 8:
                raise ValueError("Password must be at least 8 characters")
            
            # Check if exists
            for user_data in self.users.values():
                if user_data["username"] == username:
                    raise ValueError("User already exists")
            
            # Create user ID
            user_id = f"user_{len(self.users) + 1}"
            
            # Hash password
            password_hash = self.password_hasher.hash_password(password)
            
            # Store user
            self.users[user_id] = {
                "username": username,
                "password_hash": password_hash,
                "roles": roles or ["user"],
                "created_at": datetime.utcnow()
            }
            
            logger.info(f"User created successfully: {username} ({user_id})")
            
            return user_id
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            raise RuntimeError("User creation failed")
    
    def _create_access_token(self, user_id: str, username: str, roles: list) -> AuthToken:
        """Create JWT access token.
        
        Args:
            user_id: User ID
            username: Username
            roles: User roles
            
        Returns:
            AuthToken
        """
        expires = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user_id,
            "username": username,
            "roles": roles,
            "exp": expires,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        # Also create refresh token
        refresh_token = jwt.encode(
            {
                "sub": user_id,
                "type": "refresh",
                "exp": datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
            },
            self.secret_key,
            algorithm=self.algorithm
        )
        
        self.refresh_tokens[refresh_token] = {
            "user_id": user_id,
            "expires": datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        }
        
        return AuthToken(
            token=token,
            token_type="Bearer",
            expires_in=self.access_token_expire_minutes * 60,
            user_id=user_id
        )
