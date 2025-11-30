# Workout API - Test Plan

## Overview

This document outlines comprehensive test scenarios for the Workout API RESTful endpoints. The API uses Django REST Framework with token-based authentication and supports CRUD operations for exercises, workouts, workout sessions, and exercise logs.

**Base URL**: `http://localhost:8000/api/`

**Authentication**: Token-based (DRF TokenAuthentication)

---

## Table of Contents

1. [Authentication Endpoints](#1-authentication-endpoints)
2. [Exercise Endpoints](#2-exercise-endpoints)
3. [Workout Endpoints](#3-workout-endpoints)
4. [Workout Session Endpoints](#4-workout-session-endpoints)
5. [Exercise Log Endpoints](#5-exercise-log-endpoints)
6. [Health Check Endpoint](#6-health-check-endpoint)
7. [Integration Test Scenarios](#7-integration-test-scenarios)
8. [Performance Test Scenarios](#8-performance-test-scenarios)
9. [Security Test Scenarios](#9-security-test-scenarios)
10. [Error Handling Test Scenarios](#10-error-handling-test-scenarios)

---

## 1. Authentication Endpoints

### 1.1 User Registration

**Endpoint**: `POST /api/auth/register/`

**Authentication**: Not required (AllowAny)

#### Test Scenarios:

##### TC-AUTH-001: Successful Registration
- **Input**:
  ```json
  {
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User"
  }
  ```
- **Expected Output**:
  - Status: 201 Created
  - Response includes user data, profile data, and authentication token
- **Validation**:
  - User created in PostgreSQL database
  - UserProfile created in MongoDB database
  - Token generated and returned

##### TC-AUTH-002: Registration with Missing Required Fields
- **Input**:
  ```json
  {
    "username": "testuser"
  }
  ```
- **Expected Output**:
  - Status: 400 Bad Request
  - Error: "Username, email, and password are required"

##### TC-AUTH-003: Registration with Password Mismatch
- **Input**:
  ```json
  {
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "password_confirm": "DifferentPass123!"
  }
  ```
- **Expected Output**:
  - Status: 400 Bad Request
  - Error: "Passwords do not match"

##### TC-AUTH-004: Registration with Weak Password
- **Input**:
  ```json
  {
    "username": "testuser",
    "email": "test@example.com",
    "password": "123",
    "password_confirm": "123"
  }
  ```
- **Expected Output**:
  - Status: 400 Bad Request
  - Error includes password validation messages

##### TC-AUTH-005: Registration with Duplicate Username
- **Precondition**: User with username "testuser" exists
- **Input**:
  ```json
  {
    "username": "testuser",
    "email": "newemail@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }
  ```
- **Expected Output**:
  - Status: 400 Bad Request
  - Error: "Username already exists"

##### TC-AUTH-006: Registration with Duplicate Email
- **Precondition**: User with email "test@example.com" exists
- **Input**:
  ```json
  {
    "username": "newuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }
  ```
- **Expected Output**:
  - Status: 400 Bad Request
  - Error: "Email already exists"

##### TC-AUTH-007: Registration with Optional Profile Fields
- **Input**:
  ```json
  {
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "height": 180,
    "weight": 75.5,
    "fitness_goal": "muscle_gain"
  }
  ```
- **Expected Output**:
  - Status: 201 Created
  - Profile includes height, weight, and fitness_goal

---

### 1.2 User Login

**Endpoint**: `POST /api/auth/login/`

**Authentication**: Not required (AllowAny)

#### Test Scenarios:

##### TC-AUTH-101: Successful Login
- **Precondition**: User exists with username "testuser" and password "SecurePass123!"
- **Input**:
  ```json
  {
    "username": "testuser",
    "password": "SecurePass123!"
  }
  ```
- **Expected Output**:
  - Status: 200 OK
  - Response includes user data, profile data, and authentication token

##### TC-AUTH-102: Login with Invalid Credentials
- **Input**:
  ```json
  {
    "username": "testuser",
    "password": "WrongPassword123!"
  }
  ```
- **Expected Output**:
  - Status: 401 Unauthorized
  - Error: "Invalid credentials"

##### TC-AUTH-103: Login with Non-existent User
- **Input**:
  ```json
  {
    "username": "nonexistent",
    "password": "SecurePass123!"
  }
  ```
- **Expected Output**:
  - Status: 401 Unauthorized
  - Error: "Invalid credentials"

##### TC-AUTH-104: Login with Missing Fields
- **Input**:
  ```json
  {
    "username": "testuser"
  }
  ```
- **Expected Output**:
  - Status: 400 Bad Request
  - Error: "Username and password are required"

##### TC-AUTH-105: Login Creates Profile if Missing
- **Precondition**: User exists but UserProfile in MongoDB was deleted
- **Input**: Valid credentials
- **Expected Output**:
  - Status: 200 OK
  - UserProfile created with default values

---

### 1.3 User Logout

**Endpoint**: `POST /api/auth/logout/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-AUTH-201: Successful Logout
- **Headers**: `Authorization: Token <valid-token>`
- **Expected Output**:
  - Status: 200 OK
  - Message: "Logout successful"
  - Token deleted from database

##### TC-AUTH-202: Logout without Authentication
- **Headers**: None
- **Expected Output**:
  - Status: 401 Unauthorized

##### TC-AUTH-203: Logout with Invalid Token
- **Headers**: `Authorization: Token invalid-token-123`
- **Expected Output**:
  - Status: 401 Unauthorized

##### TC-AUTH-204: Multiple Logout Attempts
- **Test**: Logout twice with same token
- **Expected Output**:
  - First request: 200 OK
  - Second request: 401 Unauthorized

---

### 1.4 Get Current User

**Endpoint**: `GET /api/auth/me/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-AUTH-301: Get Current User Successfully
- **Headers**: `Authorization: Token <valid-token>`
- **Expected Output**:
  - Status: 200 OK
  - Response includes user data and profile data

##### TC-AUTH-302: Get Current User without Authentication
- **Headers**: None
- **Expected Output**:
  - Status: 401 Unauthorized

##### TC-AUTH-303: Get Current User with Profile Missing
- **Precondition**: UserProfile deleted from MongoDB
- **Expected Output**:
  - Status: 200 OK
  - UserProfile created with defaults
  - OR warning about MongoDB unavailability

---

### 1.5 Update Profile

**Endpoint**: `PUT /api/auth/profile/` or `PATCH /api/auth/profile/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-AUTH-401: Update All Fields Successfully
- **Headers**: `Authorization: Token <valid-token>`
- **Input**:
  ```json
  {
    "first_name": "Updated",
    "last_name": "Name",
    "email": "updated@example.com",
    "height": 185,
    "weight": 80.0,
    "fitness_goal": "weight_loss"
  }
  ```
- **Expected Output**:
  - Status: 200 OK
  - All fields updated in both PostgreSQL (User) and MongoDB (UserProfile)

##### TC-AUTH-402: Partial Update (PATCH)
- **Input**:
  ```json
  {
    "weight": 78.5
  }
  ```
- **Expected Output**:
  - Status: 200 OK
  - Only weight field updated

##### TC-AUTH-403: Update with Duplicate Email
- **Precondition**: Another user has email "existing@example.com"
- **Input**:
  ```json
  {
    "email": "existing@example.com"
  }
  ```
- **Expected Output**:
  - Status: 400 Bad Request
  - Error: "Email already exists"

##### TC-AUTH-404: Update without Authentication
- **Headers**: None
- **Expected Output**:
  - Status: 401 Unauthorized

---

### 1.6 Change Password

**Endpoint**: `POST /api/auth/change-password/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-AUTH-501: Change Password Successfully
- **Headers**: `Authorization: Token <valid-token>`
- **Input**:
  ```json
  {
    "old_password": "SecurePass123!",
    "new_password": "NewSecurePass456!",
    "new_password_confirm": "NewSecurePass456!"
  }
  ```
- **Expected Output**:
  - Status: 200 OK
  - Password changed
  - Old token deleted
  - New token returned

##### TC-AUTH-502: Change Password with Wrong Old Password
- **Input**:
  ```json
  {
    "old_password": "WrongPassword",
    "new_password": "NewSecurePass456!",
    "new_password_confirm": "NewSecurePass456!"
  }
  ```
- **Expected Output**:
  - Status: 400 Bad Request
  - Error: "Old password is incorrect"

##### TC-AUTH-503: Change Password with Mismatch
- **Input**:
  ```json
  {
    "old_password": "SecurePass123!",
    "new_password": "NewSecurePass456!",
    "new_password_confirm": "DifferentPass789!"
  }
  ```
- **Expected Output**:
  - Status: 400 Bad Request
  - Error: "New passwords do not match"

##### TC-AUTH-504: Change Password with Weak New Password
- **Input**:
  ```json
  {
    "old_password": "SecurePass123!",
    "new_password": "123",
    "new_password_confirm": "123"
  }
  ```
- **Expected Output**:
  - Status: 400 Bad Request
  - Error includes password validation messages

##### TC-AUTH-505: Old Token Invalid After Password Change
- **Test**: Use old token after password change
- **Expected Output**:
  - Status: 401 Unauthorized

---

## 2. Exercise Endpoints

### 2.1 List Exercises

**Endpoint**: `GET /api/exercises/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-EX-001: List All Exercises
- **Headers**: `Authorization: Token <valid-token>`
- **Expected Output**:
  - Status: 200 OK
  - Paginated list of exercises
  - Includes exercises created by user and public exercises

##### TC-EX-002: List Exercises with Pagination
- **Request**: `GET /api/exercises/?page=2&page_size=10`
- **Expected Output**:
  - Status: 200 OK
  - Second page with 10 items
  - Pagination metadata included

##### TC-EX-003: Filter Exercises by Muscle Group
- **Request**: `GET /api/exercises/?muscle_group=chest`
- **Expected Output**:
  - Status: 200 OK
  - Only exercises targeting chest muscle group

##### TC-EX-004: Filter Exercises by Equipment
- **Request**: `GET /api/exercises/?equipment=barbell`
- **Expected Output**:
  - Status: 200 OK
  - Only exercises using barbell

##### TC-EX-005: Filter Exercises by Difficulty
- **Request**: `GET /api/exercises/?difficulty=intermediate`
- **Expected Output**:
  - Status: 200 OK
  - Only intermediate difficulty exercises

##### TC-EX-006: Search Exercises by Name
- **Request**: `GET /api/exercises/?search=bench press`
- **Expected Output**:
  - Status: 200 OK
  - Exercises with "bench press" in name or description

##### TC-EX-007: List Exercises without Authentication
- **Headers**: None
- **Expected Output**:
  - Status: 401 Unauthorized

##### TC-EX-008: Combined Filters
- **Request**: `GET /api/exercises/?muscle_group=legs&equipment=bodyweight&difficulty=beginner`
- **Expected Output**:
  - Status: 200 OK
  - Exercises matching all criteria

---

### 2.2 Create Exercise

**Endpoint**: `POST /api/exercises/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-EX-101: Create Exercise Successfully
- **Headers**: `Authorization: Token <valid-token>`
- **Input**:
  ```json
  {
    "name": "Barbell Bench Press",
    "description": "Classic chest exercise",
    "muscle_group": "chest",
    "equipment": "barbell",
    "difficulty": "intermediate",
    "instructions": "Lie on bench, lower bar to chest, press up"
  }
  ```
- **Expected Output**:
  - Status: 201 Created
  - Exercise created with created_by set to current user

##### TC-EX-102: Create Exercise with Missing Required Fields
- **Input**:
  ```json
  {
    "name": "Bench Press"
  }
  ```
- **Expected Output**:
  - Status: 400 Bad Request
  - Error listing missing required fields

##### TC-EX-103: Create Exercise with Invalid Muscle Group
- **Input**:
  ```json
  {
    "name": "Test Exercise",
    "muscle_group": "invalid_muscle",
    "equipment": "barbell",
    "difficulty": "beginner"
  }
  ```
- **Expected Output**:
  - Status: 400 Bad Request
  - Error: Invalid muscle group choice

##### TC-EX-104: Create Exercise without Authentication
- **Headers**: None
- **Expected Output**:
  - Status: 401 Unauthorized

##### TC-EX-105: Create Public Exercise (Admin Only)
- **Precondition**: User is admin/staff
- **Input**:
  ```json
  {
    "name": "Public Exercise",
    "muscle_group": "chest",
    "equipment": "barbell",
    "difficulty": "beginner",
    "is_public": true
  }
  ```
- **Expected Output**:
  - Status: 201 Created
  - Exercise is public

##### TC-EX-106: Create Public Exercise (Non-Admin)
- **Precondition**: User is not admin/staff
- **Input**: Same as TC-EX-105
- **Expected Output**:
  - Status: 403 Forbidden
  - OR is_public flag ignored

---

### 2.3 Retrieve Exercise

**Endpoint**: `GET /api/exercises/{id}/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-EX-201: Retrieve Own Exercise
- **Request**: `GET /api/exercises/1/`
- **Precondition**: Exercise ID 1 belongs to current user
- **Expected Output**:
  - Status: 200 OK
  - Full exercise details

##### TC-EX-202: Retrieve Public Exercise
- **Request**: `GET /api/exercises/2/`
- **Precondition**: Exercise ID 2 is public
- **Expected Output**:
  - Status: 200 OK
  - Full exercise details

##### TC-EX-203: Retrieve Other User's Private Exercise
- **Request**: `GET /api/exercises/3/`
- **Precondition**: Exercise ID 3 belongs to another user and is private
- **Expected Output**:
  - Status: 404 Not Found
  - OR 403 Forbidden

##### TC-EX-204: Retrieve Non-existent Exercise
- **Request**: `GET /api/exercises/99999/`
- **Expected Output**:
  - Status: 404 Not Found

---

### 2.4 Update Exercise

**Endpoint**: `PUT /api/exercises/{id}/` or `PATCH /api/exercises/{id}/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-EX-301: Update Own Exercise
- **Request**: `PUT /api/exercises/1/`
- **Precondition**: Exercise ID 1 belongs to current user
- **Input**:
  ```json
  {
    "name": "Updated Bench Press",
    "muscle_group": "chest",
    "equipment": "barbell",
    "difficulty": "advanced"
  }
  ```
- **Expected Output**:
  - Status: 200 OK
  - Exercise updated

##### TC-EX-302: Partial Update (PATCH)
- **Request**: `PATCH /api/exercises/1/`
- **Input**:
  ```json
  {
    "difficulty": "advanced"
  }
  ```
- **Expected Output**:
  - Status: 200 OK
  - Only difficulty updated

##### TC-EX-303: Update Other User's Exercise
- **Request**: `PUT /api/exercises/2/`
- **Precondition**: Exercise ID 2 belongs to another user
- **Expected Output**:
  - Status: 403 Forbidden

##### TC-EX-304: Admin Update Any Exercise
- **Precondition**: Current user is admin
- **Request**: `PUT /api/exercises/2/`
- **Expected Output**:
  - Status: 200 OK
  - Exercise updated

---

### 2.5 Delete Exercise

**Endpoint**: `DELETE /api/exercises/{id}/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-EX-401: Delete Own Exercise
- **Request**: `DELETE /api/exercises/1/`
- **Precondition**: Exercise ID 1 belongs to current user
- **Expected Output**:
  - Status: 204 No Content
  - Exercise deleted from MongoDB

##### TC-EX-402: Delete Other User's Exercise
- **Request**: `DELETE /api/exercises/2/`
- **Precondition**: Exercise ID 2 belongs to another user
- **Expected Output**:
  - Status: 403 Forbidden

##### TC-EX-403: Delete Exercise Used in Workouts
- **Precondition**: Exercise is referenced in active workouts
- **Expected Output**:
  - Status: 400 Bad Request (if cascade delete not allowed)
  - OR 204 No Content (if cascade delete implemented)

---

## 3. Workout Endpoints

### 3.1 List Workouts

**Endpoint**: `GET /api/workouts/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-WO-001: List All User's Workouts
- **Headers**: `Authorization: Token <valid-token>`
- **Expected Output**:
  - Status: 200 OK
  - Paginated list of workouts created by user

##### TC-WO-002: Filter Workouts by Difficulty
- **Request**: `GET /api/workouts/?difficulty=intermediate`
- **Expected Output**:
  - Status: 200 OK
  - Only intermediate workouts

##### TC-WO-003: Filter Workouts by Goal
- **Request**: `GET /api/workouts/?goal=muscle_gain`
- **Expected Output**:
  - Status: 200 OK
  - Only muscle gain workouts

##### TC-WO-004: Search Workouts by Name
- **Request**: `GET /api/workouts/?search=push day`
- **Expected Output**:
  - Status: 200 OK
  - Workouts matching "push day"

##### TC-WO-005: Filter Public Workouts
- **Request**: `GET /api/workouts/?is_public=true`
- **Expected Output**:
  - Status: 200 OK
  - Only public workouts

---

### 3.2 Create Workout

**Endpoint**: `POST /api/workouts/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-WO-101: Create Workout Successfully
- **Headers**: `Authorization: Token <valid-token>`
- **Input**:
  ```json
  {
    "name": "Push Day A",
    "description": "Chest, shoulders, triceps",
    "difficulty": "intermediate",
    "estimated_duration": 60,
    "goal": "muscle_gain",
    "exercises": [
      {
        "exercise_id": "64abc123...",
        "sets": 4,
        "reps": 8,
        "rest_period": 90,
        "order": 1
      },
      {
        "exercise_id": "64abc456...",
        "sets": 3,
        "reps": 12,
        "rest_period": 60,
        "order": 2
      }
    ]
  }
  ```
- **Expected Output**:
  - Status: 201 Created
  - Workout created with exercises

##### TC-WO-102: Create Workout with No Exercises
- **Input**:
  ```json
  {
    "name": "Empty Workout",
    "difficulty": "beginner",
    "exercises": []
  }
  ```
- **Expected Output**:
  - Status: 201 Created (if allowed)
  - OR 400 Bad Request (if exercises required)

##### TC-WO-103: Create Workout with Invalid Exercise ID
- **Input**:
  ```json
  {
    "name": "Test Workout",
    "difficulty": "beginner",
    "exercises": [
      {
        "exercise_id": "invalid-id-123",
        "sets": 3,
        "reps": 10
      }
    ]
  }
  ```
- **Expected Output**:
  - Status: 400 Bad Request
  - Error: Invalid exercise ID

##### TC-WO-104: Create Workout with Missing Required Fields
- **Input**:
  ```json
  {
    "name": "Test Workout"
  }
  ```
- **Expected Output**:
  - Status: 400 Bad Request
  - Error listing missing fields

---

### 3.3 Retrieve Workout

**Endpoint**: `GET /api/workouts/{id}/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-WO-201: Retrieve Own Workout
- **Request**: `GET /api/workouts/64abc123.../`
- **Expected Output**:
  - Status: 200 OK
  - Full workout details with nested exercises

##### TC-WO-202: Retrieve Public Workout
- **Request**: `GET /api/workouts/64abc456.../`
- **Precondition**: Workout is public
- **Expected Output**:
  - Status: 200 OK
  - Full workout details

##### TC-WO-203: Retrieve Other User's Private Workout
- **Expected Output**:
  - Status: 404 Not Found or 403 Forbidden

---

### 3.4 Update Workout

**Endpoint**: `PUT /api/workouts/{id}/` or `PATCH /api/workouts/{id}/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-WO-301: Update Workout Details
- **Request**: `PATCH /api/workouts/64abc123.../`
- **Input**:
  ```json
  {
    "name": "Updated Push Day",
    "difficulty": "advanced"
  }
  ```
- **Expected Output**:
  - Status: 200 OK
  - Workout updated

##### TC-WO-302: Update Workout Exercises
- **Request**: `PUT /api/workouts/64abc123.../`
- **Input**: Full workout with modified exercises array
- **Expected Output**:
  - Status: 200 OK
  - Exercises updated

##### TC-WO-303: Reorder Exercises
- **Input**:
  ```json
  {
    "exercises": [
      {"exercise_id": "64abc456...", "sets": 3, "reps": 10, "order": 1},
      {"exercise_id": "64abc123...", "sets": 4, "reps": 8, "order": 2}
    ]
  }
  ```
- **Expected Output**:
  - Status: 200 OK
  - Exercise order updated

---

### 3.5 Delete Workout

**Endpoint**: `DELETE /api/workouts/{id}/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-WO-401: Delete Own Workout
- **Request**: `DELETE /api/workouts/64abc123.../`
- **Expected Output**:
  - Status: 204 No Content

##### TC-WO-402: Delete Workout with Active Sessions
- **Precondition**: Workout has associated workout sessions
- **Expected Output**:
  - Status: 400 Bad Request (if sessions must be deleted first)
  - OR 204 No Content (if cascade delete)

---

### 3.6 Clone Workout

**Endpoint**: `POST /api/workouts/{id}/clone/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-WO-501: Clone Own Workout
- **Request**: `POST /api/workouts/64abc123.../clone/`
- **Expected Output**:
  - Status: 201 Created
  - New workout created with same exercises
  - Name includes "(Copy)" or similar

##### TC-WO-502: Clone Public Workout
- **Request**: `POST /api/workouts/64abc456.../clone/`
- **Precondition**: Workout is public
- **Expected Output**:
  - Status: 201 Created
  - Workout cloned to user's library

##### TC-WO-503: Clone Other User's Private Workout
- **Expected Output**:
  - Status: 403 Forbidden

---

## 4. Workout Session Endpoints

### 4.1 List Workout Sessions

**Endpoint**: `GET /api/sessions/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-SES-001: List All Sessions
- **Expected Output**:
  - Status: 200 OK
  - Paginated list of user's workout sessions

##### TC-SES-002: Filter Sessions by Status
- **Request**: `GET /api/sessions/?status=completed`
- **Expected Output**:
  - Only completed sessions

##### TC-SES-003: Filter Sessions by Date Range
- **Request**: `GET /api/sessions/?start_date=2024-01-01&end_date=2024-01-31`
- **Expected Output**:
  - Sessions within January 2024

##### TC-SES-004: Filter Sessions by Workout
- **Request**: `GET /api/sessions/?workout=64abc123...`
- **Expected Output**:
  - Sessions for specific workout

---

### 4.2 Create Workout Session

**Endpoint**: `POST /api/sessions/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-SES-101: Create Session Successfully
- **Input**:
  ```json
  {
    "workout_id": "64abc123...",
    "scheduled_date": "2024-12-01T10:00:00Z",
    "notes": "Morning workout"
  }
  ```
- **Expected Output**:
  - Status: 201 Created
  - Session created with status "scheduled"

##### TC-SES-102: Create Session with Invalid Workout ID
- **Input**:
  ```json
  {
    "workout_id": "invalid-id",
    "scheduled_date": "2024-12-01T10:00:00Z"
  }
  ```
- **Expected Output**:
  - Status: 400 Bad Request

##### TC-SES-103: Create Session for Other User's Workout
- **Precondition**: Workout belongs to another user
- **Expected Output**:
  - Status: 403 Forbidden
  - OR 400 Bad Request

---

### 4.3 Start Workout Session

**Endpoint**: `POST /api/sessions/{id}/start/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-SES-201: Start Scheduled Session
- **Precondition**: Session status is "scheduled"
- **Request**: `POST /api/sessions/64def123.../start/`
- **Expected Output**:
  - Status: 200 OK
  - Session status changed to "in_progress"
  - started_at timestamp set

##### TC-SES-202: Start Already Started Session
- **Precondition**: Session status is "in_progress"
- **Expected Output**:
  - Status: 400 Bad Request
  - Error: "Session already started"

##### TC-SES-203: Start Completed Session
- **Precondition**: Session status is "completed"
- **Expected Output**:
  - Status: 400 Bad Request
  - Error: "Cannot start completed session"

---

### 4.4 Complete Workout Session

**Endpoint**: `POST /api/sessions/{id}/complete/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-SES-301: Complete In-Progress Session
- **Precondition**: Session status is "in_progress"
- **Request**: `POST /api/sessions/64def123.../complete/`
- **Input** (optional):
  ```json
  {
    "duration": 65,
    "notes": "Great workout!"
  }
  ```
- **Expected Output**:
  - Status: 200 OK
  - Session status changed to "completed"
  - completed_at timestamp set

##### TC-SES-302: Complete Scheduled Session
- **Precondition**: Session status is "scheduled" (never started)
- **Expected Output**:
  - Status: 400 Bad Request
  - Error: "Session must be started first"

##### TC-SES-303: Complete Already Completed Session
- **Expected Output**:
  - Status: 400 Bad Request

---

### 4.5 Retrieve Workout Session

**Endpoint**: `GET /api/sessions/{id}/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-SES-401: Retrieve Own Session
- **Expected Output**:
  - Status: 200 OK
  - Full session details with workout and exercise logs

##### TC-SES-402: Retrieve Other User's Session
- **Expected Output**:
  - Status: 404 Not Found or 403 Forbidden

---

### 4.6 Update Workout Session

**Endpoint**: `PATCH /api/sessions/{id}/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-SES-501: Update Session Notes
- **Input**:
  ```json
  {
    "notes": "Updated notes"
  }
  ```
- **Expected Output**:
  - Status: 200 OK

##### TC-SES-502: Update Scheduled Date
- **Precondition**: Session is scheduled (not started)
- **Input**:
  ```json
  {
    "scheduled_date": "2024-12-02T10:00:00Z"
  }
  ```
- **Expected Output**:
  - Status: 200 OK

##### TC-SES-503: Update Completed Session
- **Precondition**: Session is completed
- **Expected Output**:
  - Status: 400 Bad Request (if editing completed sessions not allowed)
  - OR 200 OK (if notes can be updated)

---

### 4.7 Delete Workout Session

**Endpoint**: `DELETE /api/sessions/{id}/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-SES-601: Delete Scheduled Session
- **Expected Output**:
  - Status: 204 No Content

##### TC-SES-602: Delete In-Progress Session
- **Expected Output**:
  - Status: 400 Bad Request (if deletion not allowed)
  - OR confirmation required

##### TC-SES-603: Delete Completed Session
- **Expected Output**:
  - Status: 400 Bad Request (preserve workout history)
  - OR 204 No Content (if allowed)

---

## 5. Exercise Log Endpoints

### 5.1 List Exercise Logs

**Endpoint**: `GET /api/logs/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-LOG-001: List All Exercise Logs
- **Expected Output**:
  - Status: 200 OK
  - Paginated list of user's exercise logs

##### TC-LOG-002: Filter Logs by Session
- **Request**: `GET /api/logs/?session=64def123...`
- **Expected Output**:
  - Logs for specific session

##### TC-LOG-003: Filter Logs by Exercise
- **Request**: `GET /api/logs/?exercise=64abc123...`
- **Expected Output**:
  - All logs for specific exercise (progress tracking)

##### TC-LOG-004: Filter Logs by Date Range
- **Request**: `GET /api/logs/?start_date=2024-01-01&end_date=2024-01-31`
- **Expected Output**:
  - Logs within date range

---

### 5.2 Create Exercise Log

**Endpoint**: `POST /api/logs/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-LOG-101: Log Exercise with Sets
- **Input**:
  ```json
  {
    "session_id": "64def123...",
    "exercise_id": "64abc123...",
    "sets_completed": 4,
    "reps_completed": [10, 8, 8, 6],
    "weight": [100, 100, 110, 110],
    "notes": "Increased weight on last 2 sets"
  }
  ```
- **Expected Output**:
  - Status: 201 Created
  - Log created with detailed set data

##### TC-LOG-102: Log Bodyweight Exercise
- **Input**:
  ```json
  {
    "session_id": "64def123...",
    "exercise_id": "64abc456...",
    "sets_completed": 3,
    "reps_completed": [15, 12, 10],
    "weight": []
  }
  ```
- **Expected Output**:
  - Status: 201 Created

##### TC-LOG-103: Log Time-Based Exercise
- **Input**:
  ```json
  {
    "session_id": "64def123...",
    "exercise_id": "64abc789...",
    "duration": 300,
    "notes": "5-minute plank"
  }
  ```
- **Expected Output**:
  - Status: 201 Created

##### TC-LOG-104: Log for Non-Existent Session
- **Input**:
  ```json
  {
    "session_id": "invalid-id",
    "exercise_id": "64abc123...",
    "sets_completed": 3
  }
  ```
- **Expected Output**:
  - Status: 400 Bad Request

##### TC-LOG-105: Log for Other User's Session
- **Precondition**: Session belongs to another user
- **Expected Output**:
  - Status: 403 Forbidden

---

### 5.3 Retrieve Exercise Log

**Endpoint**: `GET /api/logs/{id}/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-LOG-201: Retrieve Own Log
- **Expected Output**:
  - Status: 200 OK
  - Full log details

##### TC-LOG-202: Retrieve Other User's Log
- **Expected Output**:
  - Status: 404 Not Found or 403 Forbidden

---

### 5.4 Update Exercise Log

**Endpoint**: `PATCH /api/logs/{id}/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-LOG-301: Update Log Data
- **Input**:
  ```json
  {
    "reps_completed": [10, 10, 8, 6],
    "notes": "Corrected rep count"
  }
  ```
- **Expected Output**:
  - Status: 200 OK

##### TC-LOG-302: Update Completed Session's Log
- **Precondition**: Associated session is completed
- **Expected Output**:
  - Status: 200 OK (if edits allowed)
  - OR 400 Bad Request

---

### 5.5 Delete Exercise Log

**Endpoint**: `DELETE /api/logs/{id}/`

**Authentication**: Required (Token)

#### Test Scenarios:

##### TC-LOG-401: Delete Log
- **Expected Output**:
  - Status: 204 No Content

##### TC-LOG-402: Delete Log from Completed Session
- **Expected Output**:
  - Status: 400 Bad Request (preserve workout history)
  - OR 204 No Content (if allowed)

---

## 6. Health Check Endpoint

### 6.1 Health Check

**Endpoint**: `GET /api/health/`

**Authentication**: Not required (AllowAny)

#### Test Scenarios:

##### TC-HEALTH-001: Health Check Success
- **Expected Output**:
  - Status: 200 OK
  - Response:
    ```json
    {
      "status": "healthy",
      "service": "workout-api"
    }
    ```

##### TC-HEALTH-002: Health Check from Docker/K8s
- **Context**: Used by container orchestration
- **Expected Output**:
  - Status: 200 OK
  - Fast response time (<100ms)

---

## 7. Integration Test Scenarios

### 7.1 Complete Workout Flow

**Scenario**: User creates a workout and completes a session

1. Register user (TC-AUTH-001)
2. Login (TC-AUTH-101)
3. Create exercises (TC-EX-101) × 3
4. Create workout with exercises (TC-WO-101)
5. Create workout session (TC-SES-101)
6. Start session (TC-SES-201)
7. Log exercises (TC-LOG-101) × 3
8. Complete session (TC-SES-301)
9. Verify session data (TC-SES-401)

**Expected Result**: Complete workout session with all exercise logs recorded

---

### 7.2 Progress Tracking Flow

**Scenario**: User tracks progress over multiple sessions

1. Create workout
2. Complete session #1, log weights
3. Complete session #2, log increased weights
4. Complete session #3, log further increases
5. Query exercise logs filtered by exercise ID
6. Verify progressive overload

**Expected Result**: Exercise logs show weight progression over time

---

### 7.3 Workout Sharing Flow

**Scenario**: User creates public workout, another user clones it

1. User A creates workout
2. User A makes workout public
3. User B searches public workouts
4. User B clones User A's workout
5. User B completes session with cloned workout

**Expected Result**: User B has independent copy of workout

---

### 7.4 Profile Management Flow

**Scenario**: User updates profile and tracks body measurements

1. Register with initial height/weight
2. Update profile after 1 month with new weight
3. Update profile after 2 months with new weight
4. Query profile history (if versioning implemented)

**Expected Result**: Profile reflects current stats

---

## 8. Performance Test Scenarios

### 8.1 Load Testing

#### Scenario: Concurrent Users

- **Test**: 100 concurrent users listing exercises
- **Expected**: <2s response time for 95th percentile
- **Metrics**: Throughput, error rate, response time

#### Scenario: Bulk Data Creation

- **Test**: Create 1000 exercise logs in a session
- **Expected**: All logs created successfully, <5s total time
- **Metrics**: Database performance, serialization time

#### Scenario: Complex Query

- **Test**: Search exercises with multiple filters + pagination
- **Expected**: <500ms response time
- **Metrics**: Database query optimization, index usage

---

### 8.2 Stress Testing

#### Scenario: API Rate Limiting

- **Test**: 1000 requests/minute from single user
- **Expected**: Rate limiting triggered, 429 status returned
- **Metrics**: Rate limiter effectiveness

#### Scenario: Large Payload

- **Test**: Create workout with 50 exercises
- **Expected**: Successfully created or validation error
- **Metrics**: Payload size limits, serialization performance

---

## 9. Security Test Scenarios

### 9.1 Authentication & Authorization

#### TC-SEC-001: Access Without Token
- **Test**: Access protected endpoint without Authorization header
- **Expected**: 401 Unauthorized

#### TC-SEC-002: Access with Expired Token
- **Test**: Use token after logout/expiry
- **Expected**: 401 Unauthorized

#### TC-SEC-003: Access Other User's Resources
- **Test**: Attempt to modify another user's workout
- **Expected**: 403 Forbidden or 404 Not Found

#### TC-SEC-004: Token Leakage
- **Test**: Verify tokens not included in logs/error messages
- **Expected**: No sensitive data in responses

---

### 9.2 Input Validation

#### TC-SEC-101: SQL Injection Attempt
- **Test**: Send SQL injection payloads in search queries
- **Expected**: Input sanitized, no database errors

#### TC-SEC-102: XSS Attempt
- **Test**: Submit JavaScript in text fields
- **Expected**: Content escaped in responses

#### TC-SEC-103: Oversized Payload
- **Test**: Send extremely large JSON payload
- **Expected**: 413 Payload Too Large or 400 Bad Request

#### TC-SEC-104: Invalid JSON
- **Test**: Send malformed JSON
- **Expected**: 400 Bad Request with clear error

---

### 9.3 CORS Testing

#### TC-SEC-201: CORS Pre-flight
- **Test**: OPTIONS request from allowed origin
- **Expected**: Correct CORS headers returned

#### TC-SEC-202: CORS from Disallowed Origin
- **Test**: Request from non-whitelisted origin
- **Expected**: CORS headers not present or request blocked

---

## 10. Error Handling Test Scenarios

### 10.1 Database Errors

#### TC-ERR-001: MongoDB Connection Lost
- **Test**: Simulate MongoDB unavailability
- **Expected**: Graceful degradation, appropriate error message

#### TC-ERR-002: PostgreSQL Connection Lost
- **Test**: Simulate PostgreSQL unavailability
- **Expected**: 500 Internal Server Error, authentication fails

#### TC-ERR-003: Database Timeout
- **Test**: Simulate slow database query
- **Expected**: Timeout error, no hanging requests

---

### 10.2 Validation Errors

#### TC-ERR-101: Invalid Date Format
- **Test**: Send date in wrong format
- **Expected**: 400 Bad Request, clear error message

#### TC-ERR-102: Negative Numbers
- **Test**: Send negative values for sets/reps
- **Expected**: Validation error

#### TC-ERR-103: Missing Required Fields
- **Test**: Omit required fields
- **Expected**: 400 Bad Request listing missing fields

---

### 10.3 Network Errors

#### TC-ERR-201: Request Timeout
- **Test**: Simulate slow client connection
- **Expected**: Timeout after configured duration

#### TC-ERR-202: Partial Data Transmission
- **Test**: Interrupt request mid-transmission
- **Expected**: Connection closed, no partial data saved

---

## Test Execution Checklist

### Pre-Execution
- [ ] Test environment setup (database, Redis, etc.)
- [ ] Test data prepared
- [ ] API server running
- [ ] Authentication tokens generated

### During Execution
- [ ] Log all test results
- [ ] Capture response times
- [ ] Monitor database performance
- [ ] Check logs for errors/warnings

### Post-Execution
- [ ] Clean up test data
- [ ] Analyze failed tests
- [ ] Generate test report
- [ ] Update documentation

---

## Test Data Requirements

### Users
- Admin user
- Regular user #1
- Regular user #2
- User with empty profile

### Exercises
- Public exercises (10+)
- Private exercises per user (5+)
- Various muscle groups, equipment, difficulties

### Workouts
- Public workouts (5+)
- Private workouts per user (3+)
- Workouts with varying exercise counts

### Sessions
- Scheduled sessions
- In-progress sessions
- Completed sessions
- Sessions with logs

---

## Test Tools & Frameworks

### Automated Testing
- **pytest**: Unit and integration tests
- **pytest-django**: Django-specific testing
- **factory_boy**: Test data generation
- **Faker**: Realistic fake data

### API Testing
- **Postman**: Manual API testing, collection runner
- **curl**: Command-line testing
- **httpie**: User-friendly HTTP client

### Performance Testing
- **Locust**: Load testing
- **Apache JMeter**: Stress testing
- **wrk**: HTTP benchmarking

### Monitoring
- **Django Debug Toolbar**: Development debugging
- **Sentry**: Error tracking
- **Prometheus + Grafana**: Metrics

---

## Success Criteria

### Functional Tests
- ✅ 100% of critical paths passing
- ✅ 95%+ of all test scenarios passing
- ✅ All authentication flows working
- ✅ CRUD operations for all resources working

### Performance Tests
- ✅ 95th percentile response time <2s
- ✅ API throughput >100 req/sec
- ✅ Zero timeout errors under normal load

### Security Tests
- ✅ No unauthorized access to resources
- ✅ All inputs properly validated
- ✅ No sensitive data leakage
- ✅ HTTPS enforced in production

---

## Appendix

### A. Test Environment Setup

```bash
# Start test database
kubectl -n woodez-database port-forward mongodb-1 27012:27017
kubectl -n woodez-database port-forward service/postgres-svc 5432:5432

# Activate virtual environment
source venv/bin/activate

# Run migrations
python manage.py migrate

# Load test fixtures (if available)
python manage.py loaddata test_fixtures.json

# Run tests
pytest
pytest --cov  # with coverage
```

### B. Sample Test Data

```python
# Sample user credentials for testing
TEST_USERS = {
    "admin": {
        "username": "admin",
        "password": "Admin123!",
        "email": "admin@test.com"
    },
    "user1": {
        "username": "testuser1",
        "password": "Test123!",
        "email": "user1@test.com"
    },
    "user2": {
        "username": "testuser2",
        "password": "Test123!",
        "email": "user2@test.com"
    }
}
```

### C. Response Time Benchmarks

| Endpoint | Target (p95) | Acceptable (p95) | Unacceptable (p95) |
|----------|--------------|------------------|-------------------|
| GET /api/exercises/ | <500ms | <1s | >2s |
| POST /api/exercises/ | <1s | <2s | >3s |
| GET /api/workouts/ | <1s | <2s | >3s |
| POST /api/sessions/ | <1s | <2s | >3s |
| POST /api/logs/ | <500ms | <1s | >2s |

---

**Document Version**: 1.0
**Last Updated**: 2024-11-30
**Author**: Workout API Team
**Status**: Draft
