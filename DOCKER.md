# Docker Setup Guide

This guide explains how to build and run the Workout API using Docker/Podman.

## Prerequisites

- Docker or Podman installed
- DockerHub account (for pushing images)

## Building the Image

### Using Docker
```bash
docker build -t workout-api:latest .
```

### Using Podman
```bash
podman build -t workout-api:latest .
```

## Running the Container Locally

### Environment Variables Required

Create a `.env` file with the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL (Django Auth)
POSTGRES_DB=woodez-auth
POSTGRES_USER=workout_admin
POSTGRES_PASSWORD=your-password
POSTGRES_HOST=postgres-host
POSTGRES_PORT=5432

# MongoDB (Application Data)
MONGODB_HOST=mongodb-host
MONGODB_PORT=27017
MONGODB_DB_NAME=workoutdb
MONGODB_USERNAME=
MONGODB_PASSWORD=
```

### Run the Container

```bash
# Using Docker
docker run -d \
  --name workout-api \
  --env-file .env \
  -p 8000:8000 \
  workout-api:latest

# Using Podman
podman run -d \
  --name workout-api \
  --env-file .env \
  -p 8000:8000 \
  workout-api:latest
```

### Health Check

The container includes a health check endpoint:

```bash
curl http://localhost:8000/api/health/
```

Expected response:
```json
{
  "status": "healthy",
  "service": "workout-api"
}
```

## Pushing to DockerHub

### Tag the Image

```bash
# Using Docker
docker tag workout-api:latest <your-dockerhub-username>/workout-api:latest

# Using Podman
podman tag workout-api:latest <your-dockerhub-username>/workout-api:latest
```

### Login to DockerHub

```bash
# Using Docker
docker login

# Using Podman
podman login docker.io
```

### Push the Image

```bash
# Using Docker
docker push <your-dockerhub-username>/workout-api:latest

# Using Podman
podman push <your-dockerhub-username>/workout-api:latest
```

## GitHub Actions Setup

This repository includes a GitHub Actions workflow that automatically builds and pushes images to DockerHub.

### Required GitHub Secrets

Add the following secrets to your GitHub repository:

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Add the following secrets:

- `DOCKERHUB_USERNAME`: Your DockerHub username
- `DOCKERHUB_TOKEN`: Your DockerHub access token (create one at https://hub.docker.com/settings/security)

### Workflow Triggers

The workflow automatically runs on:
- Push to `master`, `main`, or `develop` branches
- New tags matching `v*.*.*` (semantic versioning)
- Pull requests to `master` or `main`
- Manual workflow dispatch

### Image Tags

The workflow creates the following tags:
- `latest` - Latest version from master/main branch
- `<branch-name>` - Branch-specific builds
- `v1.0.0`, `v1.0`, `v1` - Semantic version tags
- `<branch>-<sha>` - Commit-specific tags

## Multi-Architecture Support

The GitHub Actions workflow builds images for multiple architectures:
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64, including Apple Silicon)

## Container Details

### Image Layers
1. **Builder stage**: Compiles Python dependencies
2. **Runtime stage**: Minimal runtime image with only necessary components

### Features
- Multi-stage build for smaller image size
- Non-root user for security
- Health check endpoint
- Automatic migrations on startup
- Static file collection
- Gunicorn WSGI server with 4 workers

### Exposed Ports
- `8000` - HTTP API

### Volumes (Optional)
You can mount volumes for:
- `/app/staticfiles` - Static files
- `/app/media` - User-uploaded media files

### Security
- Runs as non-root user (`django`)
- Minimal attack surface (slim base image)
- No unnecessary packages installed
- Environment-based configuration (no hardcoded secrets)

## Troubleshooting

### Container won't start
Check logs:
```bash
# Docker
docker logs workout-api

# Podman
podman logs workout-api
```

### Database connection errors
Ensure your PostgreSQL and MongoDB hosts are accessible from the container. If using `localhost`, it refers to the container itself, not your host machine. Use:
- `host.docker.internal` (Docker Desktop)
- Actual IP address or hostname of database server

### Health check failing
```bash
# Docker
docker exec workout-api wget -O- http://localhost:8000/api/health/

# Podman
podman exec workout-api wget -O- http://localhost:8000/api/health/
```

### Migrations not running
The container runs migrations automatically on startup. Check logs for migration errors.

## Development vs Production

### Development
- Set `DEBUG=True`
- Use `-v $(pwd):/app` to mount code for live reload
- Install development dependencies

### Production
- Set `DEBUG=False`
- Set proper `ALLOWED_HOSTS`
- Use environment variables for all secrets
- Consider using orchestration (Kubernetes, Docker Compose)
- Set up proper logging and monitoring
- Use HTTPS/TLS termination (via reverse proxy or ingress)

## Docker Compose (Optional)

For local development with databases included, create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: woodez-auth
      POSTGRES_USER: workout_admin
      POSTGRES_PASSWORD: password123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - postgres
      - mongodb

volumes:
  postgres_data:
  mongo_data:
```

Run with:
```bash
docker-compose up -d
```

## Resources

- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [GitHub Actions Docker Build](https://docs.docker.com/build/ci/github-actions/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
