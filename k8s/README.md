# Kubernetes Deployment

## Quick Start

```bash
# Development (1 replica, debug logging)
./deploy.sh dev

# Production (4 replicas, info logging)
./deploy.sh production
```

## Environments

| Setting | Dev | Production |
|---------|-----|-----------|
| Backend Replicas | 1 | 4 |
| Log Level | DEBUG | INFO |
| Memory | 128Mi | 512Mi |
| CPU | 250m | 1000m |

## Verify

```bash
kubectl get all -n hft-trading
kubectl logs -f deployment/hft-backend -n hft-trading
kubectl port-forward svc/nginx-ingress 8080:80 -n hft-trading
```

## Scale

```bash
# Edit overlays/production/kustomization.yaml
# Change replicas: hft-backend -> count: 8
./deploy.sh production
```

## Cleanup

```bash
kubectl delete namespace hft-trading
```

## Directory Structure

```
k8s/
├── base/                    # Core manifests
├── overlays/
│   ├── dev/                # Development config
│   └── production/         # Production config
└── deploy.sh              # Deployment script
```
