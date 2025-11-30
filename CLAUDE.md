# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django REST Framework-based workout API using a dual database architecture. The API will be deployed to a Kubernetes cluster with existing database instances.

**Tech Stack**:
- Django 5.2 + Django REST Framework 3.16
- PostgreSQL (for Django auth models: User, Token, Sessions)
- MongoDB via MongoEngine (for application data models)
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
# Edit .env with your MongoDB credentials
```

**Key Environment Variables**:
- `SECRET_KEY` - Django secret key (auto-generated)
- `DEBUG` - Set to `False` in production
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts

**PostgreSQL (Django Auth)**:
- `POSTGRES_DB` - Database name (default: woodez-auth)
- `POSTGRES_USER` - PostgreSQL username
- `POSTGRES_PASSWORD` - PostgreSQL password
- `POSTGRES_HOST` - PostgreSQL hostname (localhost for dev)
- `POSTGRES_PORT` - PostgreSQL port (default: 5432)

**MongoDB (Application Data)**:
- `MONGODB_HOST` - MongoDB hostname (localhost for dev)
- `MONGODB_PORT` - MongoDB port (default: 27017)
- `MONGODB_DB_NAME` - Database name (default: workout_db)
- `MONGODB_USERNAME` - MongoDB username
- `MONGODB_PASSWORD` - MongoDB password

**Connecting to K8s MongoDB locally**:
```bash
# Port-forward MongoDB from K8s cluster
kubectl port-forward service/mongodb-service 27012:27017

# Then use localhost:27012 in .env
MONGODB_HOST=localhost
MONGODB_PORT=27012
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
python test_auth_simple.py  # Tests Django/PostgreSQL auth only
python test_auth.py         # Full tests including MongoDB (requires correct credentials)
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
- ✅ Stage 2: Django project initialization with dual database (PostgreSQL + MongoDB)
- ✅ Stage 3: Data models using MongoEngine (UserProfile, Exercise, Workout, WorkoutSession, ExerciseLog)
- ✅ Stage 4: REST API endpoints with ViewSets, filtering, permissions
- ✅ Stage 5: Authentication system (registration, login, logout, profile management)

**Current Status**: Ready for Stage 6

**Next Steps**:
- Stage 6: Kubernetes deployment (ConfigMaps, Secrets, Deployment, Service, Ingress)
- Stage 7: Testing and documentation

**Known Issues**:
- MongoDB credentials in .env need to be updated to match actual database for UserProfile functionality
- Current setup works with Django/PostgreSQL auth; MongoDB features gracefully degrade

See [STAGE5_COMPLETE.md](STAGE5_COMPLETE.md) for detailed authentication implementation notes.
