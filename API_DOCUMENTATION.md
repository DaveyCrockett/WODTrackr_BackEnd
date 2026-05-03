# WODTrackr Backend API Documentation

## Authentication Endpoints

### Base URL
All endpoints are prefixed with: `/api/users/`

---

## Exercise Endpoints

### Base URL
All exercise endpoints are prefixed with: `/api/wodtrackr/`

### OpenAPI/Swagger
The exercise endpoints are documented in [openapi.yaml](openapi.yaml).

---

## Exercise: List / Create

**Endpoint:** `GET /api/wodtrackr/exercises/`

**Description:** List public exercises and any exercises created by the authenticated user.

**Authentication:** Required (JWT)

**Query Parameters (optional):**
- `search` (string) - Search name, description, and primary muscle group
- `category` (string) - One of: weightlifting, powerlifting, gymnastics, monostructural, accessory, mobility, other
- `equipment` (string) - One of: bodyweight, barbell, dumbbell, kettlebell, medicine_ball, box, rig, rings, rope, rower, bike, ski_erg, assault_runner, jump_rope, sled, sandbag, pegboard, other
- `muscle` (string) - Filter by primary muscle group
- `is_public` (boolean)
- `mine` (boolean) - When true, returns only exercises created by the authenticated user
- `ordering` (string) - name, -name, created_at, -created_at, updated_at, -updated_at

**Success Response (200 OK):**
```json
{
    "data": [
        {
            "id": 1,
            "name": "Back Squat",
            "description": "",
            "category": "weightlifting",
            "equipment": "barbell",
            "primary_muscle_group": "legs",
            "is_public": true,
            "created_by": 2,
            "created_by_username": "coach",
            "created_at": "2026-02-01T00:00:00Z",
            "updated_at": "2026-02-01T00:00:00Z"
        }
    ]
}
```

**Endpoint:** `POST /api/wodtrackr/exercises/`

**Description:** Create a new exercise owned by the authenticated user.

**Authentication:** Required (JWT)

**Request Body:**
```json
{
    "name": "Back Squat",
    "description": "",
    "category": "weightlifting",
    "equipment": "barbell",
    "primary_muscle_group": "legs",
    "is_public": true
}
```

**Success Response (201 Created):**
```json
{
    "message": "Exercise created successfully",
    "data": {
        "id": 1,
        "name": "Back Squat",
        "description": "",
        "category": "weightlifting",
        "equipment": "barbell",
        "primary_muscle_group": "legs",
        "is_public": true,
        "created_by": 2,
        "created_by_username": "coach",
        "created_at": "2026-02-01T00:00:00Z",
        "updated_at": "2026-02-01T00:00:00Z"
    }
}
```

---

## Exercise: Retrieve / Update / Delete

**Endpoint:** `GET /api/wodtrackr/exercises/{exercise_id}/`

**Description:** Retrieve a single exercise (public or owned).

**Authentication:** Required (JWT)

**Success Response (200 OK):**
```json
{
    "data": {
        "id": 1,
        "name": "Back Squat",
        "description": "",
        "category": "weightlifting",
        "equipment": "barbell",
        "primary_muscle_group": "legs",
        "is_public": true,
        "created_by": 2,
        "created_by_username": "coach",
        "created_at": "2026-02-01T00:00:00Z",
        "updated_at": "2026-02-01T00:00:00Z"
    }
}
```

**Endpoint:** `PUT /api/wodtrackr/exercises/{exercise_id}/`

**Description:** Update an exercise (owner or admin only).

**Authentication:** Required (JWT)

**Request Body (partial allowed):**
```json
{
    "description": "Updated description",
    "is_public": false
}
```

**Success Response (200 OK):**
```json
{
    "message": "Exercise updated successfully",
    "data": {
        "id": 1,
        "name": "Back Squat",
        "description": "Updated description",
        "category": "weightlifting",
        "equipment": "barbell",
        "primary_muscle_group": "legs",
        "is_public": false,
        "created_by": 2,
        "created_by_username": "coach",
        "created_at": "2026-02-01T00:00:00Z",
        "updated_at": "2026-02-01T00:10:00Z"
    }
}
```

**Endpoint:** `DELETE /api/wodtrackr/exercises/{exercise_id}/`

**Description:** Delete an exercise (owner or admin only).

**Authentication:** Required (JWT)

**Success Response (204 No Content)**

---

## Custom Exercise Endpoints

### Base URL
All custom exercise endpoints are prefixed with: `/api/wodtrackr/`

---

## Custom Exercise: List / Create

**Endpoint:** `GET /api/wodtrackr/custom-exercises/`

**Description:** List custom exercises created by the authenticated user (admins see all).

**Authentication:** Required (JWT)

**Query Parameters (optional):**
- `search` (string) - Search title, description, and primary muscle group
- `category` (string) - One of: weightlifting, powerlifting, gymnastics, monostructural, accessory, mobility, other
- `equipment` (string) - One of: bodyweight, barbell, dumbbell, kettlebell, medicine_ball, box, rig, rings, rope, rower, bike, ski_erg, assault_runner, jump_rope, sled, sandbag, pegboard, other
- `muscle` (string) - Filter by primary muscle group
- `created_by` (integer) - Filter by creator user ID (admin only)
- `created_from` (datetime) - ISO 8601 start time filter
- `created_to` (datetime) - ISO 8601 end time filter
- `updated_from` (datetime) - ISO 8601 start time filter
- `updated_to` (datetime) - ISO 8601 end time filter
- `ordering` (string) - title, -title, created_at, -created_at, updated_at, -updated_at

**Success Response (200 OK):**
```json
{
    "data": [
        {
            "id": 1,
            "title": "Tempo Front Squat",
            "description": "3s down, 1s pause",
            "category": "weightlifting",
            "equipment": "barbell",
            "primary_muscle_group": "legs",
            "created_by": 2,
            "created_by_username": "coach",
            "created_at": "2026-02-01T00:00:00Z",
            "updated_at": "2026-02-01T00:00:00Z"
        }
    ]
}
```

**Endpoint:** `POST /api/wodtrackr/custom-exercises/`

**Description:** Create a new custom exercise owned by the authenticated user.

**Authentication:** Required (JWT)

**Request Body:**
```json
{
    "title": "Tempo Front Squat",
    "description": "3s down, 1s pause",
    "category": "weightlifting",
    "equipment": "barbell",
    "primary_muscle_group": "legs"
}
```

**Success Response (201 Created):**
```json
{
    "message": "Custom exercise created successfully",
    "data": {
        "id": 1,
        "title": "Tempo Front Squat",
        "description": "3s down, 1s pause",
        "category": "weightlifting",
        "equipment": "barbell",
        "primary_muscle_group": "legs",
        "created_by": 2,
        "created_by_username": "coach",
        "created_at": "2026-02-01T00:00:00Z",
        "updated_at": "2026-02-01T00:00:00Z"
    }
}
```

---

## Custom Exercise: Retrieve / Update / Delete

**Endpoint:** `GET /api/wodtrackr/custom-exercises/{custom_exercise_id}/`

**Description:** Retrieve a single custom exercise (owner or admin only).

**Authentication:** Required (JWT)

**Success Response (200 OK):**
```json
{
    "data": {
        "id": 1,
        "title": "Tempo Front Squat",
        "description": "3s down, 1s pause",
        "category": "weightlifting",
        "equipment": "barbell",
        "primary_muscle_group": "legs",
        "created_by": 2,
        "created_by_username": "coach",
        "created_at": "2026-02-01T00:00:00Z",
        "updated_at": "2026-02-01T00:00:00Z"
    }
}
```

**Endpoint:** `PUT /api/wodtrackr/custom-exercises/{custom_exercise_id}/`

**Description:** Update a custom exercise (owner or admin only).

**Authentication:** Required (JWT)

**Request Body (partial allowed):**
```json
{
    "description": "Updated description"
}
```

**Success Response (200 OK):**
```json
{
    "message": "Custom exercise updated successfully",
    "data": {
        "id": 1,
        "title": "Tempo Front Squat",
        "description": "Updated description",
        "category": "weightlifting",
        "equipment": "barbell",
        "primary_muscle_group": "legs",
        "created_by": 2,
        "created_by_username": "coach",
        "created_at": "2026-02-01T00:00:00Z",
        "updated_at": "2026-02-01T00:10:00Z"
    }
}
```

**Endpoint:** `DELETE /api/wodtrackr/custom-exercises/{custom_exercise_id}/`

**Description:** Delete a custom exercise (owner or admin only).

**Authentication:** Required (JWT)

**Success Response (204 No Content)**

---

## Exercise Notes Endpoints

### Base URL
All exercise note endpoints are prefixed with: `/api/wodtrackr/`

---

## Exercise Notes: List / Create

**Endpoint:** `GET /api/wodtrackr/exercise-notes/`

**Description:** List exercise notes owned by the authenticated user (admins see all).

**Authentication:** Required (JWT)

**Query Parameters (optional):**
- `exercise_id` (integer) - Filter by exercise ID
- `custom_exercise_id` (integer) - Filter by custom exercise ID
- `search` (string) - Search notes and related exercise titles
- `user_id` (integer) - Filter by user ID (admin only)
- `target` (string) - exercise or custom_exercise
- `has_notes` (boolean) - When true, returns notes with non-empty content
- `created_from` (datetime) - ISO 8601 start time filter
- `created_to` (datetime) - ISO 8601 end time filter
- `updated_from` (datetime) - ISO 8601 start time filter
- `updated_to` (datetime) - ISO 8601 end time filter
- `ordering` (string) - created_at, -created_at, updated_at, -updated_at

**Success Response (200 OK):**
```json
{
    "data": [
        {
            "id": 1,
            "user": 2,
            "user_username": "coach",
            "exercise": 1,
            "exercise_name": "Back Squat",
            "custom_exercise": null,
            "custom_exercise_title": null,
            "notes": "Focus on bracing and drive",
            "created_at": "2026-02-01T00:00:00Z",
            "updated_at": "2026-02-01T00:00:00Z"
        }
    ]
}
```

**Endpoint:** `POST /api/wodtrackr/exercise-notes/`

**Description:** Create a new exercise note for either a public exercise or a custom exercise (exactly one target).

**Authentication:** Required (JWT)

**Request Body (provide exactly one target):**
```json
{
    "exercise": 1,
    "notes": "Focus on bracing and drive"
}
```

**Success Response (201 Created):**
```json
{
    "message": "Exercise note created successfully",
    "data": {
        "id": 1,
        "user": 2,
        "user_username": "coach",
        "exercise": 1,
        "exercise_name": "Back Squat",
        "custom_exercise": null,
        "custom_exercise_title": null,
        "notes": "Focus on bracing and drive",
        "created_at": "2026-02-01T00:00:00Z",
        "updated_at": "2026-02-01T00:00:00Z"
    }
}
```

---

## Exercise Notes: Retrieve / Update / Delete

**Endpoint:** `GET /api/wodtrackr/exercise-notes/{note_id}/`

**Description:** Retrieve a single exercise note (owner or admin only).

**Authentication:** Required (JWT)

**Success Response (200 OK):**
```json
{
    "data": {
        "id": 1,
        "user": 2,
        "user_username": "coach",
        "exercise": 1,
        "exercise_name": "Back Squat",
        "custom_exercise": null,
        "custom_exercise_title": null,
        "notes": "Focus on bracing and drive",
        "created_at": "2026-02-01T00:00:00Z",
        "updated_at": "2026-02-01T00:00:00Z"
    }
}
```

**Endpoint:** `PUT /api/wodtrackr/exercise-notes/{note_id}/`

**Description:** Update an exercise note (owner or admin only).

**Authentication:** Required (JWT)

**Request Body (partial allowed):**
```json
{
    "notes": "Updated note"
}
```

**Success Response (200 OK):**
```json
{
    "message": "Exercise note updated successfully",
    "data": {
        "id": 1,
        "user": 2,
        "user_username": "coach",
        "exercise": 1,
        "exercise_name": "Back Squat",
        "custom_exercise": null,
        "custom_exercise_title": null,
        "notes": "Updated note",
        "created_at": "2026-02-01T00:00:00Z",
        "updated_at": "2026-02-01T00:10:00Z"
    }
}
```

**Endpoint:** `DELETE /api/wodtrackr/exercise-notes/{note_id}/`

**Description:** Delete an exercise note (owner or admin only).

**Authentication:** Required (JWT)

**Success Response (204 No Content)**

---

## 1. User Registration

**Endpoint:** `POST /api/users/auth/register/`

**Description:** Register a new user account with email and password.

**Authentication:** Not required

**Request Body:**
```json
{
    "username": "string (required, unique)",
    "email": "string (required, valid email)",
    "password": "string (required, min 8 chars)",
    "password2": "string (required, must match password)",
    "first_name": "string (optional)",
    "last_name": "string (optional)"
}
```

**Success Response (201 Created):**
```json
{
    "message": "User created successfully",
    "data": {
        "username": "string",
        "email": "string",
        "id": "integer"
    }
}
```

**Error Response (400 Bad Request):**
```json
{
    "error": "Invalid registration data",
    "detail": {
        "field_name": ["error message"]
    }
}
```

**Password Requirements:**
- Minimum 8 characters
- Cannot be too similar to username/email
- Cannot be entirely numeric
- Cannot be a commonly used password

---

## 2. User Login

**Endpoint:** `POST /api/users/auth/login/`

**Description:** Login with username and password to receive JWT tokens. All login attempts (successful and failed) are logged for security monitoring.

**Authentication:** Not required

**Request Body:**
```json
{
    "username": "string (required)",
    "password": "string (required)"
}
```

**Success Response (200 OK):**
```json
{
    "access": "string (JWT access token, expires in 5 minutes)",
    "refresh": "string (JWT refresh token, expires in 1 day)"
}
```

**Error Response (401 Unauthorized):**
```json
{
    "error": "Invalid credentials",
    "detail": "The username or password is incorrect."
}
```

**Notes:**
- Access tokens expire after 5 minutes
- Refresh tokens expire after 1 day
- Failed login attempts are logged with IP address and user agent

---

## 3. Token Refresh

**Endpoint:** `POST /api/users/auth/refresh/`

**Description:** Refresh an expired access token using a valid refresh token.

**Authentication:** Not required (uses refresh token)

**Request Body:**
```json
{
    "refresh": "string (required, valid refresh token)"
}
```

**Success Response (200 OK):**
```json
{
    "access": "string (new JWT access token)"
}
```

**Error Response (401 Unauthorized):**
```json
{
    "detail": "Token is invalid or expired",
    "code": "token_not_valid"
}
```

---

## 4. Guest Session Creation

**Endpoint:** `POST /api/users/auth/guest/`

**Description:** Create a guest session token for unauthenticated users. Allows limited access without registration.

**Authentication:** Not required

**Request Body (Optional):**
```json
{
    "duration_hours": "integer (optional, default: 24, min: 1, max: 168)"
}
```

**Success Response (201 Created):**
```json
{
    "message": "Guest session created successfully",
    "data": {
        "access_token": "string (format: guest_{uuid})",
        "expires_at": "string (ISO 8601 datetime)",
        "id": "string (UUID)"
    }
}
```

**Error Response (400 Bad Request):**
```json
{
    "error": "Invalid duration",
    "detail": "Duration must be between 1 and 168 hours (7 days)."
}
```

**Notes:**
- Guest tokens are prefixed with `guest_`
- Maximum duration is 168 hours (7 days)
- Guest sessions are tracked with IP address and user agent

---

## 5. Get User Profile

**Endpoint:** `GET /api/users/profile/`

**Description:** Get current authenticated user's profile information.

**Authentication:** Required (JWT or Guest token)

**Request Headers:**
```
Authorization: Bearer {access_token}
```

**Success Response (200 OK):**
```json
{
    "data": {
        "id": "integer",
        "username": "string",
        "email": "string",
        "first_name": "string",
        "last_name": "string"
    }
}
```

**Error Response (401 Unauthorized):**
```json
{
    "detail": "Authentication credentials were not provided."
}
```

---

## 6. Update User Profile

**Endpoint:** `PUT /api/users/profile/update/`

**Description:** Update current authenticated user's profile information.

**Authentication:** Required (JWT only, not guest)

**Request Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body (all fields optional):**
```json
{
    "email": "string (valid email)",
    "first_name": "string",
    "last_name": "string"
}
```

**Success Response (200 OK):**
```json
{
    "message": "Profile updated successfully",
    "data": {
        "id": "integer",
        "username": "string",
        "email": "string",
        "first_name": "string",
        "last_name": "string"
    }
}
```

**Error Response (400 Bad Request):**
```json
{
    "error": "Invalid profile data",
    "detail": {
        "field_name": ["error message"]
    }
}
```

---

## Authentication Methods

### JWT Authentication
Include JWT access token in the Authorization header:
```
Authorization: Bearer {access_token}
```

### Guest Token Authentication
Include guest token in the Authorization header:
```
Authorization: Bearer guest_{uuid}
```

---

## Error Response Format

All error responses follow a consistent format:

```json
{
    "error": "string (error category)",
    "detail": "string or object (detailed error information)"
}
```

### Common HTTP Status Codes

- **200 OK** - Request successful
- **201 Created** - Resource created successfully
- **400 Bad Request** - Invalid request data
- **401 Unauthorized** - Authentication required or failed
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource not found
- **500 Internal Server Error** - Server error

---

## Security Features

### Login Attempt Logging
All login attempts (successful and failed) are logged with:
- Username
- IP address
- User agent
- Timestamp
- Success status

This enables:
- Brute force detection
- Security auditing
- Anomaly detection

### Password Security
- Passwords are hashed using Django's default PBKDF2 algorithm
- Password validation enforces:
  - Minimum length
  - Complexity requirements
  - Common password checks
  - User attribute similarity checks

### Session Management
- JWT access tokens expire after 5 minutes
- Refresh tokens expire after 1 day
- Guest sessions have configurable expiration (1-168 hours)
- All sessions track IP address and user agent

---

## Exercise Program Endpoints

### Base URL
All exercise program endpoints are prefixed with: `/api/wodtrackr/`

---

## Exercise Program: List / Create

**Endpoint:** `GET /api/wodtrackr/exercise-programs/`

**Description:** List public exercise programs and any programs created by the authenticated user.

**Authentication:** Required (JWT)

**Query Parameters (optional):**
- `search` (string) - Search program name and description
- `is_public` (boolean)
- `mine` (boolean) - When true, returns only programs created by the authenticated user
- `exercise_id` (integer) - Filter programs containing a shared exercise
- `custom_exercise_id` (integer) - Filter programs containing a custom exercise
- `created_by` (integer) - Filter by creator user ID (admin only)
- `ordering` (string) - name, -name, created_at, -created_at, updated_at, -updated_at

**Success Response (200 OK):**
```json
{
    "data": [
        {
            "id": 1,
            "name": "Open Prep",
            "description": "Competition prep block.",
            "is_public": true,
            "created_by": 2,
            "created_by_username": "coach",
            "items": [
                {
                    "id": 1,
                    "exercise": 10,
                    "exercise_name": "Deadlift",
                    "custom_exercise": null,
                    "custom_exercise_name": null,
                    "position": 1,
                    "week": 1,
                    "day": 1,
                    "sets": 5,
                    "reps": "3",
                    "load": "80%",
                    "rest_seconds": 120,
                    "notes": "Heavy triples",
                    "created_at": "2026-05-03T00:00:00Z",
                    "updated_at": "2026-05-03T00:00:00Z"
                }
            ],
            "created_at": "2026-05-03T00:00:00Z",
            "updated_at": "2026-05-03T00:00:00Z"
        }
    ]
}
```

**Endpoint:** `POST /api/wodtrackr/exercise-programs/`

**Description:** Create a new exercise program owned by the authenticated user.

**Authentication:** Required (JWT)

**Request Body:**
```json
{
    "name": "Open Prep",
    "description": "Competition prep block.",
    "is_public": true,
    "items": [
        {
            "exercise": 10,
            "position": 1,
            "week": 1,
            "day": 1,
            "sets": 5,
            "reps": "3",
            "load": "80%",
            "rest_seconds": 120,
            "notes": "Heavy triples"
        },
        {
            "custom_exercise": 4,
            "position": 2,
            "week": 1,
            "day": 2,
            "sets": 4,
            "reps": "8",
            "load": "RPE 7",
            "rest_seconds": 90,
            "notes": "Accessory volume"
        }
    ]
}
```

**Success Response (201 Created):**
```json
{
    "message": "Exercise program created successfully",
    "data": {
        "id": 1,
        "name": "Open Prep",
        "description": "Competition prep block.",
        "is_public": true,
        "created_by": 2,
        "created_by_username": "coach",
        "items": [
            {
                "id": 1,
                "exercise": 10,
                "exercise_name": "Deadlift",
                "custom_exercise": null,
                "custom_exercise_name": null,
                "position": 1,
                "week": 1,
                "day": 1,
                "sets": 5,
                "reps": "3",
                "load": "80%",
                "rest_seconds": 120,
                "notes": "Heavy triples",
                "created_at": "2026-05-03T00:00:00Z",
                "updated_at": "2026-05-03T00:00:00Z"
            }
        ],
        "created_at": "2026-05-03T00:00:00Z",
        "updated_at": "2026-05-03T00:00:00Z"
    }
}
```

---

## Exercise Program: Retrieve / Update / Delete

**Endpoint:** `GET /api/wodtrackr/exercise-programs/{program_id}/`

**Description:** Retrieve a public or owned program.

**Authentication:** Required (JWT)

**Endpoint:** `PUT /api/wodtrackr/exercise-programs/{program_id}/`

**Description:** Update an exercise program and optionally replace its items.

**Authentication:** Required (JWT)

**Endpoint:** `DELETE /api/wodtrackr/exercise-programs/{program_id}/`

**Description:** Delete an exercise program.

**Authentication:** Required (JWT)

---

## Exercise Program: Reuse

**Endpoint:** `POST /api/wodtrackr/exercise-programs/{program_id}/reuse/`

**Description:** Clone a visible program into the authenticated user's library as a private copy.

**Authentication:** Required (JWT)

**Success Response (201 Created):**
```json
{
    "message": "Exercise program reused successfully",
    "data": {
        "id": 7,
        "name": "Open Prep Copy",
        "description": "Competition prep block.",
        "is_public": false,
        "created_by": 3,
        "created_by_username": "athlete",
        "items": [
            {
                "id": 21,
                "exercise": 10,
                "exercise_name": "Deadlift",
                "custom_exercise": null,
                "custom_exercise_name": null,
                "position": 1,
                "week": 1,
                "day": 1,
                "sets": 5,
                "reps": "3",
                "load": "80%",
                "rest_seconds": 120,
                "notes": "Heavy triples",
                "created_at": "2026-05-03T00:00:00Z",
                "updated_at": "2026-05-03T00:00:00Z"
            }
        ],
        "created_at": "2026-05-03T00:00:00Z",
        "updated_at": "2026-05-03T00:00:00Z"
    }
}
```

---

## Development and Testing

### Seed Data Command

Create test users for development:

```bash
python manage.py seed_users
```

This creates:
- **Admin user:** `admin / admin123` (superuser)
- **Coach user:** `coach / coach123` (coach role)
- **Test user:** `testuser / testpass123` (regular user)

To reset and recreate:
```bash
python manage.py seed_users --reset
```

### Running Tests

Run all authentication tests:
```bash
python manage.py test users
```

Run specific test class:
```bash
python manage.py test users.AuthenticationTestCase
```

---

## Rate Limiting

**Note:** Rate limiting is not currently implemented but should be added in production to prevent abuse of authentication endpoints.

Recommended limits:
- Login endpoint: 5 attempts per 15 minutes per IP
- Registration endpoint: 3 attempts per hour per IP
- Guest session: 10 per hour per IP

---

## Future Enhancements

Planned authentication features:
1. Email verification
2. Two-factor authentication (2FA)
3. Password reset flow
4. OAuth integration (Google, Facebook)
5. Session management (view/revoke active sessions)
6. Rate limiting
7. Account lockout after failed attempts
