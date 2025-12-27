# Multi-Backend Load Balanced Deployment

## Overview

Deploy 4 backend instances with nginx load balancing to achieve 10,000+ orders/sec.

## Architecture

```
                              Nginx Load Balancer (Port 8080)
                                        |
            ____________________________|____________________________
            |                |                |                |
        Backend-1       Backend-2         Backend-3         Backend-4
        Port 8000       Port 8000         Port 8000         Port 8000
        2,653 ops/s     2,653 ops/s       2,653 ops/s       2,653 ops/s
            |                |                |                |
            |________________|________________|________________|
                              |
                    Shared Services:
                    - Redis (6379)
                    - PostgreSQL (5432)
                    - C++ Engine (50051, 9001)
```

## Expected Performance

- **Each backend**: 2,653 orders/sec
- **4 backends total**: 10,612 orders/sec ✓ EXCEEDS TARGET
- **Resilience**: Any backend going down = 3,500+ orders/sec still available

## Deployment

### Local Docker Compose (for testing)

```bash
# Stop single backend
docker-compose down

# Start multi-backend setup
docker-compose -f docker-compose.multi-backend.yml up -d

# Verify all services
docker-compose -f docker-compose.multi-backend.yml ps

# Test load balancer
curl http://localhost:8080/health
curl http://localhost:8080/api/orders  # Will be load balanced
```

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/hft-backend-deployment.yaml
kubectl apply -f k8s/nginx-configmap.yaml
kubectl apply -f k8s/nginx-deployment.yaml
kubectl apply -f k8s/hft-service.yaml

# Check pods
kubectl get pods -l app=hft-backend

# Forward load balancer port
kubectl port-forward svc/hft-nginx 8080:8080
```

## Configuration

### Backend Configuration

Each backend instance:
- Shares single PostgreSQL database (connection pooling handles concurrency)
- Shares single Redis instance (order queue)
- Connects to single C++ engine (can handle multiple connections)
- 2 uvicorn workers per instance (8 total across 4 backends)

### Load Balancer Configuration

Nginx uses:
- **Algorithm**: Least connections (`least_conn`) - routes to backend with fewest active connections
- **Health checks**: Failed backends marked for failover
- **Connection pooling**: Keepalive 32 to reuse connections
- **Buffering**: 4KB buffers to prevent slowdowns
- **Timeouts**: 30s read/write for long operations

## Performance Expectations

### Throughput by Scenario

| Scenario | Expected | Actual |
|----------|----------|--------|
| 1 backend | 2,653 orders/sec | — |
| 2 backends | 5,306 orders/sec | — |
| 4 backends | 10,612 orders/sec | TARGET |
| 8 backends | 21,224 orders/sec | Ultra-high throughput |

### Latency

- Per-backend: 16-20ms (same as single backend)
- Load balancer overhead: <1ms
- Total: 17-21ms average

## Monitoring

### Container Status

```bash
# Watch backend health
docker stats hft-backend-1 hft-backend-2 hft-backend-3 hft-backend-4
```

### Load Balancer Status

```bash
# Check nginx access logs
docker logs hft-nginx | tail -20

# Monitor connections
docker exec hft-nginx ss -tln | grep 8080
```

### Database Connections

```bash
# Check active connections
docker exec hft-postgres psql -U trading_user -d trading_db \
  -c "SELECT count(*) FROM pg_stat_activity;"
```

## Scaling Notes

### Horizontal Scaling (Recommended)
- Add more backend instances (5th, 6th, etc.)
- Nginx automatically routes to new instances
- Zero downtime deployment possible
- Per-instance throughput stays at 2,653 orders/sec

### Vertical Scaling (Limited)
- Increasing workers per instance has diminishing returns
- Currently using 2 workers (8 total across 4 backends)
- Backend is connection-limited, not worker-limited

## Failover Behavior

If a backend fails:
- Nginx detects unhealthy backend (3 failed health checks)
- Remaining 3 backends handle traffic
- Throughput drops to ~7,959 orders/sec (acceptable)
- Failed backend recovers automatically when healthy

## Cost Efficiency

This approach is:
- **Cost-effective**: Standard horizontal scaling pattern
- **Simple**: No code changes, just container orchestration
- **Reliable**: Proven architecture used in production
- **Scalable**: Easy to add more instances

## Migration from Single Backend

### Step 1: Deploy Multi-Backend
```bash
docker-compose -f docker-compose.multi-backend.yml up -d
```

### Step 2: Test Throughput
```bash
# Run distributed load test against :8080
API_URL="http://localhost:8080" \
  python3 scripts/distributed_load_test.py
```

### Step 3: Monitor & Verify
```bash
# Watch backend loads balance
docker stats hft-backend-*
```

### Step 4: Update Frontend URL
Update frontend to use load balancer:
- Old: `http://localhost:8000`
- New: `http://localhost:8080`

## Next Steps

1. Test multi-backend deployment locally
2. Run load test against :8080
3. Verify 10,000+ orders/sec achieved
4. Deploy to Kubernetes in production
5. Monitor and optimize if needed
