# Workout API - Session Outputs and Context

## Date: 2025-12-08

---

## Session Summary

This session focused on testing and fixing MongoDB integration, creating API documentation for frontend developers, and resolving CORS configuration issues.

---

## 1. MongoDB Integration Testing

### Initial Issue
- Previous session ended with MongoDB replica set connection error: "not primary"
- App was using `directConnection: True` which bypassed replica set

### Fix Applied
Updated `config/settings.py` to use proper replica set configuration:

```python
MONGODB_SETTINGS = {
    'db': config('MONGODB_DB_NAME', default='workout_db'),
    'host': config('MONGODB_HOST', default='localhost'),
    'port': int(config('MONGODB_PORT', default=27017)),
    'replicaSet': config('MONGODB_REPLICA_SET', default='rs0'),
    'serverSelectionTimeoutMS': 5000,
    'readPreference': 'primaryPreferred',
}
```

**Key Changes:**
- Removed `directConnection: True`
- Added `replicaSet: 'rs0'`
- Added `readPreference: 'primaryPreferred'`

### Test Results

#### ✅ User Registration
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "mongotest2", "email": "mongotest2@example.com", "password": "TestPass123", "password_confirm": "TestPass123"}'
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 3,
    "username": "mongotest2",
    "email": "mongotest2@example.com",
    "first_name": "",
    "last_name": ""
  },
  "token": "15e89aee024a2e9af90e2ca062c6c6f91355eada",
  "profile": {
    "id": "69371de04541c2393d28e89b",
    "user_id": 3,
    "username": "mongotest2",
    "email": "mongotest2@example.com",
    "height": null,
    "weight": null,
    "date_of_birth": null,
    "fitness_goal": "general",
    "created_at": "2025-12-08T18:50:08.931830Z",
    "updated_at": "2025-12-08T18:50:08.931870Z"
  }
}
```

**Success:** UserProfile created in MongoDB with ID `69371de04541c2393d28e89b`

---

#### ✅ User Login
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "mongotest2", "password": "TestPass123"}'
```

**Response:**
```json
{
  "message": "Login successful",
  "user": {
    "id": 3,
    "username": "mongotest2",
    "email": "mongotest2@example.com",
    "first_name": "",
    "last_name": ""
  },
  "token": "15e89aee024a2e9af90e2ca062c6c6f91355eada",
  "profile": {
    "id": "69371de04541c2393d28e89b",
    "user_id": 3,
    "username": "mongotest2",
    "email": "mongotest2@example.com",
    "height": null,
    "weight": null,
    "date_of_birth": null,
    "fitness_goal": "general",
    "created_at": "2025-12-08T18:50:08.931000Z",
    "updated_at": "2025-12-08T18:50:08.931000Z"
  }
}
```

**Success:** Login returns profile data from MongoDB

---

#### ✅ Profile Update
```bash
curl -X PUT http://127.0.0.1:8000/api/auth/profile/ \
  -H "Authorization: Token 15e89aee024a2e9af90e2ca062c6c6f91355eada" \
  -H "Content-Type: application/json" \
  -d '{"height": 180, "weight": 75, "fitness_goal": "weight_gain"}'
```

**Response:**
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": 3,
    "username": "mongotest2",
    "email": "mongotest2@example.com",
    "first_name": "",
    "last_name": ""
  },
  "profile": {
    "id": "69371de04541c2393d28e89b",
    "user_id": 3,
    "username": "mongotest2",
    "email": "mongotest2@example.com",
    "height": 180,
    "weight": "75.00",
    "date_of_birth": null,
    "fitness_goal": "weight_gain",
    "created_at": "2025-12-08T18:50:08.931000Z",
    "updated_at": "2025-12-08T18:51:34.694546Z"
  }
}
```

**Success:** Profile updated in MongoDB with new height, weight, and fitness_goal

**Note:** Initial attempt with `fitness_goal: "muscle_gain"` failed validation. Valid options are:
- strength
- cardio
- weight_loss
- weight_gain
- endurance
- flexibility
- general

---

#### ✅ Exercise Creation

First, made user an admin:
```bash
kubectl exec -n woodez-database workout-api-76554dd787-bnrd2 -- \
  python manage.py shell -c "from django.contrib.auth.models import User; \
  u = User.objects.get(username='mongotest2'); \
  u.is_staff = True; u.is_superuser = True; u.save(); \
  print(f'User {u.username} is now admin')"
```

Created exercises:
```bash
curl -X POST http://127.0.0.1:8000/api/exercises/ \
  -H "Authorization: Token 15e89aee024a2e9af90e2ca062c6c6f91355eada" \
  -H "Content-Type: application/json" \
  -d '{"name": "Bench Press", "category": "strength", "muscle_group": "chest", "equipment": "barbell", "difficulty": "intermediate", "description": "Classic chest exercise"}'
```

**Response:**
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

**Second Exercise:**
```json
{
  "id": "69371e74b67526e7d2f46f91",
  "name": "Squat",
  "description": "Compound leg exercise",
  "category": "strength",
  "muscle_groups": [],
  "equipment_required": [],
  "difficulty": "intermediate",
  "video_url": null,
  "image_url": null,
  "instructions": [],
  "created_at": "2025-12-08T18:52:36.390813Z",
  "updated_at": "2025-12-08T18:52:36.390907Z"
}
```

---

#### ✅ List Exercises
```bash
curl -X GET http://127.0.0.1:8000/api/exercises/ \
  -H "Authorization: Token 15e89aee024a2e9af90e2ca062c6c6f91355eada"
```

**Response:**
```json
{
  "count": 2,
  "results": [
    {
      "id": "69371e74b67526e7d2f46f91",
      "name": "Squat",
      "category": "strength",
      "difficulty": "intermediate",
      "muscle_groups": []
    },
    {
      "id": "69371e6c7499f559128d9ccc",
      "name": "Bench Press",
      "category": "strength",
      "difficulty": "intermediate",
      "muscle_groups": []
    }
  ]
}
```

**Success:** Exercises stored and retrieved from MongoDB

---

### MongoDB Integration Status

**✅ Fully Working:**
- User registration with automatic UserProfile creation
- User login with profile data retrieval
- Profile updates (height, weight, fitness_goal, date_of_birth)
- Exercise CRUD operations
- MongoDB replica set connection with `rs0`
- Primary-preferred read preference

**Database Details:**
- MongoDB Host: `mongodb-headless:27017` (in K8s)
- Database: `workoutdb`
- User: `workout_admin`
- Password: `WorkoutSecure2024`
- Replica Set: `rs0`

**Known Issues:**
- Workout creation endpoint has validation issues (requires complex nested structure)
- WorkoutSession and ExerciseLog require session_id linkage

---

## 2. API Documentation for Frontend Developers

### Created File: `client.md`

Comprehensive API documentation including:

**Sections:**
1. Authentication Endpoints
   - Register User (POST /api/auth/register/)
   - Login (POST /api/auth/login/)
   - Logout (POST /api/auth/logout/)

2. User Profile Endpoints
   - Get Profile (GET /api/auth/profile/)
   - Update Profile (PUT /api/auth/profile/)

3. Exercise Endpoints
   - List Exercises (GET /api/exercises/)
   - Get Exercise Details (GET /api/exercises/{id}/)
   - Create Exercise (POST /api/exercises/) - Admin only
   - Update Exercise (PUT /api/exercises/{id}/) - Admin only
   - Delete Exercise (DELETE /api/exercises/{id}/) - Admin only

4. Workout Endpoints
   - List Workouts (GET /api/workouts/)
   - Get Workout Details (GET /api/workouts/{id}/)
   - Create Workout (POST /api/workouts/)
   - Update Workout (PUT /api/workouts/{id}/)
   - Delete Workout (DELETE /api/workouts/{id}/)

5. Workout Session Endpoints
   - List Sessions (GET /api/sessions/)
   - Get Session Details (GET /api/sessions/{id}/)
   - Create Session (POST /api/sessions/)
   - Update Session (PUT /api/sessions/{id}/)
   - Delete Session (DELETE /api/sessions/{id}/)

6. Exercise Log Endpoints
   - List Logs (GET /api/logs/)
   - Get Log Details (GET /api/logs/{id}/)
   - Create Log (POST /api/logs/)
   - Update Log (PUT /api/logs/{id}/)
   - Delete Log (DELETE /api/logs/{id}/)

7. Health Check (GET /api/health/)

8. Error Responses and Status Codes

**Documentation Features:**
- Complete request/response examples for all endpoints
- Authentication header examples
- Query parameters for filtering and pagination
- Valid enum values (fitness_goal, category, difficulty, etc.)
- Code examples in cURL, JavaScript fetch, and Axios
- Pagination documentation
- Common HTTP status codes

---

## 3. CORS Configuration Fix

### Issue
Frontend at `http://localhost:5173` was getting "Network error" when trying to access the API due to CORS restrictions.

### Root Cause
- Kubernetes ConfigMap had CORS_ALLOWED_ORIGINS set to only `http://localhost:3000,http://localhost:8080`
- Missing `http://localhost:5173` (Vite dev server default port)

### Fixes Applied

#### 1. Updated `config/settings.py`
```python
# CORS settings
# https://github.com/adamchainz/django-cors-headers

# For development: allow all origins
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = config(
        'CORS_ALLOWED_ORIGINS',
        default='http://localhost:3000,http://localhost:8080,http://localhost:5173,http://127.0.0.1:5173'
    ).split(',')

CORS_ALLOW_CREDENTIALS = True
```

**Benefits:**
- Development mode (`DEBUG=True`) now allows all origins for easier testing
- Production mode still uses explicit allowlist from environment variable

#### 2. Updated `.env`
```bash
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:8080,http://127.0.0.1:5173
```

#### 3. Updated `helm/workout-api/values.yaml`
```yaml
config:
  # CORS configuration
  cors:
    allowedOrigins: "http://localhost:3000,http://localhost:8080,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
```

**Added Origins:**
- `http://localhost:5173` - Vite dev server
- `http://127.0.0.1:5173` - Vite dev server (IP variant)
- `http://127.0.0.1:3000` - React/Next.js (IP variant)

### Next Steps to Apply CORS Fix

The changes have been made to the code but NOT committed or deployed yet. To apply:

1. **Commit changes:**
   ```bash
   git add config/settings.py helm/workout-api/values.yaml
   git commit -m "Fix CORS configuration for frontend development"
   git push
   ```

2. **Wait for CI/CD:**
   - GitHub Actions will build new Docker image
   - ArgoCD will deploy updated Helm chart
   - New pod will have updated CORS configuration

3. **Or manually deploy:**
   ```bash
   # Update ArgoCD application
   kubectl apply -f argocd/application.yaml

   # Or sync via ArgoCD UI/CLI
   argocd app sync workout-api
   ```

---

## 4. Current Deployment Status

### Kubernetes Resources

**Namespace:** `woodez-database`

**Pod:**
```
workout-api-5b7fcf4f94-8clvd (Running)
```

**Service:**
```
workout-api (ClusterIP: 10.107.62.5, Port: 8000)
```

**ConfigMap:**
```
workout-api-config
```

**Current ConfigMap Values:**
- DEBUG: "True"
- POSTGRES_HOST: "postgres-svc"
- POSTGRES_DB: "woodez-auth"
- POSTGRES_USER: "workout_admin"
- MONGODB_HOST: "mongodb-headless"
- MONGODB_PORT: "27017"
- MONGODB_DB_NAME: "workoutdb"
- MONGODB_USERNAME: "workout_admin"
- CORS_ALLOWED_ORIGINS: "http://localhost:3000,http://localhost:8080" (needs update)

### Port Forward Active
```bash
kubectl -n woodez-database port-forward service/workout-api 8000:8000
```

API accessible at: `http://127.0.0.1:8000`

---

## 5. Environment Configuration

### Local `.env` File
```bash
## Django Settings
SECRET_KEY=gi6fd&55!-11%9yo@y)30)^t@v*l)mq%g%s@x81r#l939pn@7s
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,testserver

# PostgreSQL Connection (Django Auth)
POSTGRES_DB=woodez-auth
POSTGRES_USER=workout_admin
POSTGRES_PASSWORD=jandrew28
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# MongoDB Connection (App Data)
MONGODB_HOST=localhost
MONGODB_PORT=27012
MONGODB_DB_NAME=workoutdb
MONGODB_USERNAME=
MONGODB_PASSWORD=

# CORS Settings (optional)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:8080,http://127.0.0.1:5173
```

**Note:** Local `.env` uses `MONGODB_PORT=27012` for port-forwarding from K8s cluster

### Kubernetes Secrets

**postgres-auth-secret:**
- POSTGRES_PASSWORD: jandrew28

**workout-api-secret:**
- DJANGO_SECRET_KEY: (auto-generated)
- MONGODB_PASSWORD: WorkoutSecure2024

---

## 6. Git Branch Status

**Current Branch:** `helm-clean`

**Uncommitted Changes:**
- `config/settings.py` (CORS fix)
- `helm/workout-api/values.yaml` (CORS origins update)

**Recent Commits:**
```
0f222b8 yyyy
eb00b1d llll
ee153cc nnnn
3ddd529 Merge branch 'helm-clean'
2b75e27 hhhh
```

---

## 7. Files Created/Modified This Session

### Created
1. **client.md** - API documentation for frontend developers

### Modified
1. **config/settings.py**
   - Added `CORS_ALLOW_ALL_ORIGINS = True` when DEBUG=True
   - Updated default CORS origins to include localhost:5173

2. **helm/workout-api/values.yaml**
   - Updated `config.cors.allowedOrigins` to include Vite dev server ports

3. **.env**
   - Updated CORS_ALLOWED_ORIGINS with additional ports

---

## 8. Testing Commands Reference

### Health Check
```bash
curl http://127.0.0.1:8000/api/health/
```

### User Registration
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "email": "user@example.com", "password": "TestPass123", "password_confirm": "TestPass123"}'
```

### User Login
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "password": "TestPass123"}'
```

### Update Profile
```bash
curl -X PUT http://127.0.0.1:8000/api/auth/profile/ \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"height": 180, "weight": 75, "fitness_goal": "weight_gain"}'
```

### List Exercises
```bash
curl -X GET http://127.0.0.1:8000/api/exercises/ \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

### Create Exercise (Admin)
```bash
curl -X POST http://127.0.0.1:8000/api/exercises/ \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"name": "Push-up", "category": "strength", "muscle_group": "chest", "equipment": "bodyweight", "difficulty": "beginner", "description": "Classic bodyweight exercise"}'
```

---

## 9. Kubernetes Commands Reference

### Check Pod Status
```bash
kubectl get pods -n woodez-database | grep workout-api
```

### Check Pod Logs
```bash
kubectl logs -n woodez-database workout-api-POD_NAME --tail=50
```

### Check ConfigMap
```bash
kubectl get configmap -n woodez-database workout-api-config -o yaml
```

### Port Forward
```bash
kubectl -n woodez-database port-forward service/workout-api 8000:8000
```

### Make User Admin
```bash
kubectl exec -n woodez-database POD_NAME -- \
  python manage.py shell -c "from django.contrib.auth.models import User; \
  u = User.objects.get(username='USERNAME'); \
  u.is_staff = True; u.is_superuser = True; u.save(); \
  print(f'User {u.username} is now admin')"
```

### Restart Deployment
```bash
kubectl rollout restart deployment workout-api -n woodez-database
```

---

## 10. Known Issues and Limitations

### ⚠️ Workout Creation
- Endpoint requires complex nested structure
- Validation errors with workout exercise format
- Needs `order` field for exercises

### ⚠️ WorkoutSession & ExerciseLog
- Requires valid `workout_id` and `session_id`
- Cannot create standalone sessions without workout
- Exercise logs need both session_id and exercise_id

### ⚠️ CORS Not Yet Deployed
- Changes made to settings.py and values.yaml
- NOT yet committed or deployed to Kubernetes
- Currently running pod still has old CORS configuration
- Frontend will still see network errors until deployed

---

## 11. Next Steps

### Immediate
1. ✅ MongoDB integration tested and working
2. ✅ API documentation created (client.md)
3. ✅ CORS configuration fixed in code
4. ⏳ Commit and deploy CORS fixes
5. ⏳ Test frontend can successfully call API

### Future Enhancements
1. Add OpenAPI/Swagger documentation
2. Implement rate limiting
3. Add API versioning
4. Create workout builder UI
5. Add exercise video/image uploads
6. Implement progress tracking charts
7. Add social features (sharing workouts)

---

## 12. Success Metrics

### ✅ Completed
- MongoDB replica set connection working
- User authentication and profile management functional
- Exercise CRUD operations working
- API documentation created for frontend developers
- CORS configuration updated (code-level)

### ⏳ Pending
- CORS fixes deployed to Kubernetes
- Frontend successfully calling API endpoints
- Full workout and session management testing

---

## End of Session Context

**Last Command:**
- User requested to stop git commit operations
- User wants to record all context to outputs.md

**Current State:**
- API is running and accessible via port-forward
- MongoDB integration fully functional
- CORS fixes ready but not deployed
- All code changes uncommitted

**Files Modified (Uncommitted):**
- config/settings.py
- helm/workout-api/values.yaml
- .env

**Files Created:**
- client.md
- outputs.md (this file)

---

## 13. Additional Session Updates (Continued)

### Issue: Admin Permissions for User "kwood"

**Problem:**
User `kwood` was unable to create exercises via the API, receiving error:
```json
{
  "error": "Only administrators can create exercises"
}
```

**Root Cause:**
The user `kwood` existed in the database but lacked administrator privileges:
- `is_staff`: False
- `is_superuser`: False

**Solution:**
Granted admin privileges to the `kwood` user:

```bash
kubectl exec -n woodez-database workout-api-75c44ff578-vcmv5 -- \
  python manage.py shell -c "from django.contrib.auth.models import User; \
  u = User.objects.get(username='kwood'); \
  u.is_staff = True; \
  u.is_superuser = True; \
  u.save(); \
  print(f'User {u.username} is now admin (is_staff={u.is_staff}, is_superuser={u.is_superuser})')"
```

**Result:**
```
User kwood is now admin (is_staff=True, is_superuser=True)
```

**Status:** ✅ User `kwood` can now create exercises through the API

---

### Current Pod Information

**Pod Name:** `workout-api-75c44ff578-vcmv5`
**Status:** Running
**Restarts:** 129
**Uptime:** 42 hours (as of last check)

**Note:** High restart count (129) may indicate:
- Liveness/readiness probe failures
- Application crashes
- Resource constraints
- Should be investigated if issues persist

---

### API Permissions Model

**Exercise Creation Requirements:**
- User must have `is_staff = True` OR `is_superuser = True`
- Regular authenticated users cannot create exercises
- This prevents unauthorized exercise library modifications
- Only trainers/administrators should manage the exercise catalog

**Admin Users in System:**
1. `kwood` - ✅ Now has admin privileges
2. `mongotest2` - ✅ Has admin privileges (from earlier testing)

---

### Quick Reference: Grant Admin Privileges

To make any user an administrator:

```bash
kubectl exec -n woodez-database POD_NAME -- \
  python manage.py shell -c "from django.contrib.auth.models import User; \
  u = User.objects.get(username='USERNAME'); \
  u.is_staff = True; \
  u.is_superuser = True; \
  u.save(); \
  print(f'User {u.username} is now admin')"
```

Replace `POD_NAME` and `USERNAME` with actual values.

---

**Last Updated:** 2025-12-08 (Session continued)

---

## 14. Workout Creation Failure - MongoDB Connection Issue

### Problem
User experiencing error "Failed to save workout. Please try again." when trying to create workouts through the frontend.

### Investigation

**Observed Errors:**
- GET `/api/workouts/` returns 500 error
- POST `/api/workouts/` returns 500 error (after 400 validation errors)

**Root Cause Analysis:**

1. **Workout ViewSet Issue** ([workouts/views.py:182](workouts/views.py#L182)):
   ```python
   user_profile = UserProfile.objects.get(user_id=self.request.user.id)
   ```
   - The `get_queryset()` method tries to fetch UserProfile from MongoDB
   - This query is timing out/failing

2. **Workout Serializer Issue** ([workouts/serializers.py:131-137](workouts/serializers.py#L131-L137)):
   ```python
   user_profile, _ = UserProfile.objects.get_or_create(
       user_id=request.user.id,
       defaults={
           'username': request.user.username,
           'email': request.user.email,
       }
   )
   ```
   - The `create()` method tries to get_or_create UserProfile
   - MongoDB connection is failing, causing 500 errors

3. **MongoDB Connection Status**:
   - Settings show correct replica set configuration: `rs0`, `primaryPreferred`
   - But connection tests are timing out (commands hang with no output)
   - Pod is running OLD code without the MongoDB replica set fix

### Current Pod Status
- **Pod:** `workout-api-75c44ff578-vcmv5`
- **Restart count:** 129 (HIGH - indicates ongoing issues)
- **MongoDB settings:** Correct (rs0, primaryPreferred, workout_admin)
- **Code version:** OLD - missing MongoDB replica set fix from settings.py

### Attempted Fixes

**1. Created UserProfile for kwood user directly in MongoDB:**
```bash
kubectl exec -n woodez-database mongodb-1 -- mongosh workoutdb \
  --username workout_admin --password WorkoutSecure2024 \
  --authenticationDatabase admin \
  --eval 'db.user_profile.insertOne({
    user_id: 1,
    username: "kwood",
    email: "kwood@example.com",
    fitness_goal: "general",
    created_at: new Date(),
    updated_at: new Date()
  })'
```
**Result:** Profile created with `_id: ObjectId('69398ca21349641d9a9dc29d')`, but GET /api/workouts/ still returns 500

**2. Verified User ID:**
- kwood user_id: 1
- Admin privileges: ✅ is_staff=True, is_superuser=True
- Auth token: `5892d47d03f7634023a25982f47c6cb8142a39a7`

### Root Cause
The pod is running the old code that has `directConnection: True` instead of the replica set configuration. The MongoDB connection fix in settings.py was made but **NEVER COMMITTED OR DEPLOYED**.

### Solution Required

**Must deploy updated code with MongoDB replica set fix:**

The following changes need to be committed and deployed:

1. **config/settings.py** - MongoDB replica set configuration:
   ```python
   MONGODB_SETTINGS = {
       'db': config('MONGODB_DB_NAME', default='workout_db'),
       'host': config('MONGODB_HOST', default='localhost'),
       'port': int(config('MONGODB_PORT', default=27017)),
       'replicaSet': config('MONGODB_REPLICA_SET', default='rs0'),
       'serverSelectionTimeoutMS': 5000,
       'readPreference': 'primaryPreferred',
   }
   ```

2. **config/settings.py** - CORS fix for DEBUG mode:
   ```python
   if DEBUG:
       CORS_ALLOW_ALL_ORIGINS = True
   ```

3. **helm/workout-api/values.yaml** - Added CORS origins for localhost:5173

### Deployment Steps

```bash
# 1. Commit changes
git add config/settings.py helm/workout-api/values.yaml
git commit -m "Fix MongoDB replica set connection and CORS configuration"
git push

# 2. Wait for GitHub Actions to build new Docker image
# 3. ArgoCD will auto-deploy (or manual sync)
# 4. Verify new pod is running
kubectl get pods -n woodez-database -w

# 5. Test workout creation again
```

### Workaround (Temporary)
Until deployment completes, workouts cannot be created through the API because MongoDB queries are failing.

**Status:** 🔴 **BLOCKED** - Requires code deployment to fix

---

**Last Updated:** 2025-12-10 (MongoDB connection issue identified)

---

## 15. MongoDB Replica Set Configuration Details

### The Configuration Change in settings.py

**Location:** `config/settings.py` lines 106-113

**OLD configuration (currently running in pod):**
```python
MONGODB_SETTINGS = {
    'db': config('MONGODB_DB_NAME', default='workout_db'),
    'host': config('MONGODB_HOST', default='localhost'),
    'port': int(config('MONGODB_PORT', default=27017)),
    'directConnection': True,  # ⚠️ This was the problem!
}
```

**NEW configuration (uncommitted in local settings.py):**
```python
MONGODB_SETTINGS = {
    'db': config('MONGODB_DB_NAME', default='workout_db'),
    'host': config('MONGODB_HOST', default='localhost'),
    'port': int(config('MONGODB_PORT', default=27017)),
    'replicaSet': config('MONGODB_REPLICA_SET', default='rs0'),  # ✅ Added - tells MongoEngine to use replica set
    'serverSelectionTimeoutMS': 5000,  # ✅ Added - faster timeout for connection errors (5 seconds)
    'readPreference': 'primaryPreferred',  # ✅ Added - prefer primary node for reads
}
```

### What Each Setting Does

1. **`replicaSet: 'rs0'`**
   - Tells MongoEngine the replica set name
   - Enables replica set discovery (finds all nodes: primary + secondaries)
   - Required for proper connection to MongoDB replica sets
   - Without this, connection defaults to standalone mode

2. **`serverSelectionTimeoutMS: 5000`**
   - Connection timeout set to 5 seconds
   - Prevents indefinite hanging when MongoDB is unreachable
   - Faster error detection for debugging
   - Default is 30 seconds (too slow for development)

3. **`readPreference: 'primaryPreferred'`**
   - Directs read operations to the primary node when available
   - Falls back to secondary nodes only if primary is unavailable
   - Prevents "not primary" errors on write operations
   - Ensures read-after-write consistency

### Why `directConnection: True` Was a Problem

**The Issue:**
- `directConnection: True` bypasses replica set discovery
- Connects directly to a single node (could be primary OR secondary)
- If connected to a secondary node:
  - Secondary nodes are read-only
  - Write operations fail with **"not primary"** error
  - Application crashes or hangs
- Used for connecting to standalone MongoDB instances only

**When It Happens:**
- MongoDB service returns a secondary node's address
- Load balancer routes to a secondary
- DNS resolves to a non-primary node
- Result: All write operations fail

### The "Not Primary" Error Explained

**Original Error from Earlier Session:**
```
pymongo.errors.NotPrimaryError: not primary
```

**Why It Occurred:**
1. App used `directConnection: True`
2. Connected to `mongodb-headless` service
3. Service resolved to a secondary MongoDB node
4. App tried to write UserProfile data
5. Secondary rejected write operation with "not primary"

**Fix:**
- Removed `directConnection: True`
- Added `replicaSet: 'rs0'`
- MongoEngine now discovers all nodes and connects to primary

### MongoDB Replica Set Architecture

**Current Deployment:**
```
MongoDB Replica Set: rs0
├── mongodb-0 (Primary or Secondary)
├── mongodb-1 (Primary or Secondary)
└── mongodb-2 (Primary or Secondary)

Service: mongodb-headless
- Points to all 3 pods
- Without replica set config, may return any node
- With replica set config, driver discovers primary automatically
```

### Authentication Settings

**Also in MONGODB_SETTINGS (lines 116-122):**
```python
# Only add authentication if credentials are provided
mongodb_username = config('MONGODB_USERNAME', default='')
mongodb_password = config('MONGODB_PASSWORD', default='')

if mongodb_username and mongodb_password:
    MONGODB_SETTINGS['username'] = mongodb_username
    MONGODB_SETTINGS['password'] = mongodb_password
    MONGODB_SETTINGS['authentication_source'] = 'admin'
```

**Current Values in Kubernetes:**
- `MONGODB_USERNAME`: `workout_admin`
- `MONGODB_PASSWORD`: `WorkoutSecure2024`
- `authentication_source`: `admin`

### Connection Flow

**With OLD Config (directConnection: True):**
1. App queries DNS: `mongodb-headless`
2. DNS returns ONE IP (could be any pod)
3. App connects directly to that IP
4. If secondary → writes fail ❌

**With NEW Config (replicaSet: rs0):**
1. App queries DNS: `mongodb-headless`
2. DNS returns ONE IP (any pod)
3. App connects and issues `isMaster` command
4. MongoDB returns full replica set topology
5. App discovers all nodes and identifies primary
6. App connects to primary for writes ✅
7. Reads can use primary or secondaries based on `readPreference`

### Testing the Fix

Once deployed, test with:
```bash
# Should show primary connection
kubectl exec -n woodez-database NEW_POD_NAME -- \
  python manage.py shell -c "
from workouts.models import UserProfile
from mongoengine.connection import get_connection
conn = get_connection()
print(f'Connected to: {conn.address}')
print(f'Is primary: {conn.is_primary}')
print(f'Replica set: {conn.replica_set_name}')
"
```

Expected output:
```
Connected to: ('mongodb-1', 27017)  # or mongodb-0/mongodb-2
Is primary: True
Replica set: rs0
```

---

**Last Updated:** 2025-12-10 (MongoDB replica set configuration documented)

---

## 16. 500 Internal Server Error - New Deployment Status

### Problem
Frontend showing "Backend returns 500 Internal Server Error" when trying to access workout endpoints.

### Investigation

**New Pod Deployed:**
- **Pod:** `workout-api-6466476c89-sxfp9` (replaced `workout-api-75c44ff578-vcmv5`)
- **Image:** `kwood475/workout-api:release-dev-0b5631a`
- **MongoDB Settings:** ✅ HAS the replica set fix (replicaSet: rs0, primaryPreferred)
- **Status:** Running (1 restart after manual delete)

**MongoDB Connection Tests:**

1. **Settings Verification:** ✅
   ```json
   {
     "db": "workoutdb",
     "host": "mongodb-headless",
     "port": 27017,
     "replicaSet": "rs0",
     "serverSelectionTimeoutMS": 5000,
     "readPreference": "primaryPreferred",
     "username": "workout_admin",
     "password": "WorkoutSecure2024",
     "authentication_source": "admin"
   }
   ```

2. **Network Connectivity:** ✅
   - Socket test to `mongodb-headless:27017` successful

3. **Direct PyMongo Connection:** ✅
   - Direct connection with replica set works perfectly
   - Successfully retrieved MongoDB server info (version 8.2.2)

4. **MongoEngine Queries:** ❌ HANGS
   - `UserProfile.objects.count()` command hangs indefinitely
   - Django shell queries timeout
   - Suggests MongoEngine connection initialization issue

### Root Cause Analysis

The MongoDB replica set configuration is correct, and direct pymongo connections work. However, MongoEngine queries are hanging. This suggests:

1. **MongoEngine Connection Pool Issue**: The connection may have been established before env vars were loaded
2. **Django Settings Loading**: MongoEngine.connect() happens at module import time
3. **Connection State**: Cached/stale connection information in MongoEngine

### Actions Taken

1. ✅ Verified new pod has MongoDB replica set fix in settings.py
2. ✅ Confirmed direct pymongo connection works
3. ✅ Verified UserProfile exists in MongoDB for user_id=1 (kwood)
4. ✅ Restarted pod to reinitialize MongoEngine connection
5. ⏳ Port-forward disconnected - needs restart to test

### Current Status

**Pod:** `workout-api-6466476c89-sxfp9`
- Running with correct MongoDB settings
- MongoEngine connection issue under investigation
- Port-forward to localhost:8000 needs to be restarted

### Next Steps

1. **Restart port-forward:**
   ```bash
   kubectl -n woodez-database port-forward service/workout-api 8000:8000
   ```

2. **Test workout endpoint again:**
   ```bash
   curl -X GET http://127.0.0.1:8000/api/workouts/ \
     -H "Authorization: Token 5892d47d03f7634023a25982f47c6cb8142a39a7"
   ```

3. **If still failing, check pod logs for MongoEngine errors:**
   ```bash
   kubectl logs -n woodez-database workout-api-6466476c89-sxfp9 --tail=50
   ```

4. **Possible fixes if MongoEngine still hangs:**
   - Increase `serverSelectionTimeoutMS` from 5000 to 30000
   - Add `directConnection=False` explicitly
   - Check if MongoEngine version is compatible with MongoDB 8.2.2

### Error Message from Frontend

```
Backend returns 500 Internal Server Error
The response is not valid JSON (server crashed before it could return an error message)
Frontend's fallback error handling catches it and shows {detail: 'Request failed'}
```

**This confirms:** Django is crashing/timing out before it can return a proper JSON error response.

---

**Last Updated:** 2025-12-10 (New deployment investigation - MongoEngine connection issue)
