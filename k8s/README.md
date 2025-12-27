# Kubernetes Deployment

## Quick Start

### Using Kustomize (Recommended)

```bash
# Development environment (1 replica, debug logging)
./deploy.sh dev

# Or with dry-run to preview
DRY_RUN=true ./deploy.sh production

# Production environment (4 replicas, info logging)
./deploy.sh production
```

## Directory Structure

```
k8s/
├── base/                          # Core manifests (shared)
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── postgres.yaml
│   ├── postgres-sharded.yaml
│   ├── redis.yaml
│   ├── hft-engine.yaml
│   ├── hft-backend.yaml
│   └── nginx-ingress.yaml
│
└── overlays/
    ├── dev/                       # Development
    │   └── kustomization.yaml    # 1 replica, debug mode
    │
    └── production/                # Production
        ├── kustomization.yaml    # 4 replicas, full resources
        └── secrets.yaml          # Secrets template
```

## What Changes Between Environments

| Setting | Dev | Production |
|---------|-----|-----------|
| Backend Replicas | 1 | 4 |
| Log Level | DEBUG | INFO |
| Memory Limits | 128Mi | 512Mi |
| CPU Limits | 250m | 1000m |
| Image Tags | dev | 1.0.0 |

## Manual Deployment (Without Kustomize)

If you prefer not to use Kustomize:

```bash
# Create namespace
kubectl apply -f base/namespace.yaml

# Deploy services
kubectl apply -f base/postgres.yaml
kubectl apply -f base/redis.yaml
kubectl apply -f base/hft-engine.yaml
kubectl apply -f base/hft-backend.yaml
kubectl apply -f base/nginx-ingress.yaml
```

## Verify Deployment

```bash
# Check resources
kubectl get all -n hft-trading

# Watch pods
kubectl get pods -n hft-trading -w

# Check logs
kubectl logs -f deployment/hft-backend -n hft-trading

# Port forward for access
kubectl port-forward svc/nginx-ingress 8080:80 -n hft-trading
# Visit: http://localhost:8080
```

## Scaling

### Scale Backend Replicas

```bash
# Using Kustomize overlay
# Edit overlays/production/kustomization.yaml replicas section
# Then redeploy: ./deploy.sh production

# Or direct kubectl
kubectl scale deployment hft-backend --replicas=8 -n hft-trading
```

### Scale Database (3-Way Sharding)

```bash
# Use postgres-sharded.yaml instead of postgres.yaml
# Edit overlays/production/kustomization.yaml to reference postgres-sharded.yaml
# Or deploy separately:
kubectl apply -f base/postgres-sharded.yaml
```

## Cleanup

```bash
# Delete everything
kubectl delete namespace hft-trading

# Or with Kustomize
kubectl delete -k overlays/production/
```

## Troubleshooting

### Pods not starting

```bash
kubectl describe pod <pod-name> -n hft-trading
kubectl logs <pod-name> -n hft-trading
```

### Service not accessible

```bash
kubectl get endpoints -n hft-trading
kubectl describe svc nginx-ingress -n hft-trading
```

### Database connection issues

```bash
kubectl port-forward svc/postgres 5432:5432 -n hft-trading
psql -h localhost -U trading_user -d trading_db
```

## References

- See `deploy.sh` for deployment automation
- See `overlays/` for environment-specific configurations
- See `base/` for core resource definitions
