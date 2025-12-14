# API Fixes for Frontend Integration

## Issues Resolved

### 1. ✅ Fixed: 405 Method Not Allowed on `/api/auth/profile/`

**Problem:** Frontend was calling `GET /api/auth/profile/` but the endpoint only accepted `PUT/PATCH` methods.

**Solution:** Updated `update_profile()` function in `workouts/auth_views.py` to support `GET`, `PUT`, and `PATCH` methods.

**File:** `workouts/auth_views.py` (lines 224-304)

**Status:** ✅ Deployed and working

---

### 2. ✅ Fixed: Session dates undefined

**Problem:** Frontend was accessing `session.date` property, but the list serializer didn't include it.

**Solution:** Added computed `date` field to both `WorkoutSessionSerializer` and `WorkoutSessionListSerializer` that returns the most appropriate date (completed_at, started_at, scheduled_date, or created_at as fallback).

**Files:**
- `workouts/serializers.py` (lines 145, 158-166) - WorkoutSessionSerializer
- `workouts/serializers.py` (lines 186, 196-204) - WorkoutSessionListSerializer

**Status:** ✅ Deployed and working

---

### 3. ✅ Fixed: Exercise logs showing "Unknown Exercise"

**Problem:** Frontend was displaying "Unknown Exercise" for all exercise logs because the list serializer was returning `exercise_name` (flat string) but frontend expected `exercise.name` (nested object).

**Solution:** Updated `ExerciseLogListSerializer` to return full `exercise` object using `ExerciseListSerializer`, ensuring consistency with the detail serializer.

**File:** `workouts/serializers.py` (lines 220-229)

**Before:**
```python
exercise_name = serializers.CharField(source='exercise.name', read_only=True)
fields = ['id', 'exercise_name', 'set_number', ...]
```

**After:**
```python
exercise = ExerciseListSerializer(read_only=True)
fields = ['id', 'exercise', 'set_number', ...]
```

**API Response (verified on deployed pod):**
```json
{
  "id": 2,
  "exercise": {
    "id": 1,
    "name": "Dumbbell Bench Press",
    "category": "strength",
    "difficulty": "intermediate",
    "muscle_groups": []
  },
  "set_number": 1,
  "reps": 10,
  "weight": "50.00",
  ...
}
```

**Status:** ✅ Deployed (image: `kwood475/workout-api:release-dev-49c9c15`)

**Frontend Action Required:** The backend is returning correct data with `exercise.name = "Dumbbell Bench Press"`. If still showing "Unknown Exercise", this is a frontend code issue - check that the frontend is accessing `log.exercise.name` correctly.

---

### 3. ✅ Fixed: PostgreSQL Database Restored → ❌ New Issue: Authentication Failed

**Original Problem:** PostgreSQL pod was stuck in Terminating state.
**Status:** ✅ PostgreSQL is now running (`postgres-statefulset-0: Running`)

**New Problem:** workout-api pod still in CrashLoopBackOff (180 restarts)

**Root Cause:** Password authentication failed
```
django.db.utils.OperationalError: connection to server at "postgres-svc" (10.244.8.151),
port 5432 failed: FATAL: password authentication failed for user "workout_admin"
```

**Solution Options:**

**Option A: Update PostgreSQL to match Helm chart credentials**
```bash
# Connect to PostgreSQL pod
kubectl exec -it postgres-statefulset-0 -n woodez-database -- psql -U postgres

# Create user and database
CREATE USER workout_admin WITH PASSWORD 'your-password-here';
CREATE DATABASE "woodez-auth" OWNER workout_admin;
GRANT ALL PRIVILEGES ON DATABASE "woodez-auth" TO workout_admin;
\q
```

**Option B: Update Helm chart to match existing PostgreSQL credentials**
Update `helm/workout-api/values.yaml`:
```yaml
config:
  postgres:
    username: "postgres"  # or whatever user exists in PostgreSQL
secrets:
  postgresPassword: "actual-postgres-password"
```

Then redeploy:
```bash
helm upgrade workout-api ./helm/workout-api -n woodez-database
```

---

### 4. ⚠️ Frontend React Errors (Secondary Issue)

**Problem:** Frontend showing errors like:
- `Workouts.tsx:116: Cannot read properties of undefined (reading 'length')`
- `Dashboard.tsx:426: Cannot read properties of undefined (reading 'length')`

**Status:** These are frontend code issues, NOT backend API issues.

**Root Cause:** React components are trying to access properties before checking if they exist:
```typescript
// BAD - component crashes if workouts is undefined
workouts.map(workout => ...)

// GOOD - safe access with optional chaining
workouts?.map(workout => ...) || []
```

**Note:** These errors will persist even after the database is fixed. The frontend needs null safety checks added.

---

## Deployment

To deploy fixes to Kubernetes:

```bash
# Rebuild image
docker build -t kwood475/workout-api:latest .
docker push kwood475/workout-api:latest

# Upgrade Helm release
helm upgrade workout-api ./helm/workout-api -n woodez-database
```

Or force pod restart:
```bash
kubectl rollout restart deployment/workout-api -n woodez-database
```
