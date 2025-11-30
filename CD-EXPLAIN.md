# Continuous Deployment Explained

This document explains how the complete CI/CD pipeline works for the Workout API, including GitHub Actions, DockerHub, ArgoCD, and Kubernetes.

## Table of Contents

1. [Overview](#overview)
2. [Components](#components)
3. [Secrets Management](#secrets-management)
4. [Current Workflow](#current-workflow)
5. [ArgoCD Application Manifest](#argocd-application-manifest)
6. [Kustomization](#kustomization)
7. [Integration Options](#integration-options)
8. [Recommended Setup](#recommended-setup)
9. [Complete Flow Diagrams](#complete-flow-diagrams)

---

## Overview

The Workout API uses a **GitOps-based continuous deployment** approach:

- **Continuous Integration (CI)**: GitHub Actions builds and pushes Docker images
- **Continuous Deployment (CD)**: ArgoCD watches Git and deploys to Kubernetes
- **Source of Truth**: Git repository (not the cluster)
- **Automation**: Deployments happen automatically when you push to Git

### Key Principle: GitOps

```
Git Repository = Desired State
Kubernetes Cluster = Actual State

ArgoCD ensures: Actual State = Desired State
```

---

## Components

### 1. GitHub Actions (`.github/workflows/docker-build-push.yml`)

**Purpose**: Build and publish Docker images

**Triggers**:
- Push to `master`, `main`, or `develop` branches
- New Git tags matching `v*.*.*`
- Pull requests
- Manual workflow dispatch

**What it does**:
1. Checks out code
2. Builds Docker image
3. Pushes to DockerHub with multiple tags:
   - `latest` (for default branch)
   - `<branch-name>` (e.g., `main`, `develop`)
   - `<branch>-<sha>` (e.g., `main-abc123`)
   - `v1.2.3` (for version tags)

**Outputs**:
- Docker images in DockerHub at: `your-username/workout-api`

### 2. Helm Chart (`helm/workout-api/`)

**Purpose**: Define Kubernetes resources and configuration

**Resources Created**:
- Deployment (API pods)
- Service (ClusterIP)
- ConfigMap (environment configuration)
- Secret (sensitive data)
- ServiceAccount
- Ingress (optional)
- HorizontalPodAutoscaler (optional)

**Configuration**:
- `Chart.yaml`: Chart metadata
- `values.yaml`: Default configuration values
- `templates/`: Kubernetes resource templates

### 3. ArgoCD Application (`argocd/application.yaml`)

**Purpose**: Tell ArgoCD how to deploy the application

**Key Responsibilities**:
- Watch Git repository for changes
- Render Helm chart with values
- Sync Kubernetes cluster with Git state
- Monitor application health
- Auto-heal cluster drift

### 4. Kustomization (`argocd/kustomization.yaml`)

**Purpose**: Manage and customize Kubernetes manifests

**What it does**:
- Adds namespace to all resources
- Adds common labels
- Allows environment-specific overlays

---

## Secrets Management

**Critical Concept:** There are **TWO completely separate secret systems** in this pipeline!

### The Two Secret Systems

```
┌──────────────────────────────────────────────────────────┐
│           1. GitHub Secrets (CI/CD Only)                 │
│                                                          │
│  Used in: GitHub Actions workflows                       │
│  Purpose: Build and push Docker images                   │
│  Access: GitHub Actions runners only                     │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
                    Build & Push
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│              2. Kubernetes Secrets (Runtime)             │
│                                                          │
│  Used in: Application pods at runtime                    │
│  Purpose: Database passwords, API keys, etc.             │
│  Access: Kubernetes pods only                            │
└──────────────────────────────────────────────────────────┘
```

**Important:** These two systems don't talk to each other!

---

### GitHub Secrets (CI/CD)

**Purpose:** Authenticate GitHub Actions to build and push Docker images to DockerHub.

**Where they're used:** Only in `.github/workflows/docker-build-push.yml`

**Required Secrets:**

| Secret Name | Description | How to Get It |
|-------------|-------------|---------------|
| `DOCKERHUB_USERNAME` | Your DockerHub username | Your DockerHub account name |
| `DOCKERHUB_PASSWORD` | DockerHub access token | Create at DockerHub → Account Settings → Security → New Access Token |

**Setting Up GitHub Secrets:**

1. **Create DockerHub Access Token:**
   ```
   Go to: https://hub.docker.com/settings/security
   Click: New Access Token
   Name: workout-api-github-actions
   Permissions: Read, Write, Delete
   Copy the token (you'll only see it once!)
   ```

2. **Add to GitHub Repository:**
   ```
   Go to: Your Repo → Settings → Secrets and variables → Actions
   Click: New repository secret

   Name: DOCKERHUB_USERNAME
   Value: your-dockerhub-username

   Name: DOCKERHUB_PASSWORD
   Value: dckr_pat_abc123xyz... (the token you copied)
   ```

3. **How they're used in the workflow:**
   ```yaml
   # .github/workflows/docker-build-push.yml
   - name: Log in to DockerHub
     uses: docker/login-action@v3
     with:
       username: ${{ secrets.DOCKERHUB_USERNAME }}  # ← From GitHub Secrets
       password: ${{ secrets.DOCKERHUB_PASSWORD }}  # ← From GitHub Secrets
   ```

**Security Notes:**
- ✅ GitHub Secrets are encrypted at rest
- ✅ Never exposed in logs or pull requests
- ✅ Only accessible during workflow execution
- ❌ **Cannot** be accessed by Kubernetes pods
- ❌ **Cannot** be used for runtime application secrets

---

### Kubernetes Secrets (Runtime)

**Purpose:** Store sensitive data that the application needs while running (database passwords, Django secret key, etc.).

**Where they're used:** In Kubernetes pods via environment variables

**Required Secrets:**

| Secret Key | Description | Used By |
|------------|-------------|---------|
| `django-secret-key` | Django's SECRET_KEY for cryptography | Django application |
| `postgres-password` | PostgreSQL database password | Database connection |
| `mongodb-password` | MongoDB password (optional) | Database connection |

**Creating Kubernetes Secrets:**

```bash
# 1. Generate a Django secret key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
# Output: django-insecure-abc123xyz...

# 2. Create the secret in Kubernetes
kubectl create secret generic workout-api-secrets \
  --from-literal=django-secret-key='django-insecure-abc123xyz...' \
  --from-literal=postgres-password='your-postgres-password' \
  --from-literal=mongodb-password='' \
  --namespace=woodez-database

# 3. Verify the secret was created
kubectl get secret workout-api-secrets -n woodez-database

# 4. (Optional) View the secret contents
kubectl get secret workout-api-secrets -n woodez-database -o yaml
```

**How Helm Uses Kubernetes Secrets:**

```yaml
# helm/workout-api/templates/deployment.yaml
env:
  - name: DJANGO_SECRET_KEY
    valueFrom:
      secretKeyRef:
        name: workout-api-secrets
        key: django-secret-key  # ← From Kubernetes Secret

  - name: POSTGRES_PASSWORD
    valueFrom:
      secretKeyRef:
        name: workout-api-secrets
        key: postgres-password  # ← From Kubernetes Secret
```

**Important Notes:**
- ⚠️ Secrets in `values.yaml` are **placeholder values only**
- ⚠️ **Never commit real secrets to Git!**
- ✅ Create Kubernetes secrets **manually** before deploying
- ✅ Or use a secrets management tool (see below)

---

### Why Two Separate Secret Systems?

**Different Purposes:**

```
GitHub Secrets:
  "How do I authenticate to build and publish?"
  → Used during CI/CD pipeline
  → Accessed by GitHub Actions runners
  → Never in the cluster

Kubernetes Secrets:
  "What password does my app use to connect to the database?"
  → Used during runtime
  → Accessed by application pods
  → Never in GitHub
```

**They Never Mix:**

```
┌─────────────────────┐
│  GitHub Secrets     │  ─┐
│  (DOCKERHUB_*)      │   │
└─────────────────────┘   │
                          ├─ Different systems,
┌─────────────────────┐   │  different purposes,
│ Kubernetes Secrets  │   │  don't interact!
│ (django-secret-key) │  ─┘
└─────────────────────┘
```

---

### Best Practices

**✅ DO:**
- Store DockerHub credentials in GitHub Secrets
- Create Kubernetes secrets manually in each cluster
- Use placeholder values in `values.yaml` (committed to Git)
- Rotate secrets regularly
- Use different secrets for dev/staging/production

**❌ DON'T:**
- Commit real secrets to Git (even in private repos)
- Try to use GitHub Secrets in Kubernetes
- Share secrets via email or chat
- Reuse production secrets in development

---

### Advanced: Secrets Management Tools

For production, consider using dedicated secrets management tools:

**Option 1: Sealed Secrets (Bitnami)**
- Encrypt secrets so they can be safely stored in Git
- Secrets are encrypted on commit, decrypted in cluster

```bash
# Install
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Use
kubectl create secret generic workout-api-secrets \
  --from-literal=postgres-password='mypassword' \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > sealed-secret.yaml

# Safe to commit!
git add sealed-secret.yaml
```

**Option 2: External Secrets Operator**
- Sync secrets from external providers (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault)

**Option 3: HashiCorp Vault**
- Centralized secrets management with dynamic secrets
- Advanced features: secret rotation, audit logs, fine-grained access control

---

## Current Workflow

### What Works Now

```
┌─────────────────────────────────────────────────────────────┐
│  1. Developer pushes code to GitHub                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  2. GitHub Actions Workflow Triggers                        │
│     - Builds Docker image                                   │
│     - Tags: latest, main, main-abc123                       │
│     - Pushes to DockerHub                                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Image Available in DockerHub                            │
│     ✅ your-username/workout-api:latest                     │
│     ✅ your-username/workout-api:main                       │
│     ✅ your-username/workout-api:main-abc123                │
└─────────────────────────────────────────────────────────────┘
```

### What's Missing

**Problem**: ArgoCD doesn't know about the new image because the Git repository still references the old tag!

```yaml
# helm/workout-api/values.yaml (in Git)
image:
  repository: your-username/workout-api
  tag: "latest"  # ← This never changes!
```

**Result**: ArgoCD won't deploy the new image automatically because the Helm values haven't changed.

---

## ArgoCD Application Manifest

The `argocd/application.yaml` file tells ArgoCD **what, where, and how** to deploy.

### Full Manifest Breakdown

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: workout-api
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io

spec:
  # Project this app belongs to
  project: default

  # SOURCE: Where to get the application
  source:
    # Git repository URL
    repoURL: https://github.com/your-org/workout-api.git

    # Which branch/tag/commit to deploy
    targetRevision: HEAD

    # Path to Helm chart in repo
    path: helm/workout-api

    # Helm configuration
    helm:
      releaseName: workout-api
      valueFiles:
        - values.yaml

      # Override values inline
      values: |
        image:
          repository: your-dockerhub-username/workout-api
          tag: latest

        namespace: woodez-database

        config:
          postgres:
            host: postgres-svc
            port: 5432
            database: woodez-auth
            username: workout_admin

          mongodb:
            host: mongodb-headless
            port: 27017
            database: workoutdb
            username: ""

        secrets:
          postgresPassword: jandrew28
          mongodbPassword: ""

  # DESTINATION: Where to deploy
  destination:
    # Kubernetes cluster (in-cluster)
    server: https://kubernetes.default.svc

    # Target namespace
    namespace: woodez-database

  # SYNC POLICY: How to deploy
  syncPolicy:
    # Automated sync
    automated:
      # Delete resources not in Git
      prune: true

      # Revert manual changes
      selfHeal: true

      # Don't sync empty
      allowEmpty: false

    # Sync options
    syncOptions:
      - CreateNamespace=true
      - RespectIgnoreDifferences=true
      - ServerSideApply=true

    # Retry on failure
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m

  # Ignore certain field differences
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas  # HPA manages this
```

### Key Concepts Explained

#### 1. **Source Configuration**

```yaml
source:
  repoURL: https://github.com/your-org/workout-api.git
  targetRevision: HEAD
  path: helm/workout-api
```

**What it does**:
- **repoURL**: Your Git repository (source of truth)
- **targetRevision**: Which version to deploy
  - `HEAD` = latest commit on default branch
  - `main` = latest on main branch
  - `v1.2.0` = specific version tag
  - `abc123` = specific commit SHA
- **path**: Where in repo to find the Helm chart

**ArgoCD polls this repo** every 3 minutes for changes.

#### 2. **Helm Values**

```yaml
helm:
  valueFiles:
    - values.yaml  # ArgoCD watches this file for changes
```

**What it does**:
- ArgoCD reads values from `helm/workout-api/values.yaml`
- When values.yaml changes in Git, ArgoCD detects it
- Can also use inline values to override specific settings

**Best Practice**: Update `values.yaml` in the Helm chart, not inline values in the Application manifest. This keeps infrastructure config (ArgoCD) separate from app config (image tags).

#### 3. **Automated Sync Policy**

```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: true
```

**What each does**:

##### **prune: true**
- Deletes resources removed from Git
- Example: Delete a ConfigMap from Git → ArgoCD deletes it from cluster

##### **selfHeal: true**
- Reverts manual cluster changes
- Example: Someone runs `kubectl edit deployment` → ArgoCD reverts it
- Enforces "Git is source of truth"

##### **Without automation:**
- You'd have to manually click "Sync" in ArgoCD UI
- Or run: `argocd app sync workout-api`

#### 4. **Sync Options**

```yaml
syncOptions:
  - CreateNamespace=true
  - ServerSideApply=true
```

**CreateNamespace=true**:
- Auto-creates `woodez-database` namespace if missing
- No need to create namespace manually

**ServerSideApply=true**:
- Uses Kubernetes server-side apply
- Better conflict resolution
- Recommended for production

#### 5. **Retry Configuration**

```yaml
retry:
  limit: 5
  backoff:
    duration: 5s
    factor: 2
    maxDuration: 3m
```

**What it does**:
- Retries failed syncs automatically
- Exponential backoff:
  - 1st retry: 5 seconds
  - 2nd retry: 10 seconds (5s × 2)
  - 3rd retry: 20 seconds (10s × 2)
  - 4th retry: 40 seconds (20s × 2)
  - 5th retry: 80 seconds, capped at 3 minutes

**Why it matters**:
- Temporary network issues
- Database not ready yet
- Image pull delays

#### 6. **Ignore Differences**

```yaml
ignoreDifferences:
  - group: apps
    kind: Deployment
    jsonPointers:
      - /spec/replicas
```

**What it does**:
- Don't mark app as "OutOfSync" for replica count differences
- **Why?** HorizontalPodAutoscaler dynamically changes replicas
- ArgoCD won't fight HPA by reverting replicas to Git value

**Other examples**:
```yaml
ignoreDifferences:
  # Ignore secret data (managed by Vault)
  - kind: Secret
    jsonPointers:
      - /data

  # Ignore annotations added by other controllers
  - kind: Deployment
    jsonPointers:
      - /metadata/annotations/deployment.kubernetes.io~1revision
```

### Sync Waves

Resources are deployed in order using annotations:

```yaml
# ConfigMap and Secret (Wave 1)
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "1"

# Deployment (Wave 2)
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "2"
```

**Flow**:
1. ConfigMap and Secret created first
2. Wait for them to be ready
3. Then create Deployment
4. Ensures pods have config when they start

---

## Kustomization

The `argocd/kustomization.yaml` file customizes Kubernetes manifests without templates.

### What It Does

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: argocd

resources:
  - application.yaml

commonLabels:
  app.kubernetes.io/managed-by: argocd
  app.kubernetes.io/part-of: workout-api
```

#### 1. **Namespace Injection**

```yaml
namespace: argocd
```

**Effect**:
- Automatically adds `namespace: argocd` to all resources
- You don't need to specify it in `application.yaml`

**Without Kustomize:**
```yaml
# application.yaml
metadata:
  name: workout-api
  namespace: argocd  # ← Manual
```

**With Kustomize:**
```yaml
# application.yaml
metadata:
  name: workout-api
  # namespace added automatically
```

#### 2. **Common Labels**

```yaml
commonLabels:
  app.kubernetes.io/managed-by: argocd
  app.kubernetes.io/part-of: workout-api
```

**Effect**:
- Adds labels to all resources
- Added to both `metadata.labels` and selectors

**Benefits**:
- Easy to query: `kubectl get all -l app.kubernetes.io/part-of=workout-api`
- Monitoring and metrics filtering
- Consistent labeling across all resources

#### 3. **Resources**

```yaml
resources:
  - application.yaml
```

**Effect**:
- Lists which files to include
- Can have multiple files

**Example with multiple apps:**
```yaml
resources:
  - application.yaml
  - app-team-a.yaml
  - app-team-b.yaml
```

### How to Use Kustomize

```bash
# Preview what Kustomize generates
kubectl kustomize argocd/

# Apply with Kustomize
kubectl apply -k argocd/

# Without Kustomize (plain)
kubectl apply -f argocd/application.yaml
```

### Advanced: Environment Overlays

Kustomize shines with multiple environments:

```
argocd/
├── base/
│   ├── kustomization.yaml
│   └── application.yaml
├── overlays/
│   ├── dev/
│   │   └── kustomization.yaml
│   ├── staging/
│   │   └── kustomization.yaml
│   └── production/
│       └── kustomization.yaml
```

**Dev overlay:**
```yaml
# argocd/overlays/dev/kustomization.yaml
resources:
  - ../../base

patches:
  - target:
      kind: Application
    patch: |-
      - op: replace
        path: /spec/source/targetRevision
        value: develop
      - op: replace
        path: /spec/destination/namespace
        value: workout-api-dev
```

**Deploy dev:**
```bash
kubectl apply -k argocd/overlays/dev/
```

---

## Integration Options

### The Problem

GitHub Actions builds images, but ArgoCD doesn't know about them because **the image tag in Git never updates**.

**Current State:**
```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  GitHub Actions │ builds  │   DockerHub     │         │   Kubernetes    │
│                 │────────>│                 │    ?    │                 │
│  Code: abc123   │         │ Image: abc123   │────────>│  Image: abc111  │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                                                 ▲
                                                                 │
                            ┌─────────────────┐                 │
                            │   Git Repo      │  ArgoCD syncs   │
                            │                 │─────────────────┘
                            │ Tag: abc111     │  (old tag!)
                            └─────────────────┘
```

**The Missing Link:** Git needs to be updated with the new image tag so ArgoCD can detect the change.

**Three Solutions:**

| Option | What Updates Git | Complexity | Best For | Status |
|--------|------------------|------------|----------|--------|
| **Option 1: Image Updater** | ArgoCD Image Updater component | Medium | Production, multiple registries | Not implemented |
| **Option 2: GitHub Actions** | GitHub Actions workflow | Low | Simple setups, single registry | ✅ **Implemented** |
| **Option 3: Latest Tag** | Nothing (manual restarts) | Very Low | Development only | Not recommended |

**Recommended: Option 2** - Already implemented in your workflow!

---

### Option 1: ArgoCD Image Updater (Recommended for Production)

**What it does**:
- Watches DockerHub for new image tags
- Automatically updates Git with new tags
- ArgoCD then deploys the update

**Setup**:

1. **Install Image Updater:**
```bash
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj-labs/argocd-image-updater/stable/manifests/install.yaml
```

2. **Add annotations to ArgoCD Application:**
```yaml
# argocd/application.yaml
metadata:
  annotations:
    # Watch this image in DockerHub
    argocd-image-updater.argoproj.io/image-list: workout-api=your-username/workout-api

    # Update strategy: use latest tag
    argocd-image-updater.argoproj.io/workout-api.update-strategy: latest

    # Or use semver for versioned releases
    # argocd-image-updater.argoproj.io/workout-api.update-strategy: semver
    # argocd-image-updater.argoproj.io/workout-api.allow-tags: regexp:^v[0-9]+\.[0-9]+\.[0-9]+$

    # Write changes back to Git
    argocd-image-updater.argoproj.io/write-back-method: git
```

**Flow**:
```
1. GitHub Actions → Pushes workout-api:main-abc123
2. Image Updater → Detects new tag in DockerHub
3. Image Updater → Updates argocd/application.yaml in Git
4. ArgoCD → Detects Git change
5. ArgoCD → Deploys new image
```

**Pros**:
- ✅ Fully automated
- ✅ Decoupled (GitHub doesn't need Git write access)
- ✅ Supports multiple registries
- ✅ Advanced update strategies (semver, regex)

**Cons**:
- ❌ Additional component to install
- ❌ Slightly more complex setup

---

### Option 2: GitHub Actions Updates Helm Values (Recommended)

**What it does**:
- GitHub Actions updates the image tag in `helm/workout-api/values.yaml` after building
- ArgoCD detects the Helm values change and deploys
- Keeps infrastructure config (ArgoCD Application) separate from app config (image tags)

**Why This Approach?**
- ✅ **Clean separation**: ArgoCD manifest stays static, only Helm values change
- ✅ **Standard Helm pattern**: Values files are meant for configuration
- ✅ **Better git history**: Only values.yaml changes, not the Application manifest
- ✅ **Easier to manage**: Can have environment-specific values files (values-dev.yaml, values-prod.yaml)

**Setup**:

The workflow has already been updated in `.github/workflows/docker-build-push.yml`. Here's the key step:

```yaml
- name: Update Helm values with new image tag
  if: github.event_name != 'pull_request' && github.ref == 'refs/heads/release-dev'
  run: |
    # Generate new tag (branch-sha format for traceability)
    NEW_TAG="${GITHUB_REF_NAME}-${GITHUB_SHA::7}"

    echo "Updating Helm values.yaml with new image tag: ${NEW_TAG}"

    # Update the image tag in Helm values file
    sed -i "s|tag: \".*\"|tag: \"${NEW_TAG}\"|g" helm/workout-api/values.yaml

    # Configure git
    git config user.name "GitHub Actions Bot"
    git config user.email "actions@github.com"

    # Commit and push the change
    git add helm/workout-api/values.yaml
    git commit -m "chore(helm): update image tag to ${NEW_TAG}

    Updated by GitHub Actions workflow
    Commit: ${{ github.sha }}
    Workflow: ${{ github.workflow }} #${{ github.run_number }}"

    git push
```

**What Changes in Git**:
```yaml
# helm/workout-api/values.yaml (BEFORE)
image:
  repository: your-username/workout-api
  tag: "release-dev-abc111"

# helm/workout-api/values.yaml (AFTER)
image:
  repository: your-username/workout-api
  tag: "release-dev-abc123"  # ← Updated by GitHub Actions
```

**Flow**:
```
1. Developer → Pushes code to GitHub (release-dev branch)
2. GitHub Actions → Builds image: workout-api:release-dev-abc123
3. GitHub Actions → Pushes to DockerHub
4. GitHub Actions → Updates helm/workout-api/values.yaml
5. GitHub Actions → Commits and pushes to Git
6. ArgoCD → Detects Helm values change (within 3 minutes)
7. ArgoCD → Re-renders Helm chart with new tag
8. ArgoCD → Syncs new image to Kubernetes
```

**Comparison: Why Helm Values Instead of ArgoCD Manifest?**

```yaml
# ❌ OLD APPROACH: Modifying ArgoCD Application manifest
# File: argocd/application.yaml
spec:
  source:
    helm:
      values: |
        image:
          tag: "abc123"  # ← GitHub Actions modifies this
# Problem: Mixes infrastructure config with app config

# ✅ NEW APPROACH: Modifying Helm values
# File: helm/workout-api/values.yaml
image:
  repository: your-username/workout-api
  tag: "abc123"  # ← GitHub Actions modifies this
# Benefit: Clean separation, standard Helm pattern
```

**Git History Comparison:**

```bash
# ❌ Old approach - ArgoCD manifest changes frequently
git log --oneline
abc456 chore(cd): update image tag to release-dev-abc456
abc345 chore(cd): update image tag to release-dev-abc345
abc234 chore(cd): update image tag to release-dev-abc234
abc123 chore(argocd): update ArgoCD config  # Hard to distinguish

# ✅ New approach - Only Helm values change
git log --oneline
abc456 chore(helm): update image tag to release-dev-abc456
abc345 chore(helm): update image tag to release-dev-abc345
abc234 chore(helm): update image tag to release-dev-abc234
abc123 chore(argocd): initial ArgoCD setup  # ArgoCD config stable
```

**Pros**:
- ✅ Simple to understand
- ✅ Full GitOps (everything in Git)
- ✅ Clear audit trail (Git commits)
- ✅ Easy to rollback (revert Git commit)
- ✅ No additional components
- ✅ **Clean separation of concerns**
- ✅ **Standard Helm pattern**
- ✅ **Better git history**

**Cons**:
- ❌ GitHub Actions needs Git write access
- ❌ Creates extra Git commits
- ❌ Workflow is slightly longer

---

### Option 3: Use `latest` Tag (Simplest, Not Recommended)

**What it does**:
- Always use `tag: latest`
- Configure pods to always pull latest image

**Setup**:

```yaml
# argocd/application.yaml
values: |
  image:
    tag: latest
    pullPolicy: Always  # Always pull from registry
```

```yaml
# helm/workout-api/values.yaml
image:
  pullPolicy: Always  # Not IfNotPresent
```

**Force pod restart:**
```bash
kubectl rollout restart deployment/workout-api -n woodez-database
```

Or add timestamp annotation to force restarts:
```yaml
# In deployment.yaml template
spec:
  template:
    metadata:
      annotations:
        rollout-timestamp: {{ now | date "20060102150405" }}
```

**Flow**:
```
1. GitHub Actions → Pushes workout-api:latest
2. ArgoCD → No Git change detected
3. Manual → kubectl rollout restart
4. Kubernetes → Pulls latest image
```

**Pros**:
- ✅ Very simple setup
- ✅ No Git updates needed

**Cons**:
- ❌ Not true GitOps (Git doesn't reflect actual state)
- ❌ Manual intervention required
- ❌ Can't tell what version is deployed from Git
- ❌ Harder to rollback
- ❌ Can cause issues with multiple clusters/environments

---

## Recommended Setup

For the Workout API, **use Option 2: GitHub Actions Updates Helm Values**

### Why This Option?

1. **Clean Architecture**
   - Separates infrastructure config (ArgoCD) from app config (Helm values)
   - ArgoCD Application manifest stays stable
   - Only the Helm values file changes with each deployment

2. **Standard Helm Pattern**
   - Using values.yaml is the standard way to configure Helm charts
   - Easy to understand for anyone familiar with Helm
   - Can extend to environment-specific values files later

3. **Full GitOps**
   - Git is the source of truth
   - Every deployment is a Git commit
   - Complete audit trail

4. **Easy Rollback**
   ```bash
   # Rollback to previous version
   git revert HEAD
   git push
   # ArgoCD automatically deploys previous version
   ```

5. **Works Well with Your Setup**
   - Already using GitHub Actions
   - Already have ArgoCD configured
   - GitHub Actions workflow already updated
   - No additional infrastructure needed

### Implementation Steps

**✅ Step 1: GitHub Actions workflow already updated!**

The workflow in [.github/workflows/docker-build-push.yml](.github/workflows/docker-build-push.yml:73-96) now includes the step to update Helm values.

**Step 2: Set up GitHub Secrets** (for CI/CD):
```bash
# Go to: GitHub Repository → Settings → Secrets and variables → Actions
# Add these secrets:

Name: DOCKERHUB_USERNAME
Value: your-dockerhub-username

Name: DOCKERHUB_PASSWORD
Value: dckr_pat_abc123... (DockerHub access token)
```

**Step 3: Update Helm values** with your DockerHub username:
```yaml
# helm/workout-api/values.yaml
image:
  repository: YOUR-DOCKERHUB-USERNAME/workout-api
  tag: "release-dev-abc123"  # Will be updated by workflow
```

**Step 4: Create Kubernetes Secrets** (for runtime):
```bash
# Generate Django secret key
DJANGO_SECRET=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# Create Kubernetes secrets
kubectl create secret generic workout-api-secrets \
  --from-literal=django-secret-key="${DJANGO_SECRET}" \
  --from-literal=postgres-password='your-postgres-password' \
  --from-literal=mongodb-password='' \
  --namespace=woodez-database
```

**Step 5: Deploy ArgoCD Application**:
```bash
kubectl apply -k argocd/
```

**Step 6: Push code and watch it deploy**:
```bash
# Make a code change
git commit -am "feat: add new feature"
git push origin release-dev

# Watch GitHub Actions
# → Builds image (using GitHub Secrets)
# → Pushes to DockerHub
# → Updates helm/workout-api/values.yaml
# → Pushes to Git

# Watch ArgoCD (within 3 minutes)
argocd app get workout-api --watch

# Or force immediate sync
argocd app sync workout-api

# Pods use Kubernetes Secrets for runtime configuration
```

---

## Complete Flow Diagrams

### Full CI/CD Pipeline with Recommended Setup

```
┌──────────────────────────────────────────────────────────────┐
│  STEP 1: Developer Pushes Code                              │
│                                                              │
│  git commit -m "feat: new endpoint"                         │
│  git push origin main                                       │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 2: GitHub Actions Workflow Triggers                   │
│                                                              │
│  Trigger: Push to main branch                               │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 3: Build Docker Image                                 │
│                                                              │
│  docker build -t workout-api .                              │
│  Tags created:                                               │
│    - latest                                                  │
│    - main                                                    │
│    - main-abc123 (commit SHA)                               │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 4: Push to DockerHub (using GitHub Secrets)          │
│                                                              │
│  Authenticates with:                                         │
│    - secrets.DOCKERHUB_USERNAME                             │
│    - secrets.DOCKERHUB_PASSWORD                             │
│                                                              │
│  docker push your-username/workout-api:latest               │
│  docker push your-username/workout-api:main                 │
│  docker push your-username/workout-api:main-abc123          │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 5: Update Helm Values with New Image Tag              │
│                                                              │
│  sed -i "s|tag: \".*\"|tag: \"main-abc123\"|" \             │
│    helm/workout-api/values.yaml                              │
│  git commit -m "chore(helm): update image tag to main-abc123"│
│  git push                                                    │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 6: ArgoCD Detects Helm Values Change                  │
│                                                              │
│  Polling interval: Every 3 minutes                          │
│  Change detected: helm/workout-api/values.yaml modified     │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 7: ArgoCD Renders Helm Chart                          │
│                                                              │
│  helm template helm/workout-api \                           │
│    --set image.tag=main-abc123                              │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 8: ArgoCD Compares State                              │
│                                                              │
│  Git State:  image.tag = main-abc123                        │
│  Cluster:    image.tag = main-abc111                        │
│  Result:     OutOfSync                                       │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 9: ArgoCD Auto-Syncs (automated.selfHeal: true)       │
│                                                              │
│  kubectl apply -f <rendered-manifests>                      │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 10: Kubernetes Deployment (Sync Wave Order)           │
│                                                              │
│  Wave 1: ConfigMap, Secret created/updated                  │
│  Wave 2: Deployment updated                                 │
│          - Old pods: main-abc111                            │
│          - New pods: main-abc123                            │
│  Rolling update: 2 → 1 → 0 old, 0 → 1 → 2 new             │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 11: Pods Start with Kubernetes Secrets               │
│                                                              │
│  Environment variables injected from Kubernetes Secrets:     │
│    - DJANGO_SECRET_KEY (from workout-api-secrets)           │
│    - POSTGRES_PASSWORD (from workout-api-secrets)           │
│    - MONGODB_PASSWORD (from workout-api-secrets)            │
│                                                              │
│  Application connects to databases using these secrets       │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 12: Health Checks                                     │
│                                                              │
│  Readiness Probe: GET /api/health/ → 200 OK                │
│  Liveness Probe:  GET /api/health/ → 200 OK                │
│  All pods ready: 2/2                                         │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  ✅ DEPLOYMENT COMPLETE                                     │
│                                                              │
│  Application Status: Healthy & Synced                       │
│  Image: your-username/workout-api:main-abc123               │
│  Replicas: 2/2 ready                                         │
│  Namespace: woodez-database                                  │
│  Secrets: Kubernetes Secrets in use                         │
└──────────────────────────────────────────────────────────────┘
```

### Self-Healing Flow

```
┌──────────────────────────────────────────────────────────────┐
│  SCENARIO: Someone Manually Edits Deployment                │
│                                                              │
│  kubectl edit deployment workout-api -n woodez-database     │
│  Change: replicas: 2 → replicas: 5                          │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  Kubernetes Scales Up                                        │
│                                                              │
│  Pods: 2 → 3 → 4 → 5                                        │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  ArgoCD Detects Drift (next poll, ~3 minutes)               │
│                                                              │
│  Git State:     replicas: 2                                 │
│  Cluster State: replicas: 5                                 │
│  Status: OutOfSync                                           │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  ArgoCD Self-Heals (automated.selfHeal: true)                │
│                                                              │
│  Reverts deployment to Git state                            │
│  kubectl apply -f <deployment-from-git>                     │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  Kubernetes Scales Down                                      │
│                                                              │
│  Pods: 5 → 4 → 3 → 2                                        │
│  Terminates 3 pods                                           │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  ✅ CLUSTER MATCHES GIT                                     │
│                                                              │
│  Replicas: 2 (from Git)                                      │
│  Status: Healthy & Synced                                    │
│  Git is source of truth enforced!                           │
└──────────────────────────────────────────────────────────────┘
```

### Rollback Flow

```
┌──────────────────────────────────────────────────────────────┐
│  SCENARIO: New Deployment Has Bugs                          │
│                                                              │
│  Current: main-abc123 (buggy)                               │
│  Previous: main-abc111 (working)                            │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  OPTION 1: Revert Git Commit                                │
│                                                              │
│  git log                                                     │
│  git revert HEAD  # Reverts image tag update                │
│  git push                                                    │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  ArgoCD Detects Revert                                       │
│                                                              │
│  New Git state: tag: main-abc111                            │
│  Triggers automatic sync                                     │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  Kubernetes Rolls Back                                       │
│                                                              │
│  Deployment updated: main-abc123 → main-abc111              │
│  Rolling update to previous version                          │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  ✅ ROLLBACK COMPLETE                                       │
│                                                              │
│  Running: main-abc111 (previous working version)            │
│  Time: ~2-3 minutes (Git poll + deployment)                 │
└──────────────────────────────────────────────────────────────┘

                     OR

┌──────────────────────────────────────────────────────────────┐
│  OPTION 2: ArgoCD Rollback                                  │
│                                                              │
│  argocd app rollback workout-api                            │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  ArgoCD Reverts to Previous Sync                            │
│                                                              │
│  Uses previous manifests from history                        │
│  Immediate rollback (no Git change)                         │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│  ⚠️  WARNING: Cluster now differs from Git!                │
│                                                              │
│  Git: main-abc123 (new)                                     │
│  Cluster: main-abc111 (rolled back)                         │
│  Status: OutOfSync                                           │
│                                                              │
│  Next steps: Update Git to match cluster state              │
└──────────────────────────────────────────────────────────────┘
```

---

## Monitoring and Debugging

### ArgoCD UI

Access the UI:
```bash
# Port-forward
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d

# Open browser
open https://localhost:8080
```

**What you see:**
- Application health (Healthy/Degraded/Progressing)
- Sync status (Synced/OutOfSync)
- Resource tree (visual of all K8s resources)
- Recent sync history
- Logs for each resource

### ArgoCD CLI

```bash
# Get application status
argocd app get workout-api

# View sync status
argocd app sync workout-api --dry-run

# View differences between Git and cluster
argocd app diff workout-api

# Force sync
argocd app sync workout-api

# View logs
argocd app logs workout-api --tail 100 -f

# Rollback
argocd app rollback workout-api
```

### kubectl Commands

```bash
# Check deployment status
kubectl rollout status deployment/workout-api -n woodez-database

# View pods
kubectl get pods -n woodez-database -l app.kubernetes.io/name=workout-api

# View logs
kubectl logs -n woodez-database -l app.kubernetes.io/name=workout-api --tail=100 -f

# Check events
kubectl get events -n woodez-database --sort-by='.lastTimestamp'

# Describe resources
kubectl describe deployment workout-api -n woodez-database
```

---

## Quick Reference

### GitHub Actions Secrets Setup Checklist

**Required Secrets for CI/CD Pipeline**

Before the GitHub Actions workflow can run successfully, you must configure these secrets:

| Secret Name | Required | Description | How to Obtain | Where Used |
|-------------|----------|-------------|---------------|------------|
| `DOCKERHUB_USERNAME` | ✅ **Yes** | Your DockerHub username | Your DockerHub account name | Docker login, image tagging |
| `DOCKERHUB_PASSWORD` | ✅ **Yes** | DockerHub access token (NOT your password) | DockerHub → Account Settings → Security → New Access Token | Docker login |

**Setup Instructions:**

1. **Create DockerHub Access Token** (if you haven't already):
   ```
   1. Go to: https://hub.docker.com/settings/security
   2. Click "New Access Token"
   3. Name: workout-api-github-actions
   4. Permissions: Read, Write, Delete
   5. Click "Generate"
   6. COPY THE TOKEN NOW (you'll only see it once!)
   ```

2. **Add Secrets to GitHub Repository**:
   ```
   1. Go to your GitHub repository
   2. Click: Settings → Secrets and variables → Actions
   3. Click: New repository secret

   First Secret:
   - Name: DOCKERHUB_USERNAME
   - Value: your-dockerhub-username (e.g., "johndoe")
   - Click: Add secret

   Second Secret:
   - Name: DOCKERHUB_PASSWORD
   - Value: dckr_pat_abc123xyz... (the token you copied)
   - Click: Add secret
   ```

3. **Verify Setup**:
   ```bash
   # After adding secrets, push a commit to trigger the workflow
   git commit --allow-empty -m "test: trigger workflow"
   git push origin release-dev

   # Check workflow run
   # GitHub → Actions tab → Watch the workflow
   # Should see successful Docker build and push
   ```

**Troubleshooting:**

| Error | Cause | Solution |
|-------|-------|----------|
| `Error: Username and password required` | Secrets not configured | Add both DOCKERHUB_USERNAME and DOCKERHUB_PASSWORD |
| `Error: denied: requested access to the resource is denied` | Wrong username or invalid token | Verify username is correct, regenerate token |
| `Error: unauthorized: incorrect username or password` | Using password instead of token | Use access token, not your DockerHub password |
| Workflow doesn't trigger | Wrong branch | Workflow triggers on `release-dev` branch only |

**Security Notes:**
- ✅ Use access tokens, NOT your DockerHub password
- ✅ Tokens can be revoked without changing your password
- ✅ Set token expiration if desired
- ✅ Use minimum required permissions (Read, Write, Delete for images)
- ❌ Never commit secrets to Git
- ❌ Never share secrets via email/chat

**Current Workflow Configuration:**

The workflow in [.github/workflows/docker-build-push.yml](.github/workflows/docker-build-push.yml) uses these secrets:

```yaml
# Lines 30-34: Docker login
- name: Log in to DockerHub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}  # ← Required
    password: ${{ secrets.DOCKERHUB_PASSWORD }}  # ← Required

# Line 40: Image naming
images: ${{ secrets.DOCKERHUB_USERNAME }}/${{ env.DOCKER_IMAGE_NAME }}
```

---

### Key Files

| File | Purpose |
|------|---------|
| `.github/workflows/docker-build-push.yml` | Build and push Docker images |
| `helm/workout-api/` | Kubernetes resource definitions |
| `argocd/application.yaml` | ArgoCD deployment configuration |
| `argocd/kustomization.yaml` | Manifest customization |

### Key Commands

| Task | Command |
|------|---------|
| Deploy ArgoCD App | `kubectl apply -k argocd/` |
| Sync manually | `argocd app sync workout-api` |
| View status | `argocd app get workout-api` |
| View diff | `argocd app diff workout-api` |
| Rollback | `git revert HEAD && git push` |
| Force rollback | `argocd app rollback workout-api` |

### Sync Policy Options

| Setting | Effect |
|---------|--------|
| `automated.prune: true` | Delete resources removed from Git |
| `automated.selfHeal: true` | Revert manual changes |
| `syncOptions.CreateNamespace` | Auto-create namespace |
| `retry.limit: 5` | Retry failed syncs 5 times |
| `ignoreDifferences` | Ignore certain field changes |

---

## Summary

**Complete CI/CD Flow:**

1. **Developer** pushes code to GitHub
2. **GitHub Actions** builds Docker image and pushes to DockerHub
3. **GitHub Actions** updates image tag in `helm/workout-api/values.yaml`
4. **ArgoCD** detects Helm values change and re-renders chart
5. **ArgoCD** syncs to Kubernetes cluster
6. **Kubernetes** performs rolling update
7. **Application** deployed with new version!

**Key Benefits:**

- ✅ Fully automated deployments
- ✅ Git is source of truth
- ✅ Clean separation of concerns (infrastructure vs app config)
- ✅ Standard Helm pattern (values.yaml for configuration)
- ✅ Easy rollbacks (revert Git commit)
- ✅ Self-healing cluster
- ✅ Complete audit trail
- ✅ No manual kubectl needed

**Architecture Benefits:**

Using Helm values instead of inline ArgoCD values provides:
- Better git history (only values.yaml changes, not Application manifest)
- Easier to extend with environment-specific values files
- Clearer separation between ArgoCD config and application config
- Standard practice that's familiar to Helm users

**Next Steps:**

1. ✅ GitHub Actions workflow already updated to modify Helm values
2. **Set up GitHub Secrets**: Add DOCKERHUB_USERNAME and DOCKERHUB_PASSWORD
3. **Update Helm values**: Replace DockerHub username in `helm/workout-api/values.yaml`
4. **Create Kubernetes Secrets**: Create workout-api-secrets before deploying
5. **Deploy ArgoCD Application**: `kubectl apply -k argocd/`
6. **Push code**: Watch automatic deployment with full secrets management!

**Secrets Quick Reference:**

```bash
# GitHub Secrets (one-time setup)
GitHub Repo → Settings → Secrets and variables → Actions
- DOCKERHUB_USERNAME
- DOCKERHUB_PASSWORD

# Kubernetes Secrets (per cluster/environment)
kubectl create secret generic workout-api-secrets \
  --from-literal=django-secret-key='...' \
  --from-literal=postgres-password='...' \
  -n woodez-database
```

---

**Happy GitOps! 🚀**
