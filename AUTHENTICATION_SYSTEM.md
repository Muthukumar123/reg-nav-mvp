# Authentication System - Complete Guide

## Overview

The Regulation Navigator MVP now includes a complete authentication system with login/logout functionality, password hashing, and token-based API access control.

## Features

✅ **Login Screen** - Users must authenticate before accessing the chat interface
✅ **Password Hashing** - SHA256 with mod key "Handbook"  
✅ **Token Authentication** - JWT-style tokens for API access
✅ **Session Persistence** - Credentials stored in session storage
✅ **Logout Functionality** - Clear session and return to login
✅ **Back Button** - Navigate back while in chat
✅ **User Display** - Show username and logout option in header

## Demo Credentials

```
Username: Muthu
Password: Amsterdam@2025
```

## How It Works

### Frontend Flow

1. **Login Screen Displayed**
   - User enters username and password
   - Password is hashed: SHA256(password + "Handbook")
   - Hashed password sent to backend

2. **Backend Verification**
   - Username checked against hardcoded value "Muthu"
   - Password hash compared with stored hash
   - If valid, secure token generated
   - Token expires after 2 hours

3. **Chat Interface Access**
   - Token stored in session storage
   - Every API call includes Authorization header
   - Token format: `Bearer <token>`

### Backend Architecture

**Hardcoded Credentials (Development):**
```python
VALID_USERNAME = "Muthu"
VALID_PASSWORD_HASH = "36e566b6181490fd5d5f0a354d418531f37e4f523e9387f2fc994c707244134f"
# This is SHA256("Amsterdam@2025" + "Handbook")
MOD_KEY = "Handbook"
```

**Token Management:**
```python
ACTIVE_TOKENS: Dict[str, tuple[str, datetime]] = {}
# Format: { token_string: (username, expiry_datetime) }
```

## API Endpoints

### Login Endpoint

**Request:**
```bash
POST /auth/login
Content-Type: application/json

{
  "username": "Muthu",
  "password_hash": "36e566b6181490fd5d5f0a354d418531f37e4f523e9387f2fc994c707244134f"
}
```

**Response (Success):**
```json
{
  "success": true,
  "token": "fYqt_c6YsSforxB7K1xDmQv8-wLrRZ688Ww_fxveBOM",
  "message": "Welcome, Muthu!"
}
```

**Response (Failure):**
```json
{
  "detail": "Invalid username or password"
}
```

### Ask Endpoint (Protected)

**Request:**
```bash
POST /ask
Authorization: Bearer <token>
Content-Type: application/json

{
  "question": "What is GDPR?",
  "top_k": 3
}
```

**Response:**
```json
{
  "answer": "GDPR is Regulation (EU) 2016/679...",
  "citations": [
    {
      "doc": "Regulation (EU) 2016/679",
      "section": "Article 5"
    }
  ],
  "scores": [0.543, 0.412, 0.298]
}
```

## Password Hashing Algorithm

The system uses SHA256 with a mod key for added security:

```python
def hash_password(password: str, mod_key: str = "Handbook") -> str:
    combined = password + mod_key
    return hashlib.sha256(combined.encode()).hexdigest()
```

**Example:**
- Password: "Amsterdam@2025"
- Mod Key: "Handbook"
- Combined: "Amsterdam@2025Handbook"
- SHA256 Hash: "36e566b6181490fd5d5f0a354d418531f37e4f523e9387f2fc994c707244134f"

## Frontend Implementation

### Login Component

```typescript
const hashPassword = async (password: string, modKey: string = 'Handbook'): Promise<string> => {
  const combined = password + modKey;
  const encoder = new TextEncoder();
  const data = encoder.encode(combined);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  return hashHex;
};
```

### API Calls with Token

```typescript
const token = sessionStorage.getItem('token');
const response = await axios.post(
  `/api/ask`,
  { question: input, top_k: 3 },
  { 
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);
```

## Token Lifecycle

1. **Generation** - Created on successful login
2. **Storage** - Stored in browser session storage
3. **Usage** - Included in every API request
4. **Expiration** - Expires after 2 hours
5. **Validation** - Checked and validated on every API call
6. **Cleanup** - Removed when user logs out

## Testing the System

### Using cURL

```bash
# Step 1: Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "Muthu",
    "password_hash": "36e566b6181490fd5d5f0a354d418531f37e4f523e9387f2fc994c707244134f"
  }' | jq -r '.token')

# Step 2: Use token to call /ask
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "question": "What is GDPR?",
    "top_k": 3
  }'
```

### Using Python

```python
import requests
import hashlib

# Constants
username = "Muthu"
password = "Amsterdam@2025"
mod_key = "Handbook"

# Hash password
combined = password + mod_key
password_hash = hashlib.sha256(combined.encode()).hexdigest()

# Login
login_response = requests.post(
    'http://localhost:8000/auth/login',
    json={'username': username, 'password_hash': password_hash}
)
token = login_response.json()['token']

# Ask question
ask_response = requests.post(
    'http://localhost:8000/ask',
    json={'question': 'What is GDPR?', 'top_k': 3},
    headers={'Authorization': f'Bearer {token}'}
)
print(ask_response.json())
```

## Production Considerations

The current implementation uses:
- ✅ SHA256 password hashing with mod key
- ✅ Secure token generation
- ✅ Token expiration (2 hours)
- ✅ In-memory token storage

**For production, consider:**
- [ ] Move credentials to environment variables
- [ ] Use database for user storage
- [ ] Implement refresh tokens
- [ ] Add rate limiting
- [ ] Use HTTPS/TLS
- [ ] Add password strength requirements
- [ ] Implement account lockout after failed attempts
- [ ] Add logging and monitoring
- [ ] Use OAuth2 or similar standards

## Troubleshooting

### "Invalid username or password"
- Verify username is exactly "Muthu"
- Verify password hash is calculated correctly
- Check that mod key is exactly "Handbook"

### "Missing authorization token"
- Ensure Authorization header is included
- Format should be: `Authorization: Bearer <token>`
- Token might have expired (2 hour limit)

### "Token expired"
- Token has exceeded 2 hour expiration
- User must login again to get new token

### Session Lost After Browser Refresh
- Session storage is cleared
- User must login again
- Consider localStorage for persistence

## Files Modified

- `app.py` - Backend authentication endpoints and logic
- `frontend/app/page.tsx` - Login screen and auth integration
- `requirements.txt` - Dependencies (no changes needed)

## Related Documentation

- [README.md](README.md) - System overview
- [CHANGELOG.md](CHANGELOG.md) - Recent changes
- [API_V2_MIGRATION.md](API_V2_MIGRATION.md) - OpenAI API updates
