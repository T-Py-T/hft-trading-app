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
curl http://localhost:8080/healthz   # outbox stats included in payload
```

## Scale

```bash
# Edit overlays/production/kustomization.yaml
# Change replicas: hft-backend -> count: 8
./deploy.sh production
```

## Image versions

The backend image lives in [ml-trading-app-go](https://github.com/T-Py-T/ml-trading-app-go) and is published to GHCR on every `v*` tag (`ghcr.io/t-py-t/ml-trading-app-go-server`). The base + production overlays both pin to `latest`; pin to a tagged version (e.g. `v0.2.0`) for a real production rollout.

## Cleanup

```bash
kubectl delete namespace hft-trading
```

## Directory Structure

```
k8s/
├── base/                    # Core manifests (postgres + C++ engine + Go backend + nginx)
├── overlays/
│   ├── dev/                # Development config (1 backend replica, debug logging)
│   └── production/         # Production config (4 backend replicas, info logging)
└── deploy.sh              # Deployment script
```
