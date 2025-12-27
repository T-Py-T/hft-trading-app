# hft-trading-app/k8s/deploy.sh
# Quick deployment script

#!/bin/bash

set -e

NAMESPACE="hft-trading"

echo "HFT Trading Platform - Kubernetes Deployment"
echo "=============================================="
echo ""

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "ERROR: kubectl not found. Install Kubernetes CLI first."
    exit 1
fi

# Create namespace
echo "1. Creating namespace..."
kubectl apply -f namespace.yaml
sleep 2

# Deploy infrastructure
echo "2. Deploying PostgreSQL..."
kubectl apply -f postgres.yaml
echo "   Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=120s 2>/dev/null || true
sleep 5

echo "3. Deploying Redis..."
kubectl apply -f redis.yaml
echo "   Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=60s 2>/dev/null || true
sleep 3

echo "4. Deploying C++ Engine..."
kubectl apply -f hft-engine.yaml
echo "   Waiting for Engine to be ready..."
kubectl wait --for=condition=ready pod -l app=hft-engine -n $NAMESPACE --timeout=60s 2>/dev/null || true
sleep 3

echo "5. Deploying Backend (4 replicas)..."
kubectl apply -f hft-backend.yaml
echo "   Waiting for all backends to be ready..."
kubectl wait --for=condition=ready pod -l app=hft-backend -n $NAMESPACE --timeout=120s 2>/dev/null || true

echo "6. Deploying Nginx Load Balancer..."
kubectl apply -f nginx-ingress.yaml

echo ""
echo "=============================================="
echo "Deployment Complete!"
echo "=============================================="
echo ""
echo "Cluster Status:"
kubectl get all -n $NAMESPACE

echo ""
echo "Next steps:"
echo "  1. Port forward: kubectl port-forward -n $NAMESPACE svc/nginx-ingress 8080:8080"
echo "  2. Test health: curl http://localhost:8080/health"
echo "  3. Run load test: python3 scripts/distributed_load_test.py"
echo ""
