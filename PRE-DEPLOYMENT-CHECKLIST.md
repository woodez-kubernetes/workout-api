# Pre-Deployment Checklist

Complete this checklist before deploying the Workout API to ensure a successful deployment.

---

## ✅ Prerequisites

### 1. Required Tools Installed

Check that you have these tools installed and accessible:

```bash
# Kubernetes CLI
kubectl version --client
# Should show: Client Version: v1.x.x

# ArgoCD CLI (optional but recommended)
argocd version --client
# Should show: argocd: vx.x.x

# Helm (optional, for testing charts locally)
helm version
# Should show: version.BuildInfo{Version:"v3.x.x"

# Git
git --version
# Should show: git version 2.x.x
```

**If any tool is missing:**
```bash
# macOS (using Homebrew)
brew install kubectl argocd helm git

# Linux
# Install kubectl: https://kubernetes.io/docs/tasks/tools/
# Install argocd: https://argo-cd.readthedocs.io/en/stable/cli_installation/
# Install helm: https://helm.sh/docs/intro/install/
```

---

## ✅ GitHub Configuration

### 2. GitHub Secrets Configured

**Navigate to:** GitHub Repository → Settings → Secrets and variables → Actions

**Verify these secrets exist:**

| Secret Name | Required | How to Check | How to Add |
|-------------|----------|--------------|------------|
| `DOCKERHUB_USERNAME` | ✅ **YES** | Listed in Secrets page | Settings → Secrets → New secret |
| `DOCKERHUB_PASSWORD` | ✅ **YES** | Listed in Secrets page | Settings → Secrets → New secret |

**Test GitHub Secrets:**
```bash
# Push a test commit to trigger the workflow
git commit --allow-empty -m "test: verify GitHub Actions secrets"
git push origin release-dev

# Check workflow run
# GitHub → Actions tab → Check for successful run
# If it fails with authentication errors, secrets are not configured correctly
```

**Fix if needed:**
```bash
# 1. Get DockerHub access token:
#    https://hub.docker.com/settings/security → New Access Token
#    Name: workout-api-github-actions
#    Permissions: Read, Write, Delete

# 2. Add to GitHub:
#    Repository → Settings → Secrets and variables → Actions → New secret
#    DOCKERHUB_USERNAME: your-dockerhub-username
#    DOCKERHUB_PASSWORD: dckr_pat_abc123... (the token)
```

---

## ✅ Kubernetes Cluster Access

### 3. Kubernetes Cluster Available

**Verify cluster access:**
```bash
# Check current context
kubectl config current-context
# Should show your cluster name

# Test cluster connectivity
kubectl cluster-info
# Should show: Kubernetes control plane is running at...

# Check you can access the target namespace
kubectl get namespace woodez-database
# Should show: woodez-database or NotFound (will be created automatically)
```

**If cluster not accessible:**
```bash
# List available contexts
kubectl config get-contexts

# Switch to correct context
kubectl config use-context <your-cluster-name>

# If no cluster configured, set up cluster access:
# - AWS EKS: aws eks update-kubeconfig --name <cluster-name>
# - GKE: gcloud container clusters get-credentials <cluster-name>
# - Local: minikube start / kind create cluster
```

---

## ✅ Database Services

### 4. PostgreSQL Service Available

**Verify PostgreSQL is running:**
```bash
# Check if postgres-svc exists
kubectl get svc postgres-svc -n woodez-database
# Should show: postgres-svc   ClusterIP   ...

# If not found, check other namespaces
kubectl get svc --all-namespaces | grep postgres
```

**Get PostgreSQL password:**
```bash
# You'll need this for Kubernetes secrets later
# Check existing PostgreSQL secret or documentation
kubectl get secret -n woodez-database | grep postgres
```

**If PostgreSQL not available:**
- Deploy PostgreSQL first before deploying the Workout API
- Or update `helm/workout-api/values.yaml` with correct service name
- Or update `argocd/application.yaml` with correct config

---

### 5. MongoDB Service Available

**Verify MongoDB is running:**
```bash
# Check if mongodb-headless exists
kubectl get svc mongodb-headless -n woodez-database
# Should show: mongodb-headless   ClusterIP   None ...

# Check MongoDB StatefulSet
kubectl get statefulset -n woodez-database | grep mongodb
# Should show: mongodb-1, mongodb-2 (or similar)
```

**Important MongoDB Configuration:**
```bash
# Based on previous testing, you must connect to PRIMARY:
# Service: mongodb-headless
# Pod: mongodb-1 (PRIMARY, not mongodb-2 which is SECONDARY)
# Authentication: NONE (no password required)
```

**If MongoDB not available:**
- Deploy MongoDB StatefulSet first
- Or update configuration with correct service name

---

## ✅ Kubernetes Secrets

### 6. Create Kubernetes Secrets

**CRITICAL:** Create these secrets BEFORE deploying ArgoCD Application!

```bash
# Generate Django secret key
DJANGO_SECRET=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# Get your PostgreSQL password
POSTGRES_PASSWORD="your-postgres-password"  # Replace with actual password

# Create Kubernetes secret
kubectl create secret generic workout-api-secrets \
  --from-literal=django-secret-key="${DJANGO_SECRET}" \
  --from-literal=postgres-password="${POSTGRES_PASSWORD}" \
  --from-literal=mongodb-password='' \
  --namespace=woodez-database

# Verify secret was created
kubectl get secret workout-api-secrets -n woodez-database
# Should show: workout-api-secrets   Opaque   3      1s
```

**Verify secret contents (optional):**
```bash
# Check secret keys (values will be base64 encoded)
kubectl describe secret workout-api-secrets -n woodez-database
# Should show: django-secret-key, postgres-password, mongodb-password
```

**If secret already exists:**
```bash
# Delete old secret
kubectl delete secret workout-api-secrets -n woodez-database

# Recreate with correct values
# (Run create command above)
```

---

## ✅ Git Repository Configuration

### 7. Update Repository Configuration

**Update DockerHub username in Helm values:**

```bash
# Edit helm/workout-api/values.yaml
# Find line 11 and replace:
# repository: your-dockerhub-username/workout-api
# With your actual DockerHub username

# Example:
sed -i 's|repository: your-dockerhub-username|repository: johndoe|g' helm/workout-api/values.yaml

# Verify change
grep "repository:" helm/workout-api/values.yaml
# Should show: repository: johndoe/workout-api (with your username)
```

**Update GitHub repository URL in ArgoCD Application:**

```bash
# Edit argocd/application.yaml
# Find line 16 and replace:
# repoURL: https://github.com/your-org/workout-api.git
# With your actual GitHub repository URL

# Example:
sed -i 's|your-org|your-github-username|g' argocd/application.yaml

# Verify change
grep "repoURL:" argocd/application.yaml
# Should show: repoURL: https://github.com/your-username/workout-api.git
```

**Commit configuration changes:**
```bash
# Stage changes
git add helm/workout-api/values.yaml argocd/application.yaml

# Commit
git commit -m "chore: update DockerHub and GitHub configuration for deployment"

# Push to repository
git push origin release-dev
```

---

## ✅ ArgoCD Installation

### 8. ArgoCD Installed in Cluster

**Check if ArgoCD is installed:**
```bash
# Check argocd namespace
kubectl get namespace argocd
# Should show: argocd   Active   ...

# Check ArgoCD pods
kubectl get pods -n argocd
# Should show multiple argocd-* pods in Running state
```

**If ArgoCD not installed:**
```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for pods to be ready
kubectl wait --for=condition=Ready pods --all -n argocd --timeout=300s

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
# Save this password!

# Access ArgoCD UI (in a new terminal)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Open in browser: https://localhost:8080
# Username: admin
# Password: (from command above)
```

**ArgoCD CLI Login (optional):**
```bash
# Login via CLI
argocd login localhost:8080

# Username: admin
# Password: (initial password from above)
# Accept self-signed certificate: y
```

---

## ✅ Pre-Deployment Verification

### 9. Build Test

**Test Docker build locally:**
```bash
# Build the image
podman build -t workout-api:test .
# OR
docker build -t workout-api:test .

# Should complete without errors
# Final message: Successfully tagged workout-api:test
```

**If build fails:**
- Check Dockerfile syntax
- Verify requirements.txt is complete
- Check Python version compatibility

---

### 10. Helm Chart Validation

**Validate Helm chart (optional but recommended):**
```bash
# Lint the chart
helm lint helm/workout-api
# Should show: 1 chart(s) linted, 0 chart(s) failed

# Dry-run render
helm template workout-api helm/workout-api \
  --namespace woodez-database \
  --dry-run > /tmp/rendered-manifests.yaml

# Check rendered output
cat /tmp/rendered-manifests.yaml
# Should show valid Kubernetes YAML

# Clean up
rm /tmp/rendered-manifests.yaml
```

---

### 11. ArgoCD Application Syntax Check

**Validate ArgoCD manifests:**
```bash
# Check kustomization builds
kubectl kustomize argocd/ > /tmp/argocd-manifests.yaml

# Verify output
cat /tmp/argocd-manifests.yaml
# Should show ArgoCD Application with all configurations

# Dry-run apply (doesn't actually create)
kubectl apply -k argocd/ --dry-run=client
# Should show: application.argoproj.io/workout-api created (dry run)

# Clean up
rm /tmp/argocd-manifests.yaml
```

---

## ✅ Final Pre-Deployment Checks

### 12. Review Checklist

**Before you deploy, ensure ALL of these are checked:**

- [ ] `kubectl` can access the cluster
- [ ] Cluster has ArgoCD installed
- [ ] PostgreSQL service (`postgres-svc`) is running
- [ ] MongoDB service (`mongodb-headless`) is running
- [ ] Kubernetes secret `workout-api-secrets` created in `woodez-database` namespace
- [ ] GitHub Secrets configured: `DOCKERHUB_USERNAME` and `DOCKERHUB_PASSWORD`
- [ ] DockerHub username updated in `helm/workout-api/values.yaml`
- [ ] GitHub repository URL updated in `argocd/application.yaml`
- [ ] Configuration changes committed and pushed to Git
- [ ] Docker build test completed successfully
- [ ] Helm chart validated (optional but recommended)
- [ ] ArgoCD Application syntax validated

**If all checked ✅, you're ready to deploy!**

---

## 🚀 Deployment Commands

Once all prerequisites are met:

```bash
# 1. Deploy ArgoCD Application
kubectl apply -k argocd/

# 2. Verify ArgoCD Application was created
kubectl get application -n argocd
# Should show: workout-api

# 3. Watch ArgoCD sync the application
argocd app get workout-api --watch
# OR via kubectl:
kubectl get application workout-api -n argocd -w

# 4. Check deployment status
kubectl get pods -n woodez-database
# Should show: workout-api-* pods starting up

# 5. Check service
kubectl get svc -n woodez-database
# Should show: workout-api service

# 6. View application logs
kubectl logs -n woodez-database -l app.kubernetes.io/name=workout-api --tail=50

# 7. Test health endpoint (once pods are Running)
kubectl port-forward -n woodez-database svc/workout-api 8000:8000
# In browser: http://localhost:8000/api/health/
# Should return: {"status":"healthy","service":"workout-api"}
```

---

## 🔄 Continuous Deployment Flow

After initial deployment, the CD pipeline works automatically:

```
1. Push code to release-dev branch
   ↓
2. GitHub Actions builds Docker image
   ↓
3. GitHub Actions updates helm/workout-api/values.yaml
   ↓
4. ArgoCD detects change (within 3 minutes)
   ↓
5. ArgoCD deploys new version to Kubernetes
   ↓
6. Application updated! 🎉
```

**To trigger deployment:**
```bash
# Make any code change
git add .
git commit -m "feat: add new feature"
git push origin release-dev

# Watch automatic deployment
argocd app get workout-api --watch
```

---

## 🆘 Troubleshooting

### Common Issues

**Issue: "Error from server (NotFound): namespaces 'woodez-database' not found"**
```bash
# Solution: Namespace will be created automatically by ArgoCD
# Or create manually:
kubectl create namespace woodez-database
```

**Issue: "Error: secret 'workout-api-secrets' not found"**
```bash
# Solution: Create Kubernetes secrets (step 6)
kubectl create secret generic workout-api-secrets \
  --from-literal=django-secret-key='...' \
  --from-literal=postgres-password='...' \
  --namespace=woodez-database
```

**Issue: "ImagePullBackOff"**
```bash
# Check DockerHub image exists
# Check image name matches: <username>/workout-api:<tag>
kubectl describe pod <pod-name> -n woodez-database
```

**Issue: "CrashLoopBackOff"**
```bash
# Check application logs
kubectl logs -n woodez-database <pod-name>

# Common causes:
# - Database connection failed (check postgres-svc/mongodb-headless)
# - Missing secrets
# - Environment variable misconfiguration
```

**Issue: GitHub Actions workflow fails**
```bash
# Check secrets are configured
# GitHub → Settings → Secrets → Actions
# Verify: DOCKERHUB_USERNAME and DOCKERHUB_PASSWORD exist

# Check workflow logs
# GitHub → Actions → Select failed workflow → View logs
```

**Issue: ArgoCD shows "OutOfSync"**
```bash
# Manually sync
argocd app sync workout-api

# Or via UI: Applications → workout-api → Sync
```

---

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Helm Documentation](https://helm.sh/docs/)
- [CD-EXPLAIN.md](CD-EXPLAIN.md) - Complete CI/CD pipeline guide

---

**Good luck with your deployment! 🚀**
