"""
AUTHENTICATION_QUICK_START.md - Get Started with Authentication

Quick reference for using the new authentication system.
"""

# Authentication Quick Start

## What's New

Your compliance Q&A system now has **JWT-based OAuth2 authentication**:
- ✅ User login with email/password
- ✅ JWT token generation
- ✅ Bcrypt password hashing
- ✅ Token refresh capability
- ✅ Role-based access control
- ✅ Optional (can be disabled)

---

## 5-Minute Setup

### 1. Set Secret Key

```bash
export AUTH_SECRET_KEY="your-secret-key-min-32-chars-123456789"
```

### 2. Start Server

```bash
python -m uvicorn app_refactored:app --reload
```

### 3. Login

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

### 4. Use Token

```bash
curl -X POST http://localhost:8000/api/compliance/ask \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is GDPR?",
    "top_k": 3
  }'
```

---

## Default Test User

Ready to use out-of-the-box:

```
Email:    demo@example.com
Password: demo-password-12345
Roles:    user
```

---

## New Files Created

| File | Purpose |
|------|---------|
| [core/auth_interface.py](core/auth_interface.py) | Auth contracts & value objects |
| [infrastructure/jwt_auth.py](infrastructure/jwt_auth.py) | JWT + bcrypt implementation |
| [adapters/auth_middleware.py](adapters/auth_middleware.py) | FastAPI integration |
| [AUTHENTICATION.md](AUTHENTICATION.md) | Full documentation |

### Updated Files

- [adapters/http_api.py](adapters/http_api.py) - Added auth endpoints
- [app_refactored.py](app_refactored.py) - Integrated auth
- [infrastructure/dependencies.py](infrastructure/dependencies.py) - DI for auth

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/login` | POST | Get token |
| `/api/auth/me` | GET | User info |
| `/api/auth/refresh` | POST | Refresh token |
| `/api/compliance/ask` | POST | Ask question (needs token) |

---

## Disable Authentication

If you don't want authentication:

```bash
export AUTH_ENABLED="false"
```

All endpoints will be public.

---

## Python Usage

```python
from infrastructure.dependencies import initialize_compliance_service, ComplianceContainer

# Setup
container = ComplianceContainer()
auth_service = container.get_auth_service()
compliance_service = initialize_compliance_service("data.txt")

# Login
from core.auth_interface import AuthCredentials
creds = AuthCredentials(
    username="demo@example.com",
    password="demo-password-12345"
)
token = auth_service.authenticate(creds)
print(f"Token: {token.token}")

# Verify token
user = auth_service.verify_token(token.token)
print(f"User: {user.username}")

# Ask question (with authentication)
from core.entities import ComplianceQuestion
q = ComplianceQuestion("What is GDPR?", 3)
answer = compliance_service.answer_question(q)
```

---

## SOLID Principles

Authentication follows the same clean architecture:

- ✅ **Interfaces** in core/ (AuthenticationService, PasswordHasher)
- ✅ **Implementations** in infrastructure/ (JWTAuthenticationService)
- ✅ **Injection** in adapters/ (FastAPI integration)
- ✅ **Optional** - Can swap JWT for OAuth2, API keys, etc.

---

## Creating New Users

```python
auth_service = container.get_auth_service()

user_id = auth_service.create_user(
    username="newuser@example.com",
    password="secure-password-123",
    roles=["user"]
)

print(f"Created: {user_id}")
```

---

## Next Steps

1. **Read** [AUTHENTICATION.md](AUTHENTICATION.md) for full details
2. **Try** the 5-minute setup above
3. **Explore** the source files to understand architecture
4. **Extend** by adding OAuth2, MFA, or other auth methods

---

## Testing

```bash
# Test login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo@example.com",
    "password": "demo-password-12345"
  }' | jq .

# Test protected endpoint (need valid token)
TOKEN="<copy access_token from above>"
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq .
```

---

## Key Features

✅ **Secure** - Bcrypt hashing, JWT tokens
✅ **Flexible** - Can be enabled/disabled  
✅ **Extensible** - Interface-based (swap implementations)
✅ **Production-Ready** - Error handling, logging
✅ **Well-Documented** - Comprehensive guides
✅ **SOLID** - Follows all 5 principles

---

**Ready to use! Start with the 5-minute setup above.** 🚀

