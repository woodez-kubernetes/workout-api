# ArgoCD Deployment Guide

This guide explains how to deploy the Workout API to Kubernetes using ArgoCD for GitOps-based continuous delivery.

## Overview

The Workout API is deployed using:
- **Helm Chart**: `helm/workout-api/`
- **ArgoCD Application**: `argocd/application.yaml`
- **Target Namespace**: `woodez-database`
- **Database Services**:
  - PostgreSQL: `postgres-svc:5432`
  - MongoDB: `mongodb-headless:27017`

## Prerequisites

### 1. ArgoCD Installed

ArgoCD must be installed in your cluster:

```bash
# Check if ArgoCD is installed
kubectl get pods -n argocd

# If not installed, install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### 2. Database Services Running

Verify database services are available in the `woodez-database` namespace:

```bash
# Check PostgreSQL
kubectl get svc postgres-svc -n woodez-database

# Check MongoDB
kubectl get svc mongodb-headless -n woodez-database
```

### 3. Git Repository Access

ArgoCD needs access to your Git repository:

```bash
# Add repository to ArgoCD (if using private repo)
argocd repo add https://github.com/your-org/workout-api.git \
  --username your-username \
  --password your-token
```

## Quick Start

### Step 1: Update ArgoCD Application Manifest

Edit `argocd/application.yaml` and update:

```yaml
source:
  repoURL: https://github.com/YOUR-ORG/workout-api.git  # Your repo URL

  helm:
    values: |
      image:
        repository: YOUR-DOCKERHUB-USERNAME/workout-api  # Your Docker image
        tag: latest

      secrets:
        postgresPassword: YOUR-POSTGRES-PASSWORD
        mongodbPassword: YOUR-MONGODB-PASSWORD  # Leave empty if no auth
```

### Step 2: Deploy ArgoCD Application

```bash
# Apply the ArgoCD Application
kubectl apply -f argocd/application.yaml

# Or using kustomize
kubectl apply -k argocd/
```

### Step 3: Verify Deployment

```bash
# Check ArgoCD application status
argocd app get workout-api

# Watch the sync status
argocd app sync workout-api --watch

# Check pods
kubectl get pods -n woodez-database -l app.kubernetes.io/name=workout-api
```

## ArgoCD Application Configuration

### Application Spec

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: workout-api
  namespace: argocd
spec:
  project: default

  source:
    repoURL: https://github.com/your-org/workout-api.git
    targetRevision: HEAD  # Can be: branch, tag, or commit SHA
    path: helm/workout-api

  destination:
    server: https://kubernetes.default.svc
    namespace: woodez-database
```

### Sync Policy

The application is configured with automated sync:

```yaml
syncPolicy:
  automated:
    prune: true        # Delete resources not in Git
    selfHeal: true     # Auto-sync when cluster state drifts
    allowEmpty: false

  syncOptions:
    - CreateNamespace=true
    - ServerSideApply=true

  retry:
    limit: 5
    backoff:
      duration: 5s
      factor: 2
      maxDuration: 3m
```

**What this means:**
- ArgoCD automatically syncs when you push to Git
- If someone manually changes cluster resources, ArgoCD reverts them
- Failed syncs are retried with exponential backoff
- Namespace is created automatically if it doesn't exist

### Sync Waves

Resources are deployed in order using sync waves:

1. **Wave 1** (ConfigMap, Secret) - Deploy first
2. **Wave 2** (Deployment) - Deploy after config is ready

This ensures the Deployment always has the latest configuration.

## Configuration Management

### Using Helm Values

#### Option 1: Edit ArgoCD Application

Update values directly in `argocd/application.yaml`:

```yaml
source:
  helm:
    values: |
      replicaCount: 3

      resources:
        limits:
          cpu: 2000m
          memory: 2Gi
```

#### Option 2: Use External Values File

Create `helm/workout-api/values-production.yaml`:

```yaml
replicaCount: 3
image:
  tag: v1.0.0
```

Reference it in the Application:

```yaml
source:
  helm:
    valueFiles:
      - values.yaml
      - values-production.yaml
```

### Managing Secrets

**IMPORTANT**: Never commit secrets to Git!

#### Option 1: Sealed Secrets (Recommended)

```bash
# Install Sealed Secrets
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Create sealed secret
echo -n 'my-postgres-password' | \
  kubectl create secret generic workout-api-db-secret \
    --dry-run=client \
    --from-file=password=/dev/stdin \
    -o yaml | \
  kubeseal -o yaml > sealed-secret.yaml

# Commit sealed-secret.yaml to Git
```

#### Option 2: External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: workout-api-secrets
  namespace: woodez-database
spec:
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: workout-api-secret
  data:
    - secretKey: POSTGRES_PASSWORD
      remoteRef:
        key: database/postgres
        property: password
```

#### Option 3: ArgoCD Vault Plugin

Use ArgoCD's Vault plugin to inject secrets at deployment time.

## Deployment Workflows

### Development Workflow

1. **Make changes** to code
2. **Build and push** Docker image with `dev` tag
3. **Update** `image.tag: dev` in ArgoCD Application
4. **Commit and push** to Git
5. **ArgoCD automatically syncs** the change

```bash
# Build and push
docker build -t your-username/workout-api:dev .
docker push your-username/workout-api:dev

# Update values
git commit -am "Update dev image"
git push

# ArgoCD syncs automatically
```

### Production Workflow

1. **Tag release** in Git
2. **Build image** with version tag
3. **Update** `image.tag` to version
4. **Create PR** for review
5. **Merge** - ArgoCD deploys to production

```bash
# Tag release
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Build and push
docker build -t your-username/workout-api:v1.0.0 .
docker push your-username/workout-api:v1.0.0

# Update ArgoCD application
# Create PR with image.tag: v1.0.0
# Merge PR - ArgoCD deploys
```

### Rollback

```bash
# Using ArgoCD CLI
argocd app rollback workout-api

# Or revert Git commit
git revert HEAD
git push

# ArgoCD syncs previous version
```

## Monitoring Deployment

### ArgoCD UI

Access the ArgoCD UI:

```bash
# Port-forward to ArgoCD server
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d

# Open browser
open https://localhost:8080
# Login: admin / <password from above>
```

In the UI, you'll see:
- Application health status
- Sync status
- Resource tree view
- Recent sync history
- Logs for each resource

### ArgoCD CLI

```bash
# Get application details
argocd app get workout-api

# View sync status
argocd app sync workout-api --dry-run

# View differences
argocd app diff workout-api

# View logs
argocd app logs workout-api

# View resource details
argocd app resources workout-api
```

### Kubectl

```bash
# Check deployment status
kubectl rollout status deployment/workout-api -n woodez-database

# View pods
kubectl get pods -n woodez-database -l app.kubernetes.io/name=workout-api

# View logs
kubectl logs -n woodez-database -l app.kubernetes.io/name=workout-api --tail=100 -f

# Check events
kubectl get events -n woodez-database --sort-by='.lastTimestamp'
```

## Health Checks

ArgoCD monitors application health using:

### Resource Health

ArgoCD checks:
- Pods are Running
- Deployments are fully available
- Services have endpoints
- Ingress has hosts configured

### Custom Health Checks

The Workout API provides:

```yaml
livenessProbe:
  httpGet:
    path: /api/health/
    port: 8000
  initialDelaySeconds: 60

readinessProbe:
  httpGet:
    path: /api/health/
    port: 8000
  initialDelaySeconds: 30
```

Test manually:

```bash
kubectl port-forward -n woodez-database svc/workout-api 8000:8000
curl http://localhost:8000/api/health/
```

## Sync Strategies

### Auto-Sync (Default)

ArgoCD automatically syncs when:
- Git repository changes
- Cluster state drifts from desired state

```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: true
```

### Manual Sync

Disable auto-sync for manual control:

```yaml
syncPolicy:
  automated: null  # Disable auto-sync
```

Then sync manually:

```bash
argocd app sync workout-api
```

### Selective Sync

Sync specific resources:

```bash
# Sync only ConfigMap
argocd app sync workout-api --resource ConfigMap:workout-api-config
```

## Troubleshooting

### Application Out of Sync

**Problem**: ArgoCD shows "OutOfSync"

**Solution**:
```bash
# View differences
argocd app diff workout-api

# Hard refresh (bypass cache)
argocd app get workout-api --hard-refresh

# Force sync
argocd app sync workout-api --force
```

### Sync Failed

**Problem**: Sync failed with errors

**Solution**:
```bash
# View detailed error
argocd app get workout-api

# Check ArgoCD logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller

# Validate Helm chart
helm template helm/workout-api --debug
```

### Pods Not Starting

**Problem**: Pods in CrashLoopBackOff

**Solution**:
```bash
# Check pod logs
kubectl logs -n woodez-database deployment/workout-api

# Check events
kubectl describe pod -n woodez-database -l app.kubernetes.io/name=workout-api

# Verify database connectivity
kubectl exec -it -n woodez-database deployment/workout-api -- \
  nc -zv postgres-svc 5432
```

### Health Check Failing

**Problem**: Liveness/Readiness probes failing

**Solution**:
```bash
# Test health endpoint
kubectl port-forward -n woodez-database svc/workout-api 8000:8000
curl http://localhost:8000/api/health/

# Check if migrations ran
kubectl exec -it -n woodez-database deployment/workout-api -- \
  python manage.py showmigrations

# Run migrations manually
kubectl exec -it -n woodez-database deployment/workout-api -- \
  python manage.py migrate
```

### Database Connection Issues

**Problem**: Cannot connect to PostgreSQL or MongoDB

**Solution**:
```bash
# Verify services exist
kubectl get svc -n woodez-database postgres-svc mongodb-headless

# Test connectivity from pod
kubectl exec -it -n woodez-database deployment/workout-api -- \
  nc -zv postgres-svc 5432

kubectl exec -it -n woodez-database deployment/workout-api -- \
  nc -zv mongodb-headless 27017

# Check DNS resolution
kubectl exec -it -n woodez-database deployment/workout-api -- \
  nslookup postgres-svc
```

## Best Practices

### 1. Use Git Branches

- **main/master**: Production deployments
- **develop**: Development deployments
- **feature/***: Feature branches

```yaml
# Production
targetRevision: main

# Development
targetRevision: develop

# Specific version
targetRevision: v1.0.0
```

### 2. Environment-Specific Values

Create values files per environment:

```
helm/workout-api/
├── values.yaml              # Base values
├── values-dev.yaml          # Dev overrides
├── values-staging.yaml      # Staging overrides
└── values-production.yaml   # Production overrides
```

### 3. Use Projects

Organize applications by project:

```yaml
spec:
  project: workout-api  # Instead of 'default'
```

### 4. Enable Notifications

Configure Slack/email notifications:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
  namespace: argocd
data:
  service.slack: |
    token: $slack-token
  trigger.on-deployed: |
    - when: app.status.operationState.phase in ['Succeeded']
      send: [app-deployed]
```

### 5. Use Sync Windows

Restrict deployments to specific times:

```yaml
syncPolicy:
  syncWindows:
    - kind: allow
      schedule: '0 9 * * 1-5'  # Mon-Fri 9am
      duration: 8h
      applications:
        - workout-api
```

## Advanced Features

### App of Apps Pattern

Deploy multiple related applications:

```yaml
# argocd/apps.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: workout-platform
spec:
  source:
    path: argocd/applications/
  syncPolicy:
    automated: {}
---
# argocd/applications/api.yaml
<workout-api application>

# argocd/applications/frontend.yaml
<workout-frontend application>
```

### Progressive Delivery

Use Argo Rollouts for canary/blue-green deployments:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: workout-api
spec:
  strategy:
    canary:
      steps:
        - setWeight: 20
        - pause: {duration: 1h}
        - setWeight: 50
        - pause: {duration: 1h}
```

### Multi-Cluster Deployment

Deploy to multiple clusters:

```yaml
# Production Cluster
destination:
  server: https://prod-cluster.example.com

# DR Cluster
destination:
  server: https://dr-cluster.example.com
```

## Additional Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Helm Chart Best Practices](https://helm.sh/docs/chart_best_practices/)
- [GitOps Principles](https://opengitops.dev/)
- [Workout API Helm Chart](./helm/workout-api/)

## Support

For issues or questions:
- Check ArgoCD UI for detailed error messages
- Review pod logs: `kubectl logs -n woodez-database`
- Consult CLAUDE.md for project-specific guidance
- Open an issue in the GitHub repository
