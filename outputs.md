# API Fixes for Frontend Integration

## Issues Resolved

### 1. ✅ Fixed: 405 Method Not Allowed on `/api/auth/profile/`

**Problem:** Frontend was calling `GET /api/auth/profile/` but the endpoint only accepted `PUT/PATCH` methods.

**Solution:** Updated `update_profile()` function in `workouts/auth_views.py` to support `GET`, `PUT`, and `PATCH` methods.

**File:** `workouts/auth_views.py` (lines 224-304)

---

### 2. ✅ Fixed: Session dates undefined

**Problem:** Frontend was accessing `session.date` property, but the serializer didn't include it.

**Solution:** Added computed `date` field to `WorkoutSessionSerializer` that returns the most appropriate date.

**File:** `workouts/serializers.py` (lines 133-166)

---

### 3. 🔍 Pending: 500 Internal Server Errors on workout endpoints

**Status:** Requires Django server logs to diagnose

**Next Steps:** Check Kubernetes pod logs:
```bash
kubectl logs -f deployment/workout-api -n woodez-database
```

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
