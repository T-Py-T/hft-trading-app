# hft-trading-app/k8s/README.md
# Kubernetes Deployment Guide

## Overview

This directory contains Kubernetes manifests for deploying the HFT trading platform on OrbStack or any Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (1.24+)
- OrbStack with Kubernetes enabled
- `kubectl` configured to access your cluster
- Docker images built and available (or use local images in OrbStack)

## Files

- `namespace.yaml` - HFT trading namespace
- `postgres.yaml` - PostgreSQL StatefulSet with persistent storage
- `redis.yaml` - Redis deployment
- `hft-engine.yaml` - C++ HFT trading engine
- `hft-backend.yaml` - FastAPI backend (4 replicas)
- `nginx-ingress.yaml` - Nginx load balancer

## Deployment Steps

### 1. Build Docker Images

```bash
# From ml-trading-app-cpp
docker build -f Dockerfile.prod -t hft-trading-app-hft-engine:latest .

# From ml-trading-app-py
docker build -f Dockerfile -t hft-trading-app-hft-backend:latest .
```

### 2. Load Images into OrbStack

```bash
# OrbStack automatically loads local Docker images
# Just ensure they're built in your local Docker daemon
docker images | grep hft-trading-app
```

### 3. Deploy to Kubernetes

```bash
# Create namespace and deploy all resources
kubectl apply -f namespace.yaml
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml
kubectl apply -f hft-engine.yaml
kubectl apply -f hft-backend.yaml
kubectl apply -f nginx-ingress.yaml
```

### 4. Verify Deployment

```bash
# Check all resources
kubectl get all -n hft-trading

# Watch pod status
kubectl get pods -n hft-trading -w

# Check service endpoints
kubectl get svc -n hft-trading
```

### 5. Port Forward for Testing

```bash
# Access API via local port
kubectl port-forward -n hft-trading svc/nginx-ingress 8080:8080

# Test health endpoint
curl http://localhost:8080/health
```

## Performance Characteristics

### Kubernetes Advantages over Docker Compose

| Aspect | Docker Compose | Kubernetes |
|--------|---|---|
| Network | Bridge network (single host) | SDN (distributed) |
| Isolation | Process namespaces | Full pod isolation |
| Resource limits | Soft limits | Hard enforced limits |
| Pod anti-affinity | None | Can spread across nodes |
| Service discovery | DNS | Kubernetes DNS + load balancing |
| Storage | Shared | Persistent volumes |

### Expected Performance

With Kubernetes on OrbStack:
- **Backend pods**: 4 replicas distributed across nodes
- **Network**: Proper network isolation reduces contention
- **Storage**: PostgreSQL gets dedicated persistent volume
- **Expected throughput**: 4,000-5,000 orders/sec (better than Docker)

## Scaling

### Increase Backend Replicas

```bash
kubectl scale deployment hft-backend -n hft-trading --replicas=8
```

### Monitor Performance

```bash
# Watch resource usage
kubectl top pods -n hft-trading

# View logs
kubectl logs -n hft-trading deployment/hft-backend -f

# Get metrics
kubectl get metrics -n hft-trading
```

## Cleanup

```bash
kubectl delete namespace hft-trading
```

## Troubleshooting

### Pods not starting

```bash
kubectl describe pod <pod-name> -n hft-trading
kubectl logs <pod-name> -n hft-trading
```

### Service connectivity issues

```bash
# Test DNS
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup hft-backend

# Check endpoints
kubectl get endpoints -n hft-trading
```

### Database connection issues

```bash
# Check postgres service
kubectl get svc postgres -n hft-trading

# Port forward and test
kubectl port-forward -n hft-trading svc/postgres 5432:5432
psql -h localhost -U trading_user -d trading_db
```
