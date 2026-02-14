"""
AUTHENTICATION.md - JWT Authentication System

Complete guide to authentication in the refactored compliance system.
"""

# Authentication System - JWT-Based OAuth2

---

## Overview

The refactored system includes **optional OAuth2 JWT authentication** with:
- ✅ JWT token-based authentication
- ✅ Bcrypt password hashing
- ✅ Token refresh capability
- ✅ User role-based access control
- ✅ Seamless FastAPI integration

All implemented following **SOLID principles** with interfaces and dependency injection.

---

## Architecture

### Authentication Layers

```
┌─────────────────────────────────────────┐
│  HTTP Endpoints (adapters/auth_middleware.py) │ ← FastAPI routes
├─────────────────────────────────────────┤
│   HTTP API Adapter (adapters/http_api.py)    │ ← Auth endpoints
├─────────────────────────────────────────┤
│   Auth Service Interface (core/auth_interface.py) │ ← Contracts
├─────────────────────────────────────────┤
│   JWT Implementation (infrastructure/jwt_auth.py) │ ← Concrete
└─────────────────────────────────────────┘
```

### Components

**Core Layer** ([core/auth_interface.py](core/auth_interface.py)):
- `AuthToken` - Immutable token value object
- `AuthCredentials` - Username/password value object
- `AuthUser` - Authenticated user info
- `AuthenticationService` (ABC) - Service contract
- `PasswordHasher` (ABC) - Password hashing contract

**Infrastructure Layer** ([infrastructure/jwt_auth.py](infrastructure/jwt_auth.py)):
- `BcryptPasswordHasher` - Bcrypt implementation
- `JWTAuthenticationService` - JWT implementation

**Adapter Layer** ([adapters/auth_middleware.py](adapters/auth_middleware.py)):
- `FastAPIAuthAdapter` - FastAPI integration
- Dependency injection for FastAPI routes

**API Adapter** ([adapters/http_api.py](adapters/http_api.py)):
- Login endpoint (`/api/auth/login`)
- User info endpoint (`/api/auth/me`)
- Token refresh endpoint (`/api/auth/refresh`)

---

##Configuration

### Environment Variables

```bash
# Authentication settings
export AUTH_ENABLED="true"              # Enable/disable auth (default: true)
export AUTH_SECRET_KEY="your-secret"    # JWT signing key (min 32 chars)
export AUTH_ALGORITHM="HS256"           # JWT algorithm (default: HS256)
export AUTH_ACCESS_TOKEN_EXPIRE="30"    # Access token lifetime (minutes)
export AUTH_REFRESH_TOKEN_EXPIRE="7"    # Refresh token lifetime (days)
```

### Python Configuration

```python
from infrastructure.dependencies import ComplianceConfig

print(ComplianceConfig.AUTH_ENABLED)              # true
print(ComplianceConfig.AUTH_SECRET_KEY)           # "your-secret..."
print(ComplianceConfig.AUTH_ALGORITHM)            # "HS256"
print(ComplianceConfig.AUTH_ACCESS_TOKEN_EXPIRE)  # 30
```

---

## Usage

### 1. Login and Get Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo@example.com",
    "password": "demo-password-12345"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 1800,
  "user_id": "user_1"
}
```

### 2. Use Token to Call Protected Endpoint

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Response:
```json
{
  "user_id": "user_1",
  "username": "demo@example.com",
  "roles": ["user"]
}
```

### 3. Ask Compliance Question (with Auth)

```bash
curl -X POST http://localhost:8000/api/compliance/ask \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is GDPR?",
    "top_k": 3
  }'
```

### 4. Refresh Access Token

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Authorization: Bearer <refresh_token>"
```

---

## API Endpoints

### Authentication Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---|
| `/api/auth/login` | POST | Login with credentials | ❌ No |
| `/api/auth/me` | GET | Get current user info | ✅ Yes |
| `/api/auth/refresh` | POST | Refresh access token | ❌ No (uses refresh token) |

### Compliance Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---|
| `/api/compliance/ask` | POST | Ask compliance question | ✅ Yes (if auth enabled) |
| `/health` | GET | Health check | ❌ No |
| `/info` | GET | Service info | ❌ No |

---

## Authentication Flow

### Login Flow

```
┌─────────────────┐
│  User Request   │
│  POST /login    │
│  with creds     │
└────────┬────────┘
         ↓
┌─────────────────────────────────┐
│ FastAPI                         │
│ Extract credentials from request│
└────────┬────────────────────────┘
         ↓
┌─────────────────────────────────┐
│ HTTPComplianceAPI.login()       │
│ Validate credentialss           │
└────────┬────────────────────────┘
         ↓
┌─────────────────────────────────┐
│ JWTAuthenticationService        │
│ - Verify username               │
│ - Check password (bcrypt)       │
│ - Generate JWT token            │
└────────┬────────────────────────┘
         ↓
┌─────────────────────────────────┐
│ Response: AuthToken             │
│ - access_token (JWT)            │
│ - token_type (Bearer)           │
│ - expires_in (seconds)          │
└─────────────────────────────────┘
```

### Protected Endpoint Flow

```
┌────────────────────────┐
│  User Request          │
│  GET /api/compliance   │
│  with Bearer token     │
└────────┬───────────────┘
         ↓
┌────────────────────────────────────────┐
│ FastAPI                                │
│ Extract Bearer token from header       │
└────────┬───────────────────────────────┘
         ↓
┌────────────────────────────────────────┐
│ FastAPIAuthAdapter.verify_bearer_token()│
│ Decode and verify JWT                  │
└────────┬───────────────────────────────┘
         ↓
┌────────────────────────────────────────┐
│ JWTAuthenticationService.verify_token()│
│ - Check signature                      │
│ - Verify expiration                    │
│ - Extract user info                    │
└────────┬───────────────────────────────┘
         ↓
┌────────────────────────────────────────┐
│ AuthUser (Injected into endpoint)      │
│ - user_id                              │
│ - username                             │
│ - roles                                │
└────────┬───────────────────────────────┘
         ↓
┌────────────────────────────────────────┐
│ Protected Endpoint Handler             │
│ Can use AuthUser for authorization     │
└────────────────────────────────────────┘
```

---

## Using Authentication with Endpoints

### Require Authentication

```python
from adapters.auth_middleware import FastAPIAuthAdapter
from core.auth_interface import AuthUser
from fastapi import Depends

adapter = FastAPIAuthAdapter(auth_service)

@app.get("/protected")
async def protected_route(user: AuthUser = Depends(adapter.verify_bearer_token)):
    return {"message": f"Hello {user.username}"}
```

### Optional Authentication

```python
@app.get("/maybe-protected")
async def optional_route(user: Optional[AuthUser] = Depends(adapter.verify_bearer_token_optional)):
    if user:
        return {"message": f"Hello {user.username}"}
    else:
        return {"message": "Hello anonymous"}
```

### Role-Based Access Control

```python
@app.delete("/admin/questions")
async def admin_delete(user: AuthUser = Depends(adapter.require_role("admin"))):
    return {"message": "Deleted"}
```

---

## Default Test User

For development/testing, the system creates a default user:

| Field | Value |
|-------|-------|
| Username | `demo@example.com` |
| Password | `demo-password-12345` |
| Roles | `["user"]` |

**⚠️ Change in production!**

---

## Creating New Users

### Programmatically

```python
from infrastructure.dependencies import ComplianceContainer

container = ComplianceContainer()
auth_service = container.get_auth_service()

# Create user
user_id = auth_service.create_user(
    username="newuser@example.com",
    password="secure-password-123",
    roles=["user", "admin"]
)

print(f"User created: {user_id}")
```

### Via API (Not yet implemented - add endpoint)

Future: You can add a registration endpoint if needed.

---

## Password Security

### Bcrypt Hashing

Passwords are hashed using bcrypt with automatic salt generation:

```python
from infrastructure.jwt_auth import BcryptPasswordHasher

hasher = BcryptPasswordHasher()

# Hash password
hash = hasher.hash_password("user-password")

# Verify password
is_valid = hasher.verify_password("user-password", hash)
```

Requirements:
- ✅ Minimum 8 characters
- ✅ Bcrypt hashing with salt
- ✅ Never stored in plain text

---

## JWT Token Details

### Access Token

- **Algorithm**: HS256 (HMAC SHA-256)
- **Expiration**: 30 minutes (configurable)
- **Claims**:
  - `sub` - User ID
  - `username` - Username
  - `roles` - User roles
  - `exp` - Expiration time
  - `iat` - Issued at time

### Refresh Token

- **Expiration**: 7 days (configurable)
- **Purpose**: Get new access token without re-login
- **Stored**: In-memory (replace with database in production)

---

## Security Best Practices

### ✅ Do

- ✅ Use strong secret key (min 32 characters)
- ✅ Change default test user password in production
- ✅ Use HTTPS in production (not HTTP)
- ✅ Keep secret key environment variable secure
- ✅ Refresh tokens regularly
- ✅ Use role-based access control

### ❌ Don't

- ❌ Use weak secret keys
- ❌ Keep default test credentials in production
- ❌ Log tokens or passwords
- ❌ Store tokens in localStorage (use httpOnly cookies)
- ❌ Expose secret key in code
- ❌ Use HTTP in production

---

## Production Deployment

### 1. Set Strong Secret Key

```bash
# Generate strong key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Set environment variable
export AUTH_SECRET_KEY="your-generated-key-here"
```

### 2. Replace In-Memory User Store

Current implementation uses in-memory dictionary. For production:

```python
# Replace in infrastructure/jwt_auth.py
# instead of: self.users = {}

# Use database
from sqlalchemy import create_engine
from models import User

engine = create_engine("postgresql://...")
# Query users from database
```

### 3. Use Database for Refresh Tokens

Current implementation stores refresh tokens in memory. For production:

```python
# Create refresh_tokens table
# Query from database instead of in-memory dict
```

### 4. Enable HTTPS/TLS

```bash
# Use Gunicorn with SSL certificate
gunicorn app_refactored:app \
  --certfile=/path/to/cert.pem \
  --keyfile=/path/to/key.pem \
  --bind 0.0.0.0:443
```

### 5. Add Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(...):
    ...
```

---

## Disabling Authentication

### Option 1: Environment Variable

```bash
export AUTH_ENABLED="false"
```

The system will skip authentication initialization and all endpoints will be public.

### Option 2: Code

```python
from infrastructure.dependencies import ComplianceConfig

ComplianceConfig.AUTH_ENABLED = False
```

---

## Testing Authentication

### Test Login

```python
import pytest
from fastapi.testclient import TestClient
from app_refactored import app

client = TestClient(app)

def test_login():
    response = client.post(
        "/api/auth/login",
        json={
            "username": "demo@example.com",
            "password": "demo-password-12345"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
```

### Test Protected Endpoint

```python
def test_protected_endpoint_with_token():
    # Get token
    login_response = client.post(
        "/api/auth/login",
        json={
            "username": "demo@example.com",
            "password": "demo-password-12345"
        }
    )
    token = login_response.json()["access_token"]
    
    # Use token
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "demo@example.com"


def test_protected_endpoint_without_token():
    response = client.get("/api/auth/me")
    assert response.status_code == 401
```

---

## SOLID Principles in Authentication

### ✅ Single Responsibility
- `BcryptPasswordHasher` - Only passwords
- `JWTAuthenticationService` - Only JWT
- `FastAPIAuthAdapter` - Only FastAPI integration

### ✅ Open/Closed
Add new auth methods without modifying existing:
```python
class OAuth2Service(AuthenticationService):
    def authenticate(...): ...
    def verify_token(...): ...
    # Different implementation, same interface!
```

### ✅ Liskov Substitution
All auth services satisfy `AuthenticationService` contract.

### ✅ Interface Segregation
- `AuthenticationService` - Auth only
- `PasswordHasher` - Hashing only
- Focused, not bloated

### ✅ Dependency Inversion
Services depend on `AuthenticationService` interface, not concrete `JWTAuthenticationService `.

---

## Extension Examples

### Add OAuth2 Google Login

```python
class GoogleOAuth2Service(AuthenticationService):
    def authenticate(self, credentials):
        # Validate with Google OAuth2
        pass
    
    def verify_token(self, token):
        # Verify Google token
        pass
```

### Add Multi-Factor Authentication

```python
class MFAAuthenticationService(AuthenticationService):
    def authenticate(self, credentials):
        # First factor: username/password
        # Second factor: TOTP code
        pass
```

### Add API Key Authentication

```python
class APIKeyAuthenticationService(AuthenticationService):
    def authenticate(self, credentials):
        # Validate API key
        pass
```

---

## Troubleshooting

### "Invalid token" Error

```python
# Check if token is expired
# Check if signature is valid
# Check if algorithm matches
```

### "Authentication not enabled" Error

```bash
export AUTH_ENABLED="true"
```

### Password Verification Fails

```python
# Ensure password is at least 8 characters
# Ensure password hash is valid
# Check bcrypt installation: pip install passlib[bcrypt]
```

### Secret Key Too Short

```python
# Secret key must be at least 32 characters
# Run: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Summary

The authentication system:
- ✅ Follows SOLID principles
- ✅ Uses industry-standard JWT technology
- ✅ Provides secure password hashing with bcrypt
- ✅ Integrates seamlessly with FastAPI
- ✅ Can be extended with other auth methods
- ✅ Optional (can be disabled)
- ✅ Production-ready with improvements

For questions, see the source code:
- Domain contracts: [core/auth_interface.py](core/auth_interface.py)
- JWT implementation: [infrastructure/jwt_auth.py](infrastructure/jwt_auth.py)
- FastAPI integration: [adapters/auth_middleware.py](adapters/auth_middleware.py)
- API endpoints: [adapters/http_api.py](adapters/http_api.py)

