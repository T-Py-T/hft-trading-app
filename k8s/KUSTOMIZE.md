# Kustomize Deployment Guide

## Overview

This repository uses **Kustomize** for Kubernetes deployments with environment-specific overlays.

## Directory Structure

```
k8s/
├── base/                          # Core manifests (shared)
│   ├── kustomization.yaml        # Base kustomization
│   ├── namespace.yaml
│   ├── postgres.yaml
│   ├── postgres-sharded.yaml
│   ├── redis.yaml
│   ├── hft-engine.yaml
│   ├── hft-backend.yaml
│   └── nginx-ingress.yaml
│
└── overlays/
    ├── dev/                       # Development environment
    │   └── kustomization.yaml    # Dev overrides
    │
    └── production/                # Production environment
        └── kustomization.yaml    # Prod overrides
```

## Deployment

### Development Environment

Deploy to development with reduced resources and verbose logging:

```bash
# Build manifests (preview what will be deployed)
kubectl kustomize overlays/dev/

# Deploy to development
kubectl apply -k overlays/dev/

# Verify deployment
kubectl get all -n hft-trading

# Watch rollout
kubectl rollout status deployment/hft-backend -n hft-trading
kubectl rollout status deployment/hft-engine -n hft-trading
```

### Production Environment

Deploy to production with full resources and monitoring:

```bash
# Build manifests (preview what will be deployed)
kubectl kustomize overlays/production/

# Deploy to production
kubectl apply -k overlays/production/

# Verify deployment
kubectl get all -n hft-trading

# Watch rollout
kubectl rollout status deployment/hft-backend -n hft-trading
kubectl rollout status deployment/hft-engine -n hft-trading
```

## What Changes Between Environments

### Replicas

| Component | Dev | Production |
|-----------|-----|------------|
| hft-backend | 1 | 4 |
| postgres | 1 | 1 |
| redis | 1 | 1 |
| hft-engine | 1 | 1 |

### Resource Requests/Limits

**Development (minimal resources):**
- hft-backend: 64Mi/128Mi memory, 100m/250m CPU
- postgres: 256Mi/512Mi memory, 500m/1000m CPU
- hft-engine: 256Mi/512Mi memory, 500m/1000m CPU
- redis: default

**Production (full resources):**
- hft-backend: 256Mi/512Mi memory, 500m/1000m CPU
- postgres: 1Gi/2Gi memory, 2000m/4000m CPU
- hft-engine: 512Mi/1Gi memory, 1000m/2000m CPU
- redis: 512Mi/1Gi memory, 1000m/2000m CPU

### Logging & Debug

| Setting | Dev | Production |
|---------|-----|------------|
| LOG_LEVEL | DEBUG | INFO |
| DEBUG | true | false |
| DATABASE_ECHO | true | false |

### Image Tags

| Environment | Tag |
|------------|-----|
| Development | dev |
| Production | 1.0.0 |

## Common Tasks

### Preview Changes

```bash
# See what development will deploy
kubectl kustomize overlays/dev/ > /tmp/dev-manifests.yaml
cat /tmp/dev-manifests.yaml | less

# See what production will deploy
kubectl kustomize overlays/production/ > /tmp/prod-manifests.yaml
cat /tmp/prod-manifests.yaml | less
```

### Update Image Tags

To update images for a new release:

1. Edit `overlays/production/kustomization.yaml`:
```yaml
images:
  - name: hft-engine
    newTag: "1.1.0"  # Change this
  - name: hft-backend
    newTag: "1.1.0"  # Change this
```

2. Deploy:
```bash
kubectl apply -k overlays/production/
```

### Scale Backend

To scale backend replicas:

1. Edit `overlays/production/kustomization.yaml`:
```yaml
replicas:
  - name: hft-backend
    count: 8  # Increase replicas
```

2. Deploy:
```bash
kubectl apply -k overlays/production/
```

### Add Environment Variables

To add a new configuration:

1. Edit the appropriate overlay's `kustomization.yaml`:
```yaml
configMapGenerator:
  - name: hft-config
    behavior: merge
    literals:
      - NEW_SETTING="value"
```

2. Deploy:
```bash
kubectl apply -k overlays/dev/
# or
kubectl apply -k overlays/production/
```

### Custom Kustomize

For more complex scenarios, create a custom kustomization:

```bash
# Create a new environment
mkdir -p overlays/staging
cat > overlays/staging/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
  - ../../base

commonLabels:
  environment: staging

replicas:
  - name: hft-backend
    count: 2
EOF

# Deploy staging
kubectl apply -k overlays/staging/
```

## Troubleshooting

### Manifests not generating correctly

```bash
# Validate kustomization syntax
kustomize build overlays/dev/

# If error, check for YAML syntax issues
kubectl kustomize overlays/dev/
```

### Image not pulling

```bash
# Check image configuration in overlay
grep -A 5 "images:" overlays/production/kustomization.yaml

# For development, ensure imagePullPolicy: Never
grep imagePullPolicy overlays/dev/kustomization.yaml
```

### ConfigMaps not updating

```bash
# Kustomize generates new ConfigMap names on changes
# Force deployment update:
kubectl delete deployment hft-backend -n hft-trading
kubectl apply -k overlays/production/
```

## Best Practices

1. **Always preview before deploying**
   ```bash
   kubectl kustomize overlays/production/ | head -50
   ```

2. **Tag images with versions**
   - Dev: `dev`
   - Production: Semantic version (1.0.0, 1.1.0, etc.)

3. **Document overlays**
   - Add comments explaining why each patch exists

4. **Test overlays before production**
   - Deploy dev overlay first
   - Verify all services work
   - Then deploy production overlay

5. **Use GitOps workflow**
   - Commit all changes to git
   - Review changes before applying
   - Apply from version-controlled manifests

## References

- [Kustomize Documentation](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/kustomization/)
- [Kustomize Best Practices](https://kubectl.docs.kubernetes.io/guides/introduction/kustomize/)
