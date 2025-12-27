# Distributed Load Testing with OrbStack Kubernetes

## Prerequisites

1. OrbStack is running with Kubernetes support
2. HFT Trading Platform is deployed in Kubernetes (or use docker-compose as backend)
3. kubectl is configured to access OrbStack cluster

## Quick Start

### Option 1: Run with Docker Compose Backend + Local Python Clients

```bash
# Start the backend (if not already running)
cd hft-trading-app
docker-compose up -d

# Run multiple clients locally
for i in {1..20}; do
  CLIENT_ID=$i API_URL="http://localhost:8000" DURATION_SEC=60 \
    python scripts/distributed_load_test.py &
done

# Wait for all to complete
wait

# Aggregate results (redirect all output to script)
for i in {1..20}; do
  wait $!
done 2>&1 | python scripts/aggregate_load_test.py
```

### Option 2: Deploy to OrbStack Kubernetes (Full Distributed)

```bash
# 1. Create namespace
kubectl create namespace hft-testing

# 2. Copy scripts to ConfigMap
kubectl create configmap load-test-scripts \
  --from-file=scripts/distributed_load_test.py \
  -n hft-testing

# 3. Apply load test job (10 parallel clients)
kubectl apply -f k8s/load-test-job.yaml -n hft-testing

# 4. Monitor job
kubectl get pods -n hft-testing
kubectl logs -f job/hft-load-test -n hft-testing

# 5. Collect results
kubectl logs -l batch.kubernetes.io/job-name=hft-load-test -n hft-testing | \
  python scripts/aggregate_load_test.py
```

## Expected Results

With 20 distributed clients:
- **Projected**: 20 × 549 = 10,980 orders/sec
- **Actual**: Will validate in this test

The test will show:
1. Per-client throughput
2. Total aggregated throughput
3. Latency statistics
4. Success rates

## Validation Criteria

| Throughput | Status |
|-----------|--------|
| ≥ 10,000 orders/sec | TARGET ACHIEVED |
| 5,000 - 9,999 | EXCELLENT |
| 2,000 - 4,999 | GOOD |
| 1,074 - 1,999 | IMPROVEMENT |
| < 1,074 | INVESTIGATION NEEDED |

## What This Tests

✓ Multi-client concurrent load
✓ Fire-and-forget pattern scaling
✓ Batch submission under load
✓ Redis queue capacity
✓ Network throughput
✓ Backend stability
✓ Real distributed scenario

## Troubleshooting

If results are lower than expected:
1. Check backend logs for errors
2. Monitor CPU/memory usage
3. Check Redis queue size
4. Verify batch worker is active
5. Check for timeout/rejection rates
