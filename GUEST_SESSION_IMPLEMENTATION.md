# Guest Session/Token Flow Implementation

## Overview
Implemented a guest session/token flow that allows unauthenticated users to access limited functionality without creating an account.

## Key Features

### 1. **GuestSession Model** ([users/models.py](users/models.py))
- UUID-based unique identifier
- Auto-generated token (format: `guest_{uuid}`)
- Expiration tracking with configurable duration (default: 24 hours)
- IP address and User-Agent logging
- `is_valid()` method to check session validity
- `create_session()` class method for creating new sessions

### 2. **Authentication Backend** ([users/auth.py](users/auth.py))
Two authentication classes provided:

- **GuestSessionAuthentication**: Standalone authentication for guest tokens
- **GuestTokenAuthentication**: Extended authentication supporting both JWT and guest tokens

Guest tokens are identified by the `guest_` prefix and validated against the database.

### 3. **Custom Permissions** ([users/permissions.py](users/permissions.py))

- **IsAuthenticatedOrGuest**: Allows both authenticated users and guests
- **IsGuest**: Only allows guest session holders
- **IsAuthenticatedUser**: Only allows registered authenticated users (excludes guests)

### 4. **Guest Session Endpoint**

**Create Guest Session:**
```
POST /users/auth/guest/
```

**Response:**
```json
{
    "message": "Guest session created successfully",
    "data": {
        "access_token": "guest_550e8400-e29b-41d4-a716-446655440000",
        "expires_at": "2026-01-20T10:30:45.123456Z",
        "id": "550e8400-e29b-41d4-a716-446655440000"
    }
}
```

**Optional Parameters:**
- `duration_hours` (integer, default: 24): How long the guest session should be valid

### 5. **Using Guest Tokens**

Include the guest token in the Authorization header:
```
Authorization: Bearer guest_550e8400-e29b-41d4-a716-446655440000
```

## Usage Examples

### Creating a Guest Session
```bash
curl -X POST http://localhost:8000/users/auth/guest/ \
  -H "Content-Type: application/json"
```

### Using Guest Token to Access Protected Resources
```bash
curl -X GET http://localhost:8000/users/profile/ \
  -H "Authorization: Bearer guest_550e8400-e29b-41d4-a716-446655440000"
```

(Guest users can be allowed access by using `IsAuthenticatedOrGuest` permission)

## Endpoint Details

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/users/auth/guest/` | POST | No | Create a new guest session |
| `/users/auth/login/` | POST | No | Login as registered user (JWT) |
| `/users/auth/register/` | POST | No | Register new user account |
| `/users/auth/refresh/` | POST | Yes | Refresh JWT token |
| `/users/profile/` | GET | Yes | Get user profile (supports both JWT and guest) |
| `/users/profile/update/` | PUT | Yes | Update user profile (JWT only) |

## Database Schema

**GuestSession Table:**
- `id` (UUID, Primary Key)
- `token` (CharField, unique)
- `created_at` (DateTime)
- `expires_at` (DateTime)
- `is_active` (Boolean)
- `ip_address` (GenericIPAddressField, nullable)
- `user_agent` (TextField)

## Security Considerations

1. **Token Format**: Guest tokens follow the pattern `guest_{uuid}` for easy identification
2. **Expiration**: Sessions automatically expire after the configured duration
3. **IP Logging**: Optional IP address tracking for security audits
4. **User-Agent Logging**: Optional User-Agent tracking for device identification
5. **Database Storage**: Tokens are stored in the database (not JWTs) for revocation capability
6. **Inactive Flag**: Sessions can be manually deactivated

## Configuration

Guest tokens use the standard DRF authentication chain. The `GuestTokenAuthentication` backend is added to `DEFAULT_AUTHENTICATION_CLASSES` in settings.py and will:
1. Accept guest tokens (prefixed with `guest_`)
2. Fall back to JWT authentication for regular tokens
3. Allow both token types in the same request

## Future Enhancements

- Rate limiting per guest session
- Guest session upgrade to full user account
- Session activity tracking
- Guest feature restrictions/limits
- Auto-cleanup of expired sessions
