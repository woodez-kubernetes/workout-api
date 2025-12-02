# Workout API - Application Architecture Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Design](#database-design)
4. [File Structure](#file-structure)
5. [Core Components](#core-components)
6. [API Endpoints](#api-endpoints)
7. [Data Flow](#data-flow)
8. [How Everything Fits Together](#how-everything-fits-together)

---

## Overview

The Workout API is a Django REST Framework application designed for comprehensive fitness tracking. It allows users to:
- Create and manage exercise libraries
- Build workout templates
- Track workout sessions in real-time
- Log individual exercise performance with sets, reps, and weights
- Analyze workout history and progress

### Technology Stack
- **Backend Framework**: Django 5.1 + Django REST Framework
- **Primary Database**: MongoDB (via MongoEngine) - Application data
- **Auth Database**: PostgreSQL - Django built-in models (User, Token, Sessions)
- **Authentication**: Token-based authentication
- **API Documentation**: drf-spectacular (OpenAPI/Swagger)
- **Deployment**: Docker + Kubernetes + ArgoCD

---

## Architecture

### Dual Database Architecture

This application uses a **hybrid database approach** for optimal performance:

```
┌─────────────────────────────────────────────┐
│           Workout API Application           │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐      ┌─────────────────┐ │
│  │  PostgreSQL  │      │    MongoDB      │ │
│  │              │      │                 │ │
│  │  - User      │      │  - UserProfile  │ │
│  │  - Token     │      │  - Exercise     │ │
│  │  - Session   │      │  - Workout      │ │
│  │  - Admin     │      │  - WorkoutSess. │ │
│  │              │      │  - ExerciseLog  │ │
│  └──────────────┘      └─────────────────┘ │
│   Django Built-in       Application Data   │
└─────────────────────────────────────────────┘
```

**Why Two Databases?**

1. **PostgreSQL**:
   - Handles Django's built-in models requiring relational integrity
   - Used for: User authentication, admin panel, sessions, tokens
   - Benefits: ACID compliance, robust authentication system

2. **MongoDB**:
   - Handles application-specific data with flexible schemas
   - Used for: Exercises, workouts, workout sessions, exercise logs
   - Benefits: Flexible schema, embedded documents, better for hierarchical data

### Configuration (`config/settings.py`)

The dual database setup is configured in lines 89-124:

```python
# PostgreSQL - Django's default database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'woodez-auth'),
        'USER': os.getenv('POSTGRES_USER', 'workout_admin'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'workout_password'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

# MongoDB - Application data
MONGODB_SETTINGS = {
    'db': os.getenv('MONGODB_DB', 'workoutdb'),
    'host': os.getenv('MONGODB_HOST', 'localhost'),
    'port': int(os.getenv('MONGODB_PORT', '27017')),
}
```

---

## Database Design

### MongoDB Collections and Relationships

```
UserProfile (linked to Django User)
    ↓ references
Exercise (standalone, can be user-created or public)
    ↓ referenced by
WorkoutExercise (embedded in Workout)
    ↓ part of
Workout (template containing multiple exercises)
    ↓ referenced by
WorkoutSession (actual workout instance)
    ↓ contains
ExerciseLog (individual set/rep/weight logs)
```

### Data Models

#### 1. UserProfile (`workouts/models.py:6-51`)
Extends Django's User model with fitness-specific profile data.

```python
class UserProfile(Document):
    user_id = IntField(required=True, unique=True)  # Links to Django User
    bio = StringField(max_length=500)
    height = FloatField(min_value=0)  # in cm
    weight = FloatField(min_value=0)  # in kg
    date_of_birth = DateTimeField()
    fitness_goal = StringField(choices=FITNESS_GOALS)
    experience_level = StringField(choices=EXPERIENCE_LEVELS)
    preferred_workout_types = ListField(StringField())
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
```

**Purpose**: Store extended user information not suitable for PostgreSQL User model.

#### 2. Exercise (`workouts/models.py:53-110`)
Exercise library with detailed metadata.

```python
class Exercise(Document):
    name = StringField(required=True, max_length=200)
    description = StringField()
    category = StringField(choices=EXERCISE_CATEGORIES, required=True)
    difficulty_level = StringField(choices=DIFFICULTY_LEVELS, default='beginner')
    primary_muscles = ListField(StringField(choices=MUSCLE_GROUPS))
    secondary_muscles = ListField(StringField(choices=MUSCLE_GROUPS))
    equipment_needed = ListField(StringField())
    instructions = ListField(StringField())
    video_url = URLField()
    image_url = URLField()
    is_custom = BooleanField(default=False)
    created_by_user_id = IntField()  # Only set if custom exercise
    is_public = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
```

**Purpose**: Centralized exercise library. Supports both system-wide exercises and user-created custom exercises.

#### 3. WorkoutExercise (`workouts/models.py:112-133`)
Embedded document representing an exercise within a workout.

```python
class WorkoutExercise(EmbeddedDocument):
    exercise = ReferenceField(Exercise, required=True)
    order = IntField(required=True, min_value=1)
    target_sets = IntField(min_value=1)
    target_reps_min = IntField(min_value=1)
    target_reps_max = IntField(min_value=1)
    target_weight = FloatField(min_value=0)
    rest_seconds = IntField(min_value=0, default=60)
    notes = StringField(max_length=500)
```

**Purpose**: Define how an exercise should be performed within a specific workout (sets, reps, weight targets).

#### 4. Workout (`workouts/models.py:135-217`)
Workout template containing multiple exercises.

```python
class Workout(Document):
    name = StringField(required=True, max_length=200)
    description = StringField()
    created_by_user_id = IntField(required=True)
    exercises = EmbeddedDocumentListField(WorkoutExercise)
    difficulty_level = StringField(choices=DIFFICULTY_LEVELS)
    estimated_duration_minutes = IntField(min_value=1)
    tags = ListField(StringField(max_length=50))
    is_template = BooleanField(default=False)
    is_public = BooleanField(default=False)
    total_exercises = IntField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)
```

**Purpose**: Reusable workout templates that users can create and execute.

#### 5. WorkoutSession (`workouts/models.py:219-286`)
Actual workout instance being performed.

```python
class WorkoutSession(Document):
    user_id = IntField(required=True)
    workout = ReferenceField(Workout, required=True)
    status = StringField(choices=SESSION_STATUS, default='planned')
    start_time = DateTimeField()
    end_time = DateTimeField()
    actual_duration_minutes = IntField(min_value=0)
    notes = StringField()
    rating = IntField(min_value=1, max_value=5)
    calories_burned = IntField(min_value=0)
    total_volume = FloatField(min_value=0, default=0)
    created_at = DateTimeField(default=datetime.utcnow)
```

**Purpose**: Track when and how a workout was performed, including start/end times and metrics.

#### 6. ExerciseLog (`workouts/models.py:288-327`)
Individual exercise performance log.

```python
class ExerciseLog(Document):
    workout_session = ReferenceField(WorkoutSession, required=True)
    exercise = ReferenceField(Exercise, required=True)
    user_id = IntField(required=True)
    set_number = IntField(required=True, min_value=1)
    reps = IntField(min_value=0)
    weight = FloatField(min_value=0)
    duration_seconds = IntField(min_value=0)
    distance = FloatField(min_value=0)
    notes = StringField(max_length=500)
    completed_at = DateTimeField(default=datetime.utcnow)
```

**Purpose**: Detailed logging of each set performed during a workout session.

---

## File Structure

```
workout-api/
├── config/
│   ├── __init__.py
│   ├── settings.py          # Django configuration
│   ├── urls.py              # Root URL routing
│   └── wsgi.py              # WSGI application
├── workouts/
│   ├── __init__.py
│   ├── models.py            # MongoDB data models
│   ├── serializers.py       # DRF serializers
│   ├── views.py             # API ViewSets
│   ├── urls.py              # Workout app URL routing
│   └── permissions.py       # Custom permissions
├── manage.py                # Django management script
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker image definition
├── helm/                    # Kubernetes Helm charts
│   └── workout-api/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
├── argocd/                  # ArgoCD application manifests
│   └── application.yaml
└── .github/
    └── workflows/
        └── docker-build-push.yml  # CI/CD pipeline
```

---

## Core Components

### 1. Settings (`config/settings.py`)

**Purpose**: Central configuration for the entire Django application.

**Key Sections**:

- **Lines 20-28**: Installed Apps
  ```python
  INSTALLED_APPS = [
      'django.contrib.admin',
      'django.contrib.auth',
      'django.contrib.contenttypes',
      'django.contrib.sessions',
      'django.contrib.messages',
      'django.contrib.staticfiles',
      'rest_framework',
      'rest_framework.authtoken',
      'drf_spectacular',
      'corsheaders',
      'workouts',
  ]
  ```

- **Lines 172-196**: REST Framework Configuration
  ```python
  REST_FRAMEWORK = {
      'DEFAULT_AUTHENTICATION_CLASSES': [
          'rest_framework.authentication.TokenAuthentication',
      ],
      'DEFAULT_PERMISSION_CLASSES': [
          'rest_framework.permissions.IsAuthenticated',
      ],
      'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
      'PAGE_SIZE': 20,
      'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
  }
  ```

- **Lines 214-219**: CORS Configuration
  ```python
  CORS_ALLOW_ALL_ORIGINS = os.getenv('CORS_ALLOW_ALL_ORIGINS', 'False').lower() == 'true'
  CORS_ALLOWED_ORIGINS = [
      origin.strip()
      for origin in os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
  ]
  ```

**Environment Variables**:
- `DJANGO_SECRET_KEY`: Django secret key for cryptographic signing
- `DJANGO_DEBUG`: Debug mode flag
- `POSTGRES_*`: PostgreSQL connection settings
- `MONGODB_*`: MongoDB connection settings
- `CORS_*`: CORS policy settings

### 2. Models (`workouts/models.py`)

**Purpose**: Define the data structure for all application entities using MongoEngine.

**Key Features**:
- Uses `mongoengine.Document` instead of Django's ORM models
- Supports embedded documents (`WorkoutExercise` embedded in `Workout`)
- Reference fields create relationships between collections
- Custom validation and constraints
- Automatic timestamp tracking with `created_at` and `updated_at`

**Constants** (Lines 5-47):
- `FITNESS_GOALS`: weight_loss, muscle_gain, endurance, flexibility, general_fitness
- `EXPERIENCE_LEVELS`: beginner, intermediate, advanced, expert
- `EXERCISE_CATEGORIES`: strength, cardio, flexibility, balance, plyometrics, powerlifting, olympic_weightlifting, calisthenics, sports
- `DIFFICULTY_LEVELS`: beginner, intermediate, advanced, expert
- `MUSCLE_GROUPS`: chest, back, shoulders, arms, legs, core, glutes, cardio
- `SESSION_STATUS`: planned, in_progress, completed, cancelled

### 3. Serializers (`workouts/serializers.py`)

**Purpose**: Handle data validation and transformation between API and database.

**Key Serializers**:

#### UserProfileSerializer (Lines 5-28)
- Validates user profile data
- Ensures date_of_birth is in the past
- Updates `updated_at` timestamp automatically

#### ExerciseSerializer (Lines 30-66)
- Full exercise detail serialization
- `ExerciseListSerializer`: Optimized version for list views (minimal fields)
- Validates difficulty levels and muscle groups

#### WorkoutExerciseSerializer (Lines 68-100)
- Validates exercise order within workout
- Ensures target_reps_max >= target_reps_min
- Nested exercise details using `ExerciseListSerializer`

#### WorkoutSerializer (Lines 102-219)
- Most complex serializer with nested exercises
- `calculate_estimated_duration()`: Auto-calculates workout duration
- `calculate_total_exercises()`: Counts exercises in workout
- Custom validation for exercise order uniqueness
- `WorkoutListSerializer`: Optimized for list views

#### WorkoutSessionSerializer (Lines 221-318)
- Handles workout session lifecycle
- Validates status transitions
- Calculates `actual_duration_minutes` from start/end times
- Ensures end_time > start_time
- `WorkoutSessionListSerializer`: Optimized for list views

#### ExerciseLogSerializer (Lines 320-410)
- Validates exercise logs during sessions
- Ensures at least one performance metric (reps, weight, duration, distance)
- User-friendly validation error messages
- `ExerciseLogListSerializer`: Optimized for list views

**Common Pattern**: Each model has two serializers:
1. **Full Serializer**: All fields, used for detail views and create/update
2. **List Serializer**: Minimal fields, optimized for list views to reduce payload size

### 4. Views (`workouts/views.py`)

**Purpose**: Implement all API endpoints using Django REST Framework ViewSets.

**Authentication & Permissions**:
All views require token authentication by default (`settings.py:172-196`). Custom permission classes ensure users can only access their own data.

#### ExerciseViewSet (Lines 22-166)

**Endpoints**:
- `GET /api/exercises/` - List exercises
- `POST /api/exercises/` - Create exercise
- `GET /api/exercises/{id}/` - Get exercise detail
- `PUT/PATCH /api/exercises/{id}/` - Update exercise
- `DELETE /api/exercises/{id}/` - Delete exercise

**Key Features**:
- **Filtering** (Lines 61-87): Filter by category, difficulty, muscle group
- **Search** (Lines 89-115): Search by name
- **Custom Exercises** (Lines 117-143): Users can create private exercises
- **Permission Logic** (Lines 145-166):
  - Public exercises: read-only for all users
  - Custom exercises: full CRUD only for creator

**Example**:
```python
def get_queryset(self):
    queryset = Exercise.objects.all()

    # Filter by category
    category = self.request.query_params.get('category')
    if category:
        queryset = queryset.filter(category=category)

    # Filter custom exercises
    if self.request.query_params.get('custom_only') == 'true':
        queryset = queryset.filter(
            is_custom=True,
            created_by_user_id=self.request.user.id
        )

    return queryset
```

#### WorkoutViewSet (Lines 168-450)

**Endpoints**:
- `GET /api/workouts/` - List workouts
- `POST /api/workouts/` - Create workout
- `GET /api/workouts/{id}/` - Get workout detail
- `PUT/PATCH /api/workouts/{id}/` - Update workout
- `DELETE /api/workouts/{id}/` - Delete workout
- `POST /api/workouts/{id}/clone/` - Clone workout (custom action)

**Key Features**:
- **Filtering** (Lines 255-300): Filter by difficulty, tags, template status
- **Clone Action** (Lines 302-365): Duplicate workouts with new name
- **Exercise Management** (Lines 367-410): Add/remove exercises from workout
- **Statistics** (Lines 412-450): Calculate workout metrics

**Clone Action Example**:
```python
@action(detail=True, methods=['post'])
def clone(self, request, pk=None):
    original_workout = self.get_object()

    # Create new workout with cloned data
    cloned_workout = Workout(
        name=f"{original_workout.name} (Copy)",
        description=original_workout.description,
        created_by_user_id=request.user.id,
        exercises=original_workout.exercises,
        difficulty_level=original_workout.difficulty_level,
        # ... other fields
    )
    cloned_workout.save()

    return Response(WorkoutSerializer(cloned_workout).data)
```

#### WorkoutSessionViewSet (Lines 452-686)

**Endpoints**:
- `GET /api/workout-sessions/` - List sessions
- `POST /api/workout-sessions/` - Create session
- `GET /api/workout-sessions/{id}/` - Get session detail
- `PUT/PATCH /api/workout-sessions/{id}/` - Update session
- `DELETE /api/workout-sessions/{id}/` - Delete session
- `POST /api/workout-sessions/{id}/start/` - Start session
- `POST /api/workout-sessions/{id}/complete/` - Complete session

**Key Features**:
- **Session Lifecycle** (Lines 520-600):
  - Start: Set status to 'in_progress', record start_time
  - Complete: Set status to 'completed', record end_time, calculate duration
- **Filtering** (Lines 602-640): Filter by status, date range, workout
- **Statistics** (Lines 642-686): Total volume, calories burned, duration

**Session Start Example**:
```python
@action(detail=True, methods=['post'])
def start(self, request, pk=None):
    session = self.get_object()

    if session.status != 'planned':
        return Response(
            {'error': 'Can only start planned sessions'},
            status=status.HTTP_400_BAD_REQUEST
        )

    session.status = 'in_progress'
    session.start_time = datetime.utcnow()
    session.save()

    return Response(WorkoutSessionSerializer(session).data)
```

#### ExerciseLogViewSet (Lines 688-885)

**Endpoints**:
- `GET /api/exercise-logs/` - List logs
- `POST /api/exercise-logs/` - Create log
- `GET /api/exercise-logs/{id}/` - Get log detail
- `PUT/PATCH /api/exercise-logs/{id}/` - Update log
- `DELETE /api/exercise-logs/{id}/` - Delete log

**Key Features**:
- **Session Validation** (Lines 750-790): Ensure logs belong to user's session
- **Filtering** (Lines 792-830): Filter by session, exercise, date range
- **Bulk Creation** (Lines 832-870): Create multiple logs at once
- **Analytics** (Lines 872-885): Personal records, progress tracking

**Bulk Create Example**:
```python
@action(detail=False, methods=['post'])
def bulk_create(self, request):
    logs_data = request.data.get('logs', [])
    created_logs = []

    for log_data in logs_data:
        log_data['user_id'] = request.user.id
        serializer = ExerciseLogSerializer(data=log_data)

        if serializer.is_valid():
            log = serializer.save()
            created_logs.append(log)
        else:
            return Response(serializer.errors, status=400)

    return Response(
        ExerciseLogListSerializer(created_logs, many=True).data,
        status=201
    )
```

### 5. URL Routing

#### Root URLs (`config/urls.py`)

```python
urlpatterns = [
    path('admin/', admin.site.urls),  # Django admin panel

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(), name='redoc'),

    # Main API endpoints
    path('api/', include('workouts.urls')),
]
```

#### Workout URLs (`workouts/urls.py`)

**ViewSet Registration** (Lines 17-21):
```python
router = DefaultRouter()
router.register(r'exercises', ExerciseViewSet, basename='exercise')
router.register(r'workouts', WorkoutViewSet, basename='workout')
router.register(r'workout-sessions', WorkoutSessionViewSet, basename='workoutsession')
router.register(r'exercise-logs', ExerciseLogViewSet, basename='exerciselog')
```

**Authentication Endpoints** (Lines 29-34):
```python
urlpatterns = [
    path('health/', health_check, name='health'),
    path('auth/register/', register_user, name='register'),
    path('auth/login/', login_user, name='login'),
    path('auth/logout/', logout_user, name='logout'),
    path('auth/profile/', user_profile, name='profile'),
    path('', include(router.urls)),
]
```

**Health Check** (Lines 12-14):
```python
def health_check(request):
    return JsonResponse({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register/` | Create new user account | No |
| POST | `/api/auth/login/` | Login and receive auth token | No |
| POST | `/api/auth/logout/` | Logout and invalidate token | Yes |
| GET | `/api/auth/profile/` | Get user profile | Yes |
| PUT | `/api/auth/profile/` | Update user profile | Yes |

### Exercises

| Method | Endpoint | Description | Filters |
|--------|----------|-------------|---------|
| GET | `/api/exercises/` | List exercises | `category`, `difficulty`, `muscle_group`, `custom_only` |
| POST | `/api/exercises/` | Create exercise | - |
| GET | `/api/exercises/{id}/` | Exercise detail | - |
| PUT | `/api/exercises/{id}/` | Update exercise | - |
| DELETE | `/api/exercises/{id}/` | Delete exercise | - |

### Workouts

| Method | Endpoint | Description | Filters |
|--------|----------|-------------|---------|
| GET | `/api/workouts/` | List workouts | `difficulty`, `tags`, `is_template`, `is_public` |
| POST | `/api/workouts/` | Create workout | - |
| GET | `/api/workouts/{id}/` | Workout detail | - |
| PUT | `/api/workouts/{id}/` | Update workout | - |
| DELETE | `/api/workouts/{id}/` | Delete workout | - |
| POST | `/api/workouts/{id}/clone/` | Clone workout | - |

### Workout Sessions

| Method | Endpoint | Description | Filters |
|--------|----------|-------------|---------|
| GET | `/api/workout-sessions/` | List sessions | `status`, `workout`, `date_from`, `date_to` |
| POST | `/api/workout-sessions/` | Create session | - |
| GET | `/api/workout-sessions/{id}/` | Session detail | - |
| PUT | `/api/workout-sessions/{id}/` | Update session | - |
| DELETE | `/api/workout-sessions/{id}/` | Delete session | - |
| POST | `/api/workout-sessions/{id}/start/` | Start session | - |
| POST | `/api/workout-sessions/{id}/complete/` | Complete session | - |

### Exercise Logs

| Method | Endpoint | Description | Filters |
|--------|----------|-------------|---------|
| GET | `/api/exercise-logs/` | List logs | `session`, `exercise`, `date_from`, `date_to` |
| POST | `/api/exercise-logs/` | Create log | - |
| POST | `/api/exercise-logs/bulk_create/` | Create multiple logs | - |
| GET | `/api/exercise-logs/{id}/` | Log detail | - |
| PUT | `/api/exercise-logs/{id}/` | Update log | - |
| DELETE | `/api/exercise-logs/{id}/` | Delete log | - |

### Documentation

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/schema/` | OpenAPI schema (JSON) |
| GET | `/api/docs/` | Swagger UI documentation |
| GET | `/api/redoc/` | ReDoc documentation |

---

## Data Flow

### Request/Response Flow

```
1. HTTP Request
   ↓
2. Django URL Router (config/urls.py)
   ↓
3. Workout App URL Router (workouts/urls.py)
   ↓
4. REST Framework ViewSet (workouts/views.py)
   ↓
5. Authentication Check (Token validation)
   ↓
6. Permission Check (Custom permissions)
   ↓
7. Serializer Validation (workouts/serializers.py)
   ↓
8. MongoDB Query (via MongoEngine models)
   ↓
9. Serializer Transform (Convert to JSON)
   ↓
10. HTTP Response
```

### Example: Creating a Workout

**1. Client Request**:
```bash
POST /api/workouts/
Authorization: Token abc123xyz

{
  "name": "Push Day",
  "description": "Chest, shoulders, triceps",
  "difficulty_level": "intermediate",
  "exercises": [
    {
      "exercise": "507f1f77bcf86cd799439011",
      "order": 1,
      "target_sets": 4,
      "target_reps_min": 8,
      "target_reps_max": 12,
      "target_weight": 185,
      "rest_seconds": 90
    }
  ]
}
```

**2. URL Routing**:
- `config/urls.py:30` → Routes to `workouts.urls`
- `workouts/urls.py:37` → Router matches `/workouts/` to `WorkoutViewSet`

**3. View Processing**:
- `WorkoutViewSet.create()` method called (inherited from `ModelViewSet`)
- Token authentication verified (lines 172-176 in settings.py)
- Permission check: User must be authenticated

**4. Serialization**:
- `WorkoutSerializer` validates request data (lines 102-219)
- Validates exercise order is unique
- Validates target_reps_max >= target_reps_min
- Calculates estimated_duration and total_exercises

**5. Database Operation**:
- `Workout` document created in MongoDB
- `created_by_user_id` set to current user
- `created_at` and `updated_at` timestamps added

**6. Response**:
```json
{
  "id": "507f1f77bcf86cd799439012",
  "name": "Push Day",
  "description": "Chest, shoulders, triceps",
  "created_by_user_id": 42,
  "difficulty_level": "intermediate",
  "estimated_duration_minutes": 60,
  "total_exercises": 1,
  "exercises": [
    {
      "exercise": {
        "id": "507f1f77bcf86cd799439011",
        "name": "Bench Press",
        "category": "strength"
      },
      "order": 1,
      "target_sets": 4,
      "target_reps_min": 8,
      "target_reps_max": 12,
      "target_weight": 185.0,
      "rest_seconds": 90
    }
  ],
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

### Example: Tracking a Workout Session

**Complete Workout Flow**:

```
1. Create Session (planned)
   POST /api/workout-sessions/
   {
     "workout": "507f1f77bcf86cd799439012",
     "status": "planned"
   }
   → Returns session with id: "507f1f77bcf86cd799439020"

2. Start Session
   POST /api/workout-sessions/507f1f77bcf86cd799439020/start/
   → Sets status='in_progress', start_time=now

3. Log Exercise Sets (during workout)
   POST /api/exercise-logs/bulk_create/
   {
     "logs": [
       {
         "workout_session": "507f1f77bcf86cd799439020",
         "exercise": "507f1f77bcf86cd799439011",
         "set_number": 1,
         "reps": 12,
         "weight": 185
       },
       {
         "workout_session": "507f1f77bcf86cd799439020",
         "exercise": "507f1f77bcf86cd799439011",
         "set_number": 2,
         "reps": 10,
         "weight": 185
       }
     ]
   }

4. Complete Session
   POST /api/workout-sessions/507f1f77bcf86cd799439020/complete/
   {
     "rating": 4,
     "notes": "Great session!"
   }
   → Sets status='completed', end_time=now, calculates duration
```

---

## How Everything Fits Together

### The Complete Picture

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATION                    │
│              (Web App, Mobile App, etc.)                 │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP Requests (JSON)
                     │ Authorization: Token abc123
                     ↓
┌─────────────────────────────────────────────────────────┐
│                   DJANGO APPLICATION                     │
├─────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────┐    │
│  │         URL Routing Layer                       │    │
│  │  config/urls.py → workouts/urls.py             │    │
│  └──────────────────┬─────────────────────────────┘    │
│                     ↓                                    │
│  ┌────────────────────────────────────────────────┐    │
│  │         Authentication & Permissions            │    │
│  │  - Token Validation (PostgreSQL)               │    │
│  │  - Permission Checks (Custom Logic)            │    │
│  └──────────────────┬─────────────────────────────┘    │
│                     ↓                                    │
│  ┌────────────────────────────────────────────────┐    │
│  │         ViewSet Layer (Business Logic)          │    │
│  │  - ExerciseViewSet                             │    │
│  │  - WorkoutViewSet                              │    │
│  │  - WorkoutSessionViewSet                       │    │
│  │  - ExerciseLogViewSet                          │    │
│  └──────────────────┬─────────────────────────────┘    │
│                     ↓                                    │
│  ┌────────────────────────────────────────────────┐    │
│  │         Serializer Layer (Validation)           │    │
│  │  - Validate input data                         │    │
│  │  - Transform data types                        │    │
│  │  - Nested serialization                        │    │
│  └──────────────────┬─────────────────────────────┘    │
│                     ↓                                    │
│  ┌────────────────────────────────────────────────┐    │
│  │         Model Layer (Data Access)               │    │
│  │  - MongoEngine Documents                       │    │
│  │  - Validation constraints                      │    │
│  │  - Relationships                               │    │
│  └──────────────────┬─────────────────────────────┘    │
└────────────────────┬┴───────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ↓                         ↓
┌───────────────┐        ┌────────────────┐
│  PostgreSQL   │        │    MongoDB     │
│               │        │                │
│ - User        │        │ - UserProfile  │
│ - Token       │        │ - Exercise     │
│ - Session     │        │ - Workout      │
│ - Admin       │        │ - WorkoutSess. │
│               │        │ - ExerciseLog  │
└───────────────┘        └────────────────┘
  Django Built-in        Application Data
```

### Component Interaction Example: "Get My Workouts"

**Request**: `GET /api/workouts/?difficulty=intermediate`

**Flow**:

1. **URL Routing**:
   - Request hits `config/urls.py:30` → `include('workouts.urls')`
   - Routes to `workouts/urls.py` → Router matches to `WorkoutViewSet`

2. **Authentication** (Automatic):
   - DRF checks for `Authorization: Token abc123` header
   - Queries PostgreSQL `authtoken_token` table
   - Validates token and loads associated User

3. **ViewSet Processing** (`workouts/views.py:168-450`):
   - `WorkoutViewSet.list()` method called
   - `get_queryset()` filters workouts:
     - Base query: All workouts user can access
     - Apply filter: `difficulty='intermediate'`
     - Apply permission: User's own workouts or public workouts

4. **Database Query** (MongoDB):
   ```python
   Workout.objects.filter(
       Q(created_by_user_id=user.id) | Q(is_public=True),
       difficulty_level='intermediate'
   )
   ```

5. **Serialization** (`workouts/serializers.py:197-219`):
   - `WorkoutListSerializer` used for performance (minimal fields)
   - Converts MongoEngine documents to Python dicts
   - Includes nested exercise count

6. **Response**:
   ```json
   {
     "count": 15,
     "next": "http://api/workouts/?difficulty=intermediate&page=2",
     "previous": null,
     "results": [
       {
         "id": "507f1f77bcf86cd799439012",
         "name": "Push Day",
         "difficulty_level": "intermediate",
         "total_exercises": 6,
         "estimated_duration_minutes": 60
       },
       // ... more workouts
     ]
   }
   ```

### Why This Architecture Works

**1. Separation of Concerns**:
- **Models**: Define data structure and validation rules
- **Serializers**: Handle data transformation and API contracts
- **Views**: Implement business logic and orchestration
- **URLs**: Route requests to appropriate handlers

**2. Dual Database Benefits**:
- **PostgreSQL**: Handles Django's complex auth system with proven reliability
- **MongoDB**: Flexible schema for fitness data that varies widely (different exercise types, custom user data)

**3. Token Authentication**:
- Stateless: No session storage required
- Scalable: Can be distributed across multiple servers
- Simple: Easy for clients to implement

**4. ViewSet Pattern**:
- **DRY**: One ViewSet provides all CRUD operations
- **Extensible**: Easy to add custom actions (`clone`, `start`, `complete`)
- **Consistent**: All endpoints follow same pattern

**5. Serializer Optimization**:
- **List Serializers**: Minimal data for list views (fast, less bandwidth)
- **Detail Serializers**: Full data for detail views (complete information)
- **Nested Serializers**: Related data included automatically

### Deployment Architecture

```
Developer
   ↓
   (git push)
   ↓
GitHub Repository
   ↓
   (webhook trigger)
   ↓
GitHub Actions (.github/workflows/docker-build-push.yml)
   ├─ Build Docker image
   ├─ Push to DockerHub
   └─ Update Helm values (image tag)
   ↓
   (git commit)
   ↓
ArgoCD (monitors Git repository)
   ├─ Detects Helm values change
   ├─ Renders Helm chart
   └─ Applies to Kubernetes
   ↓
Kubernetes Cluster
   ├─ Creates/Updates Deployment
   ├─ Creates Service
   ├─ Creates ConfigMap & Secret
   └─ Runs health checks
   ↓
Application Running
   ├─ Connects to PostgreSQL
   ├─ Connects to MongoDB
   └─ Serves API requests
```

**Key Files**:
- **`Dockerfile`**: Defines container image
- **`helm/workout-api/`**: Kubernetes resource templates
- **`argocd/application.yaml`**: ArgoCD app definition
- **`.github/workflows/docker-build-push.yml`**: CI/CD pipeline

### Development Workflow

**Local Development**:
```bash
# 1. Activate Python virtual environment
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations (PostgreSQL only)
python manage.py migrate

# 4. Create superuser
python manage.py createsuperuser

# 5. Run development server
python manage.py runserver

# 6. Access API
curl http://localhost:8000/api/health/
```

**Production Deployment**:
```bash
# 1. Make code changes
git add .
git commit -m "Add new feature"

# 2. Push to GitHub
git push origin main

# 3. GitHub Actions automatically:
#    - Builds Docker image
#    - Pushes to DockerHub
#    - Updates Helm values with new image tag
#    - Commits changes back to repo

# 4. ArgoCD automatically:
#    - Detects Git changes
#    - Syncs to Kubernetes cluster
#    - Deploys new version

# 5. Monitor deployment
kubectl get pods -n woodez-database
kubectl logs -f deployment/workout-api -n woodez-database
```

---

## Key Takeaways

### What Makes This Application Work

1. **Dual Database Strategy**:
   - PostgreSQL handles authentication complexity
   - MongoDB handles flexible fitness data

2. **DRF ViewSets**:
   - Standardized CRUD operations
   - Easy to extend with custom actions
   - Built-in pagination and filtering

3. **Serializer Pattern**:
   - Validation before database
   - Transformation for API responses
   - Nested data handling

4. **Token Authentication**:
   - Stateless and scalable
   - Simple client implementation
   - Secure with HTTPS

5. **GitOps Deployment**:
   - Git as single source of truth
   - Automated CI/CD pipeline
   - Declarative infrastructure

### How to Extend

**Adding a New Model**:
1. Define model in `workouts/models.py`
2. Create serializers in `workouts/serializers.py`
3. Create ViewSet in `workouts/views.py`
4. Register in router in `workouts/urls.py`

**Adding a Custom Action**:
```python
class WorkoutViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    def my_custom_action(self, request, pk=None):
        workout = self.get_object()
        # Your logic here
        return Response({'status': 'success'})
```

**Adding Filtering**:
```python
def get_queryset(self):
    queryset = super().get_queryset()
    param = self.request.query_params.get('my_param')
    if param:
        queryset = queryset.filter(field=param)
    return queryset
```

### Common Operations

**Create Exercise → Build Workout → Track Session → Log Progress**:
```
1. POST /api/exercises/
   Create exercises in library

2. POST /api/workouts/
   Build workout template with exercises

3. POST /api/workout-sessions/
   Plan a workout session

4. POST /api/workout-sessions/{id}/start/
   Start the session

5. POST /api/exercise-logs/bulk_create/
   Log all sets as you complete them

6. POST /api/workout-sessions/{id}/complete/
   Complete session and record metrics

7. GET /api/exercise-logs/?date_from=2025-01-01
   View progress over time
```

---

## Summary

This Workout API is a production-ready Django REST Framework application that:

- **Manages fitness data** through a well-designed MongoDB schema
- **Authenticates users** with token-based auth via PostgreSQL
- **Provides a RESTful API** with comprehensive CRUD operations
- **Validates data** using DRF serializers
- **Deploys automatically** via GitOps with ArgoCD
- **Scales horizontally** with stateless architecture
- **Documents itself** with OpenAPI/Swagger

Every component has a specific responsibility, and they work together to provide a complete fitness tracking platform that's easy to use, extend, and maintain.
