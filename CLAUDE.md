# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django REST Framework-based workout API using PostgreSQL for all data storage. The API is deployed to a Kubernetes cluster.

**Tech Stack**:
- Django 5.2 + Django REST Framework 3.16
- PostgreSQL (for all data: User, Token, Sessions, and application models)
- Django ORM with PostgreSQL-specific features (ArrayField)
- Token-based authentication (DRF TokenAuthentication)
- Deployed on Kubernetes

## Python Environment Setup

**CRITICAL**: Always activate the Python virtual environment before installing any pip modules.

```bash
# Create virtual environment (first time only)
python3 -m venv venv

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Environment Configuration

The project uses environment variables for configuration. Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

**Key Environment Variables**:
- `SECRET_KEY` - Django secret key (auto-generated)
- `DEBUG` - Set to `False` in production
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts

**PostgreSQL (All Data)**:
- `POSTGRES_DB` - Database name (default: woodez-auth)
- `POSTGRES_USER` - PostgreSQL username
- `POSTGRES_PASSWORD` - PostgreSQL password
- `POSTGRES_HOST` - PostgreSQL hostname (localhost for dev)
- `POSTGRES_PORT` - PostgreSQL port (default: 5432)

**Connecting to K8s PostgreSQL locally**:
```bash
# Port-forward PostgreSQL from K8s cluster
kubectl port-forward service/postgres-svc 5432:5432

# Then use localhost:5432 in .env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

## Development Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run development server
python manage.py runserver

# Run tests
pytest
pytest --cov  # with coverage report

# Linting and formatting
ruff check .
ruff format .

# Type checking
mypy workouts/

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell

# Test authentication endpoints
python test_auth_simple.py  # Tests authentication endpoints
```

## Project Structure

```
workout-api/
├── config/           # Django project settings
├── workouts/         # Main app (models, views, serializers)
├── k8s/             # Kubernetes manifests (ConfigMap, Secret, Deployment, etc.)
├── .env             # Local environment variables (DO NOT COMMIT)
├── .env.example     # Environment template
├── requirements.txt # Python dependencies
├── plan.md          # Implementation plan
└── CLAUDE.md        # This file
```

## Deployment

See [plan.md](plan.md) Stage 6 for detailed Kubernetes deployment instructions.

**Quick deployment**:
```bash
# Build Docker image
docker build -t your-registry/workout-api:latest .

# Push to registry
docker push your-registry/workout-api:latest

# Apply K8s manifests
kubectl apply -f k8s/
```

## Development Status

**Completed Stages**:
- ✅ Stage 1: Project setup, virtual environment, dependencies, .env configuration
- ✅ Stage 2: Django project initialization with PostgreSQL database
- ✅ Stage 3: Data models using Django ORM (UserProfile, Exercise, Workout, WorkoutExercise, WorkoutSession, ExerciseLog)
- ✅ Stage 4: REST API endpoints with ViewSets, filtering, permissions
- ✅ Stage 5: Authentication system (registration, login, logout, profile management)
- ✅ Stage 6: Migration from MongoDB to PostgreSQL (single database architecture)

**Current Status**: Ready for deployment and testing

**Architecture**:
- **Single Database**: All data stored in PostgreSQL using Django ORM
- **Django Models**: Full Django ORM with PostgreSQL-specific features
  - `UserProfile`: OneToOneField to User model
  - `Exercise`: ArrayField for muscle_groups, equipment_required, instructions
  - `Workout`: ForeignKey to UserProfile, ArrayField for tags
  - `WorkoutExercise`: Separate model (formerly EmbeddedDocument)
  - `WorkoutSession`: ForeignKey relationships
  - `ExerciseLog`: ForeignKey relationships
- **No MongoDB**: MongoEngine removed, all MongoDB configuration cleaned up

**Next Steps**:
- Apply migrations to production database: `python manage.py migrate`
- Test all API endpoints
- Kubernetes deployment (updated without MongoDB)
