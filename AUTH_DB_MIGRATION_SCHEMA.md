# Auth-Related Database Migration - Issue #6

## Overview
Designed and applied comprehensive auth-related database schema for user authentication and session management.

## New Database Models

### 1. **UserProfile**
Extended user profile with authentication metadata and user roles.

**Fields:**
- `user` (OneToOne) - Link to Django User model
- `role` - User role: user, coach, admin
- `profile_picture` - User avatar
- `bio` - User biography
- `phone_number` - Contact number
- `verified` - Email verification status
- `two_factor_enabled` - 2FA activation status
- `created_at` - Account creation timestamp
- `updated_at` - Last profile update
- `last_login` - Last successful login

**Use Cases:**
- Track user roles and permissions
- Store user metadata
- Monitor verification and security settings

---

### 2. **UserSession**
Tracks authenticated user sessions with device and location tracking.

**Fields:**
- `user` (ForeignKey) - Associated user
- `session_key` - Unique session identifier
- `ip_address` - Client IP address
- `user_agent` - Browser/device info
- `device_name` - Friendly device name
- `is_active` - Session active status
- `created_at` - Session creation time
- `last_activity` - Last activity timestamp
- `expires_at` - Session expiration time

**Use Cases:**
- Multi-device session management
- "Show active sessions" dashboard
- Logout from specific devices
- Security monitoring and anomaly detection
- Session expiration tracking

**Methods:**
- `is_valid()` - Check if session is active and not expired
- `logout()` - Mark session as inactive

---

### 3. **GuestSession** (Enhanced)
Unauthenticated guest sessions with limited access.

**Added Fields:**
- `session_data` (JSONField) - Store guest preferences/data

**Existing Fields:**
- `id` - UUID primary key
- `token` - Unique token (format: `guest_{uuid}`)
- `created_at` - Creation timestamp
- `expires_at` - Expiration timestamp
- `is_active` - Active status
- `ip_address` - Client IP
- `user_agent` - Browser info

**Use Cases:**
- Guest user browsing without registration
- Limited functionality access
- Session data storage for guests

---

### 4. **LoginAttempt**
Security logging for login attempts (both successful and failed).

**Fields:**
- `username` - Attempted username
- `ip_address` - Source IP address
- `user_agent` - Browser/device info
- `success` - Login success status
- `timestamp` - Attempt time

**Indexes:**
- `(username, timestamp)` - Query by user
- `(ip_address, timestamp)` - Query by IP

**Use Cases:**
- Brute force detection
- Login history auditing
- Suspicious activity monitoring
- IP-based anomaly detection
- Security incident investigation

---

## Database Schema

```sql
-- UserProfile Table
CREATE TABLE users_userprofile (
    id BIGINT PRIMARY KEY,
    user_id INT UNIQUE,
    role VARCHAR(20),
    profile_picture VARCHAR(100),
    bio TEXT,
    phone_number VARCHAR(20),
    verified BOOLEAN DEFAULT FALSE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_login TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES auth_user(id)
);

-- UserSession Table
CREATE TABLE users_usersession (
    id BIGINT PRIMARY KEY,
    user_id INT,
    session_key VARCHAR(255) UNIQUE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    last_activity TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES auth_user(id)
);

-- GuestSession Table
CREATE TABLE users_guestsession (
    id UUID PRIMARY KEY,
    token VARCHAR(255) UNIQUE,
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    ip_address VARCHAR(45) NULL,
    user_agent TEXT,
    session_data JSONB DEFAULT '{}'
);

-- LoginAttempt Table
CREATE TABLE users_loginattempt (
    id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    success BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP
);
```

---

## Admin Configuration

All models registered in Django admin with custom list displays:

### UserProfile Admin
- Display: username, role, verified, 2FA status, creation date
- Filters: role, verified, 2FA, creation date
- Fieldsets: User info, Profile details, Security, Timestamps
- Search: by username, email

### UserSession Admin
- Display: username, device, IP, status, last activity
- Filters: active status, creation date, activity date
- Fieldsets: Session info, Connection details, Status, Timeline
- Search: by username, IP, device name
- Status indicator with color coding (green/red)

### GuestSession Admin
- Display: ID, validity status, IP, creation, expiration
- Filters: active status, creation date, expiration date
- Search: by ID, IP address
- Status indicator with color coding

### LoginAttempt Admin
- Display: username, IP, success status, timestamp
- Filters: success status, timestamp
- Search: by username, IP
- Read-only (auto-recorded, non-editable)
- Status indicator: Success (green) / Failed (red)

---

## Migration Information

**Migration File:** `users/migrations/0002_alter_guestsession_options_guestsession_session_data_and_more.py`

**Changes:**
- Modified GuestSession Meta options
- Added session_data field to GuestSession
- Created LoginAttempt model
- Created UserProfile model
- Created UserSession model

**Status:** ✓ Applied successfully

---

## Security Features

1. **Session Management:**
   - Automatic expiration tracking
   - Device-level logout capability
   - Session revocation support

2. **Login Monitoring:**
   - Successful/failed attempt logging
   - IP address tracking
   - User-Agent logging for device identification
   - Indexed queries for quick security checks

3. **Guest Sessions:**
   - UUID-based tokens (cryptographically secure)
   - Expiration enforcement
   - Optional session data storage

4. **User Verification:**
   - Email verification tracking
   - 2FA activation status
   - Account role-based access control

---

## Usage Examples

### Create User Profile
```python
from django.contrib.auth.models import User
from users.models import UserProfile

user = User.objects.create_user(username='john', email='john@example.com')
profile = UserProfile.objects.create(
    user=user,
    role='user',
    bio='My bio',
    phone_number='+1234567890'
)
```

### Create User Session
```python
from users.models import UserSession
from django.utils import timezone
from datetime import timedelta

session = UserSession.objects.create(
    user=user,
    session_key='abc123xyz',
    ip_address='192.168.1.1',
    user_agent='Mozilla/5.0...',
    device_name='Chrome on Windows',
    expires_at=timezone.now() + timedelta(days=30)
)
```

### Create Login Attempt
```python
from users.models import LoginAttempt

LoginAttempt.objects.create(
    username='john',
    ip_address='192.168.1.1',
    user_agent='Mozilla/5.0...',
    success=True
)
```

### Query Active Sessions
```python
from django.utils import timezone

user = User.objects.get(username='john')
active_sessions = user.sessions.filter(
    is_active=True,
    expires_at__gt=timezone.now()
)
```

### Admin Logout
```python
session = UserSession.objects.get(id=1)
session.logout()  # Marks as inactive
```

---

## Next Steps

1. Create authentication middleware to automatically log login attempts
2. Implement session cleanup management command
3. Add session security middleware (IP validation, etc.)
4. Create API endpoints for session management
5. Implement 2FA authentication logic
6. Add login throttling based on LoginAttempt logs
