# Workout API - Client Documentation

**Base URL:** `http://your-api-domain.com/api`

**Authentication:** Token-based authentication using `Authorization: Token <token>` header

---

## Table of Contents

- [Authentication Endpoints](#authentication-endpoints)
- [User Profile Endpoints](#user-profile-endpoints)
- [Exercise Endpoints](#exercise-endpoints)
- [Workout Endpoints](#workout-endpoints)
- [Workout Session Endpoints](#workout-session-endpoints)
- [Exercise Log Endpoints](#exercise-log-endpoints)
- [Health Check](#health-check)
- [Error Responses](#error-responses)

---

## Authentication Endpoints

### Register User

Creates a new user account and returns an authentication token.

**Endpoint:** `POST /api/auth/register/`

**Authentication:** None required

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "password_confirm": "SecurePass123",
  "first_name": "John",      // Optional
  "last_name": "Doe"          // Optional
}
```

**Success Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 3,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "token": "15e89aee024a2e9af90e2ca062c6c6f91355eada",
  "profile": {
    "id": "69371de04541c2393d28e89b",
    "user_id": 3,
    "username": "johndoe",
    "email": "john@example.com",
    "height": null,
    "weight": null,
    "date_of_birth": null,
    "fitness_goal": "general",
    "created_at": "2025-12-08T18:50:08.931830Z",
    "updated_at": "2025-12-08T18:50:08.931870Z"
  }
}
```

**Error Response (400):**
```json
{
  "username": ["A user with that username already exists."],
  "email": ["This field must be unique."],
  "password": ["This password is too short. It must contain at least 8 characters."]
}
```

---

### Login

Authenticate user and receive token.

**Endpoint:** `POST /api/auth/login/`

**Authentication:** None required

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "SecurePass123"
}
```

**Success Response (200):**
```json
{
  "message": "Login successful",
  "user": {
    "id": 3,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "token": "15e89aee024a2e9af90e2ca062c6c6f91355eada",
  "profile": {
    "id": "69371de04541c2393d28e89b",
    "user_id": 3,
    "username": "johndoe",
    "email": "john@example.com",
    "height": 180,
    "weight": "75.00",
    "date_of_birth": null,
    "fitness_goal": "weight_gain",
    "created_at": "2025-12-08T18:50:08.931000Z",
    "updated_at": "2025-12-08T18:51:34.694000Z"
  }
}
```

**Error Response (400):**
```json
{
  "detail": "Invalid credentials"
}
```

---

### Logout

Invalidate the current authentication token.

**Endpoint:** `POST /api/auth/logout/`

**Authentication:** Required

**Headers:**
```
Authorization: Token 15e89aee024a2e9af90e2ca062c6c6f91355eada
```

**Request Body:** None

**Success Response (200):**
```json
{
  "message": "Logout successful"
}
```

---

## User Profile Endpoints

### Get Profile

Retrieve the current user's profile information.

**Endpoint:** `GET /api/auth/profile/`

**Authentication:** Required

**Headers:**
```
Authorization: Token <your-token>
```

**Success Response (200):**
```json
{
  "id": "69371de04541c2393d28e89b",
  "user_id": 3,
  "username": "johndoe",
  "email": "john@example.com",
  "height": 180,
  "weight": "75.00",
  "date_of_birth": "1990-01-15",
  "fitness_goal": "weight_gain",
  "created_at": "2025-12-08T18:50:08.931000Z",
  "updated_at": "2025-12-08T18:51:34.694000Z"
}
```

---

### Update Profile

Update the current user's profile information.

**Endpoint:** `PUT /api/auth/profile/`

**Authentication:** Required

**Headers:**
```
Authorization: Token <your-token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "height": 180,
  "weight": 75,
  "date_of_birth": "1990-01-15",
  "fitness_goal": "weight_gain"
}
```

**Fitness Goal Options:**
- `strength`
- `cardio`
- `weight_loss`
- `weight_gain`
- `endurance`
- `flexibility`
- `general`

**Success Response (200):**
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": 3,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "profile": {
    "id": "69371de04541c2393d28e89b",
    "user_id": 3,
    "username": "johndoe",
    "email": "john@example.com",
    "height": 180,
    "weight": "75.00",
    "date_of_birth": "1990-01-15",
    "fitness_goal": "weight_gain",
    "created_at": "2025-12-08T18:50:08.931000Z",
    "updated_at": "2025-12-08T18:55:12.123456Z"
  }
}
```

---

## Exercise Endpoints

### List Exercises

Retrieve a list of all exercises. Supports filtering and pagination.

**Endpoint:** `GET /api/exercises/`

**Authentication:** Required

**Query Parameters:**
- `category` - Filter by category (e.g., `strength`, `cardio`)
- `muscle_group` - Filter by muscle group (e.g., `chest`, `legs`)
- `difficulty` - Filter by difficulty (e.g., `beginner`, `intermediate`, `advanced`)
- `page` - Page number for pagination
- `page_size` - Number of results per page

**Example Request:**
```
GET /api/exercises/?category=strength&muscle_group=chest
```

**Success Response (200):**
```json
{
  "count": 2,
  "results": [
    {
      "id": "69371e6c7499f559128d9ccc",
      "name": "Bench Press",
      "category": "strength",
      "difficulty": "intermediate",
      "muscle_groups": []
    },
    {
      "id": "69371e74b67526e7d2f46f91",
      "name": "Squat",
      "category": "strength",
      "difficulty": "intermediate",
      "muscle_groups": []
    }
  ]
}
```

---

### Get Exercise Details

Retrieve detailed information about a specific exercise.

**Endpoint:** `GET /api/exercises/{exercise_id}/`

**Authentication:** Required

**Success Response (200):**
```json
{
  "id": "69371e6c7499f559128d9ccc",
  "name": "Bench Press",
  "description": "Classic chest exercise",
  "category": "strength",
  "muscle_groups": [],
  "equipment_required": [],
  "difficulty": "intermediate",
  "video_url": null,
  "image_url": null,
  "instructions": [],
  "created_at": "2025-12-08T18:52:28.593704Z",
  "updated_at": "2025-12-08T18:52:28.593822Z"
}
```

---

### Create Exercise

Create a new exercise (admin only).

**Endpoint:** `POST /api/exercises/`

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "name": "Bench Press",
  "description": "Classic chest exercise",
  "category": "strength",
  "muscle_group": "chest",
  "equipment": "barbell",
  "difficulty": "intermediate",
  "video_url": "https://example.com/video.mp4",
  "image_url": "https://example.com/image.jpg",
  "instructions": ["Step 1", "Step 2"]
}
```

**Category Options:**
- `strength`
- `cardio`
- `flexibility`
- `balance`
- `other`

**Difficulty Options:**
- `beginner`
- `intermediate`
- `advanced`

**Success Response (201):**
```json
{
  "id": "69371e6c7499f559128d9ccc",
  "name": "Bench Press",
  "description": "Classic chest exercise",
  "category": "strength",
  "muscle_groups": [],
  "equipment_required": [],
  "difficulty": "intermediate",
  "video_url": "https://example.com/video.mp4",
  "image_url": "https://example.com/image.jpg",
  "instructions": [],
  "created_at": "2025-12-08T18:52:28.593704Z",
  "updated_at": "2025-12-08T18:52:28.593822Z"
}
```

**Error Response (403):**
```json
{
  "error": "Only administrators can create exercises"
}
```

---

### Update Exercise

Update an existing exercise (admin only).

**Endpoint:** `PUT /api/exercises/{exercise_id}/`

**Authentication:** Required (Admin)

**Request Body:** Same as Create Exercise

---

### Delete Exercise

Delete an exercise (admin only).

**Endpoint:** `DELETE /api/exercises/{exercise_id}/`

**Authentication:** Required (Admin)

**Success Response (204):** No content

---

## Workout Endpoints

### List Workouts

Retrieve a list of workouts for the authenticated user.

**Endpoint:** `GET /api/workouts/`

**Authentication:** Required

**Query Parameters:**
- `difficulty` - Filter by difficulty
- `page` - Page number for pagination
- `page_size` - Number of results per page

**Success Response (200):**
```json
{
  "count": 1,
  "results": [
    {
      "id": "workout_id_123",
      "title": "Push Day",
      "description": "Upper body push workout",
      "difficulty": "intermediate",
      "exercises": [
        {
          "exercise_id": "69371e6c7499f559128d9ccc",
          "sets": 3,
          "reps": 10,
          "order": 1
        }
      ],
      "created_at": "2025-12-08T10:00:00Z",
      "updated_at": "2025-12-08T10:00:00Z"
    }
  ]
}
```

---

### Get Workout Details

Retrieve detailed information about a specific workout.

**Endpoint:** `GET /api/workouts/{workout_id}/`

**Authentication:** Required

---

### Create Workout

Create a new workout plan.

**Endpoint:** `POST /api/workouts/`

**Authentication:** Required

**Request Body:**
```json
{
  "title": "Push Day",
  "description": "Upper body push workout",
  "difficulty": "intermediate",
  "exercises": [
    {
      "exercise_id": "69371e6c7499f559128d9ccc",
      "sets": 3,
      "reps": 10,
      "order": 1
    },
    {
      "exercise_id": "69371e74b67526e7d2f46f91",
      "sets": 4,
      "reps": 8,
      "order": 2
    }
  ]
}
```

**Success Response (201):** Returns created workout

---

### Update Workout

Update an existing workout.

**Endpoint:** `PUT /api/workouts/{workout_id}/`

**Authentication:** Required

**Request Body:** Same as Create Workout

---

### Delete Workout

Delete a workout.

**Endpoint:** `DELETE /api/workouts/{workout_id}/`

**Authentication:** Required

**Success Response (204):** No content

---

## Workout Session Endpoints

### List Workout Sessions

Retrieve a list of workout sessions for the authenticated user.

**Endpoint:** `GET /api/sessions/`

**Authentication:** Required

**Query Parameters:**
- `date` - Filter by date (format: YYYY-MM-DD)
- `workout_id` - Filter by workout ID
- `page` - Page number for pagination
- `page_size` - Number of results per page

**Success Response (200):**
```json
{
  "count": 1,
  "results": [
    {
      "id": "session_id_123",
      "workout_id": "workout_id_123",
      "user_id": 3,
      "date": "2025-12-08",
      "duration": 60,
      "notes": "Great workout!",
      "created_at": "2025-12-08T10:00:00Z",
      "updated_at": "2025-12-08T10:00:00Z"
    }
  ]
}
```

---

### Get Session Details

Retrieve detailed information about a specific workout session.

**Endpoint:** `GET /api/sessions/{session_id}/`

**Authentication:** Required

---

### Create Workout Session

Create a new workout session.

**Endpoint:** `POST /api/sessions/`

**Authentication:** Required

**Request Body:**
```json
{
  "workout_id": "workout_id_123",
  "date": "2025-12-08",
  "duration": 60,
  "notes": "Great workout!"
}
```

**Required Fields:**
- `workout_id` - ID of the workout plan
- `date` - Date of the session (YYYY-MM-DD)

**Optional Fields:**
- `duration` - Duration in minutes
- `notes` - Session notes

**Success Response (201):** Returns created session

---

### Update Workout Session

Update an existing workout session.

**Endpoint:** `PUT /api/sessions/{session_id}/`

**Authentication:** Required

**Request Body:** Same as Create Workout Session

---

### Delete Workout Session

Delete a workout session.

**Endpoint:** `DELETE /api/sessions/{session_id}/`

**Authentication:** Required

**Success Response (204):** No content

---

## Exercise Log Endpoints

### List Exercise Logs

Retrieve a list of exercise logs for the authenticated user.

**Endpoint:** `GET /api/logs/`

**Authentication:** Required

**Query Parameters:**
- `exercise_id` - Filter by exercise ID
- `session_id` - Filter by session ID
- `date` - Filter by date (format: YYYY-MM-DD)
- `page` - Page number for pagination
- `page_size` - Number of results per page

**Success Response (200):**
```json
{
  "count": 1,
  "results": [
    {
      "id": "log_id_123",
      "session_id": "session_id_123",
      "exercise_id": "69371e6c7499f559128d9ccc",
      "user_id": 3,
      "set_number": 1,
      "reps": 10,
      "weight": 80,
      "duration": null,
      "distance": null,
      "date": "2025-12-08",
      "notes": "Felt strong",
      "created_at": "2025-12-08T10:00:00Z",
      "updated_at": "2025-12-08T10:00:00Z"
    }
  ]
}
```

---

### Get Exercise Log Details

Retrieve detailed information about a specific exercise log.

**Endpoint:** `GET /api/logs/{log_id}/`

**Authentication:** Required

---

### Create Exercise Log

Create a new exercise log entry.

**Endpoint:** `POST /api/logs/`

**Authentication:** Required

**Request Body:**
```json
{
  "session_id": "session_id_123",
  "exercise_id": "69371e6c7499f559128d9ccc",
  "set_number": 1,
  "reps": 10,
  "weight": 80,
  "duration": null,
  "distance": null,
  "date": "2025-12-08",
  "notes": "Felt strong"
}
```

**Required Fields:**
- `session_id` - ID of the workout session
- `exercise_id` - ID of the exercise
- `set_number` - Set number (1, 2, 3, etc.)
- `date` - Date of the exercise (YYYY-MM-DD)

**Optional Fields:**
- `reps` - Number of repetitions
- `weight` - Weight used (in kg or lbs)
- `duration` - Duration in seconds (for cardio)
- `distance` - Distance (for cardio, in meters/km)
- `notes` - Exercise notes

**Success Response (201):** Returns created log

---

### Update Exercise Log

Update an existing exercise log.

**Endpoint:** `PUT /api/logs/{log_id}/`

**Authentication:** Required

**Request Body:** Same as Create Exercise Log

---

### Delete Exercise Log

Delete an exercise log.

**Endpoint:** `DELETE /api/logs/{log_id}/`

**Authentication:** Required

**Success Response (204):** No content

---

## Health Check

### Health Check

Check API health status.

**Endpoint:** `GET /api/health/`

**Authentication:** None required

**Success Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-08T18:00:00Z"
}
```

---

## Error Responses

### Common HTTP Status Codes

- **200 OK** - Request succeeded
- **201 Created** - Resource created successfully
- **204 No Content** - Request succeeded, no content returned
- **400 Bad Request** - Invalid request data
- **401 Unauthorized** - Missing or invalid authentication token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource not found
- **500 Internal Server Error** - Server error

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

Or for validation errors:

```json
{
  "field_name": ["Error message for this field"],
  "another_field": ["Error message for another field"]
}
```

---

## Authentication

All authenticated endpoints require the `Authorization` header with a valid token:

```
Authorization: Token <your-token-here>
```

### Example with cURL:

```bash
curl -X GET http://api.example.com/api/exercises/ \
  -H "Authorization: Token 15e89aee024a2e9af90e2ca062c6c6f91355eada"
```

### Example with JavaScript (fetch):

```javascript
fetch('http://api.example.com/api/exercises/', {
  method: 'GET',
  headers: {
    'Authorization': 'Token 15e89aee024a2e9af90e2ca062c6c6f91355eada',
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data));
```

### Example with Axios:

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://api.example.com/api',
  headers: {
    'Authorization': 'Token 15e89aee024a2e9af90e2ca062c6c6f91355eada',
    'Content-Type': 'application/json'
  }
});

// Get exercises
api.get('/exercises/')
  .then(response => console.log(response.data))
  .catch(error => console.error(error));
```

---

## Pagination

List endpoints support pagination with the following query parameters:

- `page` - Page number (default: 1)
- `page_size` - Number of items per page (default: 20, max: 100)

**Example:**
```
GET /api/exercises/?page=2&page_size=10
```

**Response includes:**
```json
{
  "count": 50,
  "next": "http://api.example.com/api/exercises/?page=3&page_size=10",
  "previous": "http://api.example.com/api/exercises/?page=1&page_size=10",
  "results": [...]
}
```

---

## Rate Limiting

*Note: Rate limiting is not currently implemented but may be added in future versions.*

---

## Support

For issues or questions, please contact the API development team or refer to the main repository documentation.
