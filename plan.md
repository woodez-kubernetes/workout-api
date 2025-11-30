# Multi-Stage Plan: Workout API with Django REST Framework & MongoDB

## Overview
This plan outlines the development of a workout tracking API using Django REST Framework with MongoDB. The application will be developed locally first, then deployed to a Kubernetes cluster with an existing MongoDB instance.

**IMPORTANT NOTE**: We are using **mongoengine** instead of djongo for MongoDB integration. Djongo is not compatible with Django 5.2+. MongoEngine is actively maintained and provides a clean ODM (Object-Document Mapper) for MongoDB.

## Development Strategy: Dual Environment

**Local Development** (Stages 1-5):
- Use `.env` file for configuration
- Connect to local MongoDB OR port-forward to K8s MongoDB
- Standard Django development workflow

**Kubernetes Deployment** (Stage 6):
- Use ConfigMaps and Secrets for configuration
- Deploy to K8s cluster with existing MongoDB
- Production-ready setup

---

## Stage 1: Project Setup and Environment Configuration

**Objective**: Set up the Python environment and install required dependencies

### Tasks:
1. Create and activate Python virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   ```

2. Install core dependencies:
   - `django` - Web framework
   - `djangorestframework` - REST API toolkit
   - `djongo` - Django MongoDB connector (or `pymongo` + `mongoengine`)
   - `django-cors-headers` - CORS support
   - `python-decouple` - Environment variable management
   - `gunicorn` - Production WSGI server

3. Create `requirements.txt` with pinned versions

4. Create environment configuration:
   - `.env` - Local development config (DO NOT COMMIT)
   - `.env.example` - Template for other developers

   Example `.env`:
   ```bash
   # Django Settings
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   # MongoDB Connection (Local Development)
   MONGODB_HOST=localhost
   MONGODB_PORT=27012
   MONGODB_DB_NAME=workout_db
   MONGODB_USERNAME=workoutuser
   MONGODB_PASSWORD=workout

   # Alternative: Port-forward to K8s MongoDB
   # kubectl port-forward service/mongodb-service 27017:27017
   # Then use localhost above
   ```

5. Update `.gitignore` to ensure `.env` is not committed

**Deliverables**:
- Working virtual environment
- requirements.txt with all dependencies
- .env and .env.example files
- Updated .gitignore

---

## Stage 2: Django Project Initialization with MongoDB

**Objective**: Initialize Django project configured to use MongoDB

### Tasks:
1. Create Django project structure:
   ```bash
   django-admin startproject config .
   python manage.py startapp workouts
   ```

2. Configure `config/settings.py` for MongoDB:
   ```python
   from decouple import config

   DATABASES = {
       'default': {
           'ENGINE': 'djongo',
           'NAME': config('MONGODB_DB_NAME'),
           'CLIENT': {
               'host': config('MONGODB_HOST'),
               'port': int(config('MONGODB_PORT', default=27017)),
               'username': config('MONGODB_USERNAME'),
               'password': config('MONGODB_PASSWORD'),
               'authSource': 'admin',
               'authMechanism': 'SCRAM-SHA-1',
           }
       }
   }
   ```

3. Configure REST Framework settings in `settings.py`:
   ```python
   REST_FRAMEWORK = {
       'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
       'PAGE_SIZE': 20,
       'DEFAULT_AUTHENTICATION_CLASSES': [
           'rest_framework.authentication.TokenAuthentication',
           'rest_framework.authentication.SessionAuthentication',
       ],
       'DEFAULT_PERMISSION_CLASSES': [
           'rest_framework.permissions.IsAuthenticatedOrReadOnly',
       ],
       'DEFAULT_FILTER_BACKENDS': [
           'django_filters.rest_framework.DjangoFilterBackend',
           'rest_framework.filters.SearchFilter',
           'rest_framework.filters.OrderingFilter',
       ],
   }
   ```

4. Add installed apps:
   - `rest_framework`
   - `rest_framework.authtoken`
   - `corsheaders`
   - `django_filters`
   - `workouts`

5. Configure CORS middleware

6. Test MongoDB connection:
   ```bash
   python manage.py check
   ```

**Deliverables**:
- Django project structure
- MongoDB-configured settings
- Initial workouts app
- Working database connection

---

## Stage 3: Core Models and Database Schema Design

**Objective**: Design and implement core workout-related models

### Data Model Architecture

```
User (Django built-in)
  └── UserProfile (1:1)

Exercise (library of exercises)

Workout (workout templates)
  └── WorkoutExercise (many exercises per workout)
      └── Exercise (FK)

WorkoutSession (actual workout instances)
  └── User (FK)
  └── Workout (FK)
  └── ExerciseLog (many logs per session)
      └── Exercise (FK)
```

### Key Models:

#### 1. UserProfile
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    height = models.IntegerField(null=True, blank=True)  # cm
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True)  # kg
    date_of_birth = models.DateField(null=True, blank=True)
    fitness_goal = models.CharField(max_length=50)  # strength, cardio, weight_loss, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### 2. Exercise
```python
class Exercise(models.Model):
    CATEGORY_CHOICES = [
        ('strength', 'Strength'),
        ('cardio', 'Cardio'),
        ('flexibility', 'Flexibility'),
        ('balance', 'Balance'),
    ]

    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    muscle_groups = models.JSONField(default=list)  # ['chest', 'triceps']
    equipment_required = models.JSONField(default=list)  # ['barbell', 'bench']
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    video_url = models.URLField(null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['difficulty']),
        ]
```

#### 3. Workout
```python
class Workout(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workouts')
    is_public = models.BooleanField(default=False)
    estimated_duration = models.IntegerField(help_text='Duration in minutes')
    difficulty = models.CharField(max_length=20, choices=Exercise.DIFFICULTY_CHOICES)
    tags = models.JSONField(default=list)  # ['upper_body', 'hypertrophy']
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
```

#### 4. WorkoutExercise
```python
class WorkoutExercise(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='exercises')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()  # sequence in workout
    sets = models.PositiveIntegerField(default=3)
    reps = models.PositiveIntegerField(null=True, blank=True)
    duration = models.PositiveIntegerField(null=True, blank=True)  # seconds
    rest_period = models.PositiveIntegerField(default=60)  # seconds between sets
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['order']
        unique_together = ['workout', 'order']
```

#### 5. WorkoutSession
```python
class WorkoutSession(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    workout = models.ForeignKey(Workout, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    scheduled_date = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'completed_at']),
        ]
```

#### 6. ExerciseLog
```python
class ExerciseLog(models.Model):
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='exercise_logs')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    set_number = models.PositiveIntegerField()
    reps = models.PositiveIntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)  # kg
    duration = models.PositiveIntegerField(null=True, blank=True)  # seconds
    distance = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)  # km
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['set_number']
```

### Tasks:
1. Create all model classes in `workouts/models.py`
2. Create model managers for common queries
3. Add model methods (e.g., `workout.get_total_duration()`)
4. Create migrations (note: djongo handles MongoDB schema)
5. Create serializers for each model in `workouts/serializers.py`
6. Add model admin classes for Django admin interface

**Deliverables**:
- All core models defined
- Model serializers (basic and detailed versions)
- Django admin configuration
- Database indexes configured

---

## Stage 4: Django REST Framework API Endpoints

**Objective**: Build comprehensive RESTful API endpoints

### API Endpoint Structure

#### Authentication & Users
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - Login (get token)
- `POST /api/auth/logout/` - Logout
- `GET /api/auth/me/` - Current user profile
- `PUT /api/auth/me/` - Update profile

#### Exercises
- `GET /api/exercises/` - List all exercises
  - Filters: `?category=strength&difficulty=beginner`
  - Search: `?search=bench press`
- `GET /api/exercises/{id}/` - Exercise detail
- `POST /api/exercises/` - Create exercise (admin only)
- `PUT/PATCH /api/exercises/{id}/` - Update exercise (admin only)
- `DELETE /api/exercises/{id}/` - Delete exercise (admin only)
- `GET /api/exercises/{id}/history/` - User's history with this exercise

#### Workouts
- `GET /api/workouts/` - List workouts (public + user's own)
  - Filters: `?difficulty=intermediate&is_public=true`
  - Search: `?search=upper body`
- `GET /api/workouts/{id}/` - Workout detail (includes exercises)
- `POST /api/workouts/` - Create workout
- `PUT/PATCH /api/workouts/{id}/` - Update workout (owner only)
- `DELETE /api/workouts/{id}/` - Delete workout (owner only)
- `POST /api/workouts/{id}/clone/` - Clone workout to user's library

#### Workout Sessions
- `GET /api/sessions/` - List user's sessions
  - Filters: `?status=completed&date_from=2024-01-01`
- `GET /api/sessions/{id}/` - Session detail (includes logs)
- `POST /api/sessions/` - Create/start new session
- `PUT/PATCH /api/sessions/{id}/` - Update session
- `POST /api/sessions/{id}/start/` - Mark session as started
- `POST /api/sessions/{id}/complete/` - Mark session as completed
- `DELETE /api/sessions/{id}/` - Delete session

#### Exercise Logs
- `GET /api/sessions/{session_id}/logs/` - All logs for a session
- `POST /api/sessions/{session_id}/logs/` - Add exercise log to session
- `PUT/PATCH /api/logs/{id}/` - Update log
- `DELETE /api/logs/{id}/` - Delete log

#### Statistics & Analytics
- `GET /api/stats/summary/` - Overall workout summary
  - Total sessions, total duration, streak, etc.
- `GET /api/stats/progress/` - Progress over time
  - Sessions per week, volume progression
- `GET /api/stats/exercises/{exercise_id}/progress/` - Progress on specific exercise
  - Weight progression, volume over time

### Implementation Tasks:
1. Create ViewSets in `workouts/views.py`:
   - `ExerciseViewSet`
   - `WorkoutViewSet`
   - `WorkoutSessionViewSet`
   - `ExerciseLogViewSet`
   - `StatsViewSet`

2. Implement filtering and search:
   ```python
   class ExerciseViewSet(viewsets.ModelViewSet):
       queryset = Exercise.objects.all()
       serializer_class = ExerciseSerializer
       filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
       filterset_fields = ['category', 'difficulty']
       search_fields = ['name', 'description']
       ordering_fields = ['name', 'created_at', 'difficulty']
   ```

3. Add custom actions:
   ```python
   @action(detail=True, methods=['post'])
   def clone(self, request, pk=None):
       # Clone workout logic
       pass
   ```

4. Create permission classes in `workouts/permissions.py`:
   - `IsOwnerOrReadOnly`
   - `IsAdminOrReadOnly`

5. Configure URL routing in `workouts/urls.py` using routers

6. Add pagination and query optimization (select_related, prefetch_related)

**Deliverables**:
- Complete API with all endpoints
- URL configuration
- Proper permissions and filtering
- Optimized queries
- API documentation (DRF browsable API)

---

## Stage 5: Authentication and Authorization

**Objective**: Secure the API with authentication and permission controls

### Authentication Strategy
Use **Token Authentication** (DRF built-in) for simplicity, with option to upgrade to JWT later.

### Tasks:

1. **Set up Token Authentication**:
   ```python
   # settings.py
   INSTALLED_APPS += ['rest_framework.authtoken']

   REST_FRAMEWORK = {
       'DEFAULT_AUTHENTICATION_CLASSES': [
           'rest_framework.authentication.TokenAuthentication',
       ],
   }
   ```

2. **Create authentication views** in `workouts/auth_views.py`:
   ```python
   class RegisterView(APIView):
       permission_classes = [AllowAny]
       # User registration logic

   class LoginView(APIView):
       permission_classes = [AllowAny]
       # Login and return token

   class LogoutView(APIView):
       # Logout and delete token

   class UserProfileView(RetrieveUpdateAPIView):
       # Get/update current user
   ```

3. **Custom Permission Classes** (`workouts/permissions.py`):
   ```python
   class IsOwnerOrReadOnly(permissions.BasePermission):
       def has_object_permission(self, request, view, obj):
           if request.method in permissions.SAFE_METHODS:
               return True
           return obj.creator == request.user  # or obj.user

   class IsAdminOrReadOnly(permissions.BasePermission):
       def has_permission(self, request, view):
           if request.method in permissions.SAFE_METHODS:
               return True
           return request.user.is_staff
   ```

4. **Apply permissions to ViewSets**:
   ```python
   class WorkoutViewSet(viewsets.ModelViewSet):
       permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

       def get_queryset(self):
           user = self.request.user
           # Return public workouts + user's own workouts
           return Workout.objects.filter(
               Q(is_public=True) | Q(creator=user)
           )
   ```

5. **Add throttling** to prevent abuse:
   ```python
   REST_FRAMEWORK = {
       'DEFAULT_THROTTLE_CLASSES': [
           'rest_framework.throttling.AnonRateThrottle',
           'rest_framework.throttling.UserRateThrottle'
       ],
       'DEFAULT_THROTTLE_RATES': {
           'anon': '100/hour',
           'user': '1000/hour'
       }
   }
   ```

6. **Create signals** for auto-creating user profile and token:
   ```python
   # workouts/signals.py
   @receiver(post_save, sender=User)
   def create_user_profile(sender, instance, created, **kwargs):
       if created:
           UserProfile.objects.create(user=instance)
           Token.objects.create(user=instance)
   ```

### Authentication Flow:
```
1. Register: POST /api/auth/register/
   → Returns: user data + token

2. Login: POST /api/auth/login/
   → Returns: token

3. Authenticated requests:
   → Header: Authorization: Token <token>

4. Logout: POST /api/auth/logout/
   → Deletes token
```

**Deliverables**:
- Working token authentication system
- Authorization rules applied to all endpoints
- User registration/login/logout endpoints
- Custom permission classes
- Rate limiting configured

---

## Stage 6: Kubernetes Configuration and Deployment

**Objective**: Deploy the Django API to K8s cluster with existing MongoDB

### Phase 6A: Dockerize the Application

1. **Create `Dockerfile`**:
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   # Install dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   # Copy application
   COPY . .

   # Collect static files
   RUN python manage.py collectstatic --noinput

   # Run gunicorn
   CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

   EXPOSE 8000
   ```

2. **Create `.dockerignore`**:
   ```
   venv/
   .env
   __pycache__/
   *.pyc
   .git/
   .gitignore
   ```

3. **Build and test locally**:
   ```bash
   docker build -t workout-api:latest .
   docker run -p 8000:8000 --env-file .env workout-api:latest
   ```

### Phase 6B: Kubernetes Manifests

Create `k8s/` directory with the following manifests:

1. **`k8s/mongodb-configmap.yaml`** (Non-sensitive config):
   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: workout-api-config
     namespace: default
   data:
     MONGODB_HOST: "mongodb-service.default.svc.cluster.local"
     MONGODB_PORT: "27017"
     MONGODB_DB_NAME: "workout_db"
     DJANGO_SETTINGS_MODULE: "config.settings"
     DEBUG: "False"
     ALLOWED_HOSTS: "api.workout.example.com,workout-api-service"
   ```

2. **`k8s/mongodb-secret.yaml`** (Sensitive credentials):
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: workout-api-secret
     namespace: default
   type: Opaque
   data:
     # Base64 encoded values
     # Generate: echo -n 'your-value' | base64
     MONGODB_USERNAME: YWRtaW4=  # admin
     MONGODB_PASSWORD: cGFzc3dvcmQ=  # password
     SECRET_KEY: eW91ci1kamFuZ28tc2VjcmV0LWtleQ==  # your-django-secret-key
   ```

   **To create real secrets**:
   ```bash
   # Generate Django secret key
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

   # Base64 encode values
   echo -n 'your-username' | base64
   echo -n 'your-password' | base64
   echo -n 'your-secret-key' | base64
   ```

3. **`k8s/deployment.yaml`**:
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: workout-api
     namespace: default
     labels:
       app: workout-api
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: workout-api
     template:
       metadata:
         labels:
           app: workout-api
       spec:
         containers:
         - name: workout-api
           image: your-registry/workout-api:latest
           imagePullPolicy: Always
           ports:
           - containerPort: 8000

           # Environment variables from ConfigMap
           envFrom:
           - configMapRef:
               name: workout-api-config

           # Environment variables from Secret
           env:
           - name: MONGODB_USERNAME
             valueFrom:
               secretKeyRef:
                 name: workout-api-secret
                 key: MONGODB_USERNAME
           - name: MONGODB_PASSWORD
             valueFrom:
               secretKeyRef:
                 name: workout-api-secret
                 key: MONGODB_PASSWORD
           - name: SECRET_KEY
             valueFrom:
               secretKeyRef:
                 name: workout-api-secret
                 key: SECRET_KEY

           # Health checks
           livenessProbe:
             httpGet:
               path: /api/health/
               port: 8000
             initialDelaySeconds: 30
             periodSeconds: 10

           readinessProbe:
             httpGet:
               path: /api/health/
               port: 8000
             initialDelaySeconds: 10
             periodSeconds: 5

           # Resource limits
           resources:
             requests:
               memory: "256Mi"
               cpu: "250m"
             limits:
               memory: "512Mi"
               cpu: "500m"
   ```

4. **`k8s/service.yaml`**:
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: workout-api-service
     namespace: default
   spec:
     selector:
       app: workout-api
     ports:
     - protocol: TCP
       port: 80
       targetPort: 8000
     type: ClusterIP
   ```

5. **`k8s/ingress.yaml`** (Optional - for external access):
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: workout-api-ingress
     namespace: default
     annotations:
       cert-manager.io/cluster-issuer: "letsencrypt-prod"
   spec:
     ingressClassName: nginx
     tls:
     - hosts:
       - api.workout.example.com
       secretName: workout-api-tls
     rules:
     - host: api.workout.example.com
       http:
         paths:
         - path: /
           pathType: Prefix
           backend:
             service:
               name: workout-api-service
               port:
                 number: 80
   ```

6. **`k8s/hpa.yaml`** (Optional - Auto-scaling):
   ```yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: workout-api-hpa
     namespace: default
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: workout-api
     minReplicas: 2
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
   ```

### Phase 6C: Deployment Process

1. **Build and push Docker image**:
   ```bash
   # Build
   docker build -t your-registry/workout-api:v1.0.0 .

   # Push to registry (Docker Hub, GCR, ECR, etc.)
   docker push your-registry/workout-api:v1.0.0
   ```

2. **Apply Kubernetes manifests**:
   ```bash
   # Apply in order
   kubectl apply -f k8s/mongodb-configmap.yaml
   kubectl apply -f k8s/mongodb-secret.yaml
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   kubectl apply -f k8s/ingress.yaml  # if using
   kubectl apply -f k8s/hpa.yaml  # if using
   ```

3. **Verify deployment**:
   ```bash
   # Check pods
   kubectl get pods -l app=workout-api

   # Check logs
   kubectl logs -l app=workout-api --tail=100

   # Check service
   kubectl get svc workout-api-service

   # Port-forward for testing
   kubectl port-forward svc/workout-api-service 8000:80
   ```

4. **Test MongoDB connection**:
   ```bash
   # Exec into pod
   kubectl exec -it <pod-name> -- python manage.py check

   # Test database
   kubectl exec -it <pod-name> -- python manage.py dbshell
   ```

### Phase 6D: Health Check Endpoint

Add a health check endpoint in Django:

```python
# workouts/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    # Check database connection
    try:
        connection.ensure_connection()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return Response({
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status
    })

# config/urls.py
urlpatterns = [
    path('api/health/', health_check),
]
```

**Deliverables**:
- Dockerfile and .dockerignore
- Complete K8s manifests in k8s/ directory
- Deployed application in K8s cluster
- Working connection to existing MongoDB
- Health checks configured
- Auto-scaling configured (optional)

---

## Stage 7: Testing and Documentation

**Objective**: Ensure code quality and provide comprehensive documentation

### Phase 7A: Testing

1. **Configure pytest**:
   ```bash
   pip install pytest pytest-django pytest-cov factory-boy
   ```

   Create `pytest.ini`:
   ```ini
   [pytest]
   DJANGO_SETTINGS_MODULE = config.settings
   python_files = tests.py test_*.py *_tests.py
   addopts = --cov=workouts --cov-report=html --cov-report=term
   ```

2. **Unit Tests** (`workouts/tests/test_models.py`):
   - Model creation and validation
   - Model methods
   - Manager methods
   - Signals

3. **API Tests** (`workouts/tests/test_api.py`):
   ```python
   from rest_framework.test import APITestCase
   from rest_framework import status
   from django.contrib.auth.models import User

   class ExerciseAPITestCase(APITestCase):
       def setUp(self):
           self.user = User.objects.create_user('test', 'test@test.com', 'pass')
           self.client.force_authenticate(user=self.user)

       def test_list_exercises(self):
           response = self.client.get('/api/exercises/')
           self.assertEqual(response.status_code, status.HTTP_200_OK)
   ```

4. **Integration Tests**:
   - Complete workout flow (create → session → log)
   - Authentication flow
   - Permission enforcement

5. **Run tests**:
   ```bash
   pytest
   pytest --cov
   pytest --cov --cov-report=html
   ```

### Phase 7B: Code Quality

1. **Configure Ruff** (`pyproject.toml`):
   ```toml
   [tool.ruff]
   line-length = 100
   target-version = "py311"

   [tool.ruff.lint]
   select = ["E", "F", "I", "N", "W"]
   ignore = []

   [tool.ruff.format]
   quote-style = "double"
   ```

2. **Type hints with mypy** (`mypy.ini`):
   ```ini
   [mypy]
   python_version = 3.11
   warn_return_any = True
   warn_unused_configs = True
   disallow_untyped_defs = True
   ```

3. **Pre-commit hooks** (`.pre-commit-config.yaml`):
   ```yaml
   repos:
     - repo: https://github.com/astral-sh/ruff-pre-commit
       rev: v0.1.0
       hooks:
         - id: ruff
           args: [--fix]
         - id: ruff-format
   ```

4. **Run linting**:
   ```bash
   ruff check .
   ruff format .
   mypy workouts/
   ```

### Phase 7C: API Documentation

1. **Install drf-spectacular**:
   ```bash
   pip install drf-spectacular
   ```

2. **Configure in settings.py**:
   ```python
   INSTALLED_APPS += ['drf_spectacular']

   REST_FRAMEWORK = {
       'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
   }

   SPECTACULAR_SETTINGS = {
       'TITLE': 'Workout API',
       'DESCRIPTION': 'API for tracking workouts and exercises',
       'VERSION': '1.0.0',
       'SERVE_INCLUDE_SCHEMA': False,
   }
   ```

3. **Add URLs**:
   ```python
   from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

   urlpatterns = [
       path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
       path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
   ]
   ```

4. **Generate OpenAPI schema**:
   ```bash
   python manage.py spectacular --color --file schema.yml
   ```

### Phase 7D: Documentation Files

1. **Update README.md**:
   - Project overview
   - Features
   - Tech stack
   - Setup instructions (local and K8s)
   - API endpoints overview
   - Contributing guidelines

2. **Update CLAUDE.md**:
   - Add all development commands
   - Architecture overview
   - Model relationships
   - Testing instructions
   - Deployment process

3. **Create API documentation**:
   - Available at `/api/docs/` (Swagger UI)
   - OpenAPI schema at `/api/schema/`

### Commands Reference

```bash
# Development
source venv/bin/activate
python manage.py runserver
python manage.py makemigrations
python manage.py migrate

# Testing
pytest
pytest --cov
pytest -k test_name -v

# Code quality
ruff check .
ruff format .
mypy workouts/

# Database
python manage.py shell
python manage.py dbshell
python manage.py createsuperuser

# Docker
docker build -t workout-api:latest .
docker run -p 8000:8000 --env-file .env workout-api:latest

# Kubernetes
kubectl apply -f k8s/
kubectl get pods -l app=workout-api
kubectl logs -f <pod-name>
kubectl port-forward svc/workout-api-service 8000:80

# Port-forward MongoDB from K8s (for local dev)
kubectl port-forward service/mongodb-service 27017:27017
```

**Deliverables**:
- Comprehensive test suite (>80% coverage)
- Configured linting and type checking
- API documentation (Swagger/OpenAPI)
- Complete README.md
- Updated CLAUDE.md
- Pre-commit hooks

---

## Complete Dependency List

```txt
# Core Framework
django>=4.2,<5.0
djangorestframework>=3.14,<4.0

# MongoDB
djongo>=1.3.6
pymongo>=4.0,<5.0
# Alternative: mongoengine>=0.27 (if not using djongo)

# Authentication
djangorestframework-simplejwt>=5.3,<6.0  # Optional: for JWT

# Utilities
python-decouple>=3.8
django-cors-headers>=4.3
django-filter>=23.0

# Production Server
gunicorn>=21.0
whitenoise>=6.6

# Development/Testing
pytest>=7.4
pytest-django>=4.5
pytest-cov>=4.1
factory-boy>=3.3

# Code Quality
ruff>=0.1
mypy>=1.7
django-stubs>=4.2

# Documentation
drf-spectacular>=0.27

# Pre-commit
pre-commit>=3.5
```

---

## Estimated Timeline

| Stage | Tasks | Estimated Time |
|-------|-------|----------------|
| Stage 1: Setup | Environment, dependencies, .env | 1-2 hours |
| Stage 2: Django Init | Project setup, MongoDB config | 2-3 hours |
| Stage 3: Models | All models, serializers, admin | 6-8 hours |
| Stage 4: API Endpoints | ViewSets, URLs, filtering | 8-10 hours |
| Stage 5: Auth | Authentication, permissions | 3-4 hours |
| Stage 6: K8s Deploy | Docker, manifests, deployment | 4-6 hours |
| Stage 7: Testing & Docs | Tests, linting, documentation | 6-8 hours |

**Total Estimated Time**: 30-40 hours

---

## Development vs Production Configuration

### Local Development (.env)
```bash
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
MONGODB_HOST=localhost  # or port-forwarded K8s
MONGODB_PORT=27017
```

### Kubernetes Production (ConfigMap + Secret)
```bash
DEBUG=False
ALLOWED_HOSTS=api.workout.example.com
MONGODB_HOST=mongodb-service.default.svc.cluster.local
MONGODB_PORT=27017
# Credentials from Secret
```

---

## Next Steps

After completing all stages:

1. **Performance Optimization**:
   - Add Redis for caching
   - Implement database query optimization
   - Add CDN for static files

2. **Advanced Features**:
   - Real-time updates (WebSockets)
   - File uploads (exercise videos/images)
   - Social features (share workouts, follow users)
   - Workout recommendations (ML-based)

3. **Monitoring & Observability**:
   - Add Sentry for error tracking
   - Prometheus + Grafana for metrics
   - ELK stack for logging

4. **CI/CD Pipeline**:
   - GitHub Actions for automated testing
   - Automated deployments to K8s
   - Multi-environment setup (dev/staging/prod)

---

## Questions to Answer Before Starting

1. **MongoDB Setup**:
   - What is the K8s service name for MongoDB? (e.g., `mongodb-service`)
   - What namespace is MongoDB running in?
   - What are the authentication credentials?
   - Does MongoDB already have the workout_db database created?

2. **Kubernetes Cluster**:
   - What container registry will you use? (Docker Hub, GCR, ECR)
   - Do you have ingress controller installed? (nginx, traefik)
   - Do you need TLS/SSL certificates?
   - What domain will the API use?

3. **Development Preferences**:
   - Use djongo (Django ORM with MongoDB) or mongoengine?
   - Token auth or JWT?
   - Need admin interface?
