# hft-trading-app/k8s/deploy-clean.sh
# Clean Kubernetes deployment with proper initialization

#!/bin/bash

set -e

NAMESPACE="hft-trading"

echo "=========================================="
echo "HFT Trading Platform - Kubernetes Deploy"
echo "=========================================="
echo ""

# Verify cluster is clean
echo "Checking for existing namespace..."
if kubectl get namespace $NAMESPACE &>/dev/null; then
  echo "ERROR: Namespace $NAMESPACE already exists"
  echo "Run: kubectl delete namespace $NAMESPACE"
  exit 1
fi

echo "✓ Cluster is clean"
echo ""

# Deploy in order
echo "1. Creating namespace..."
kubectl apply -f namespace.yaml
sleep 2

echo "2. Deploying PostgreSQL..."
kubectl apply -f postgres.yaml
echo "   Waiting for StatefulSet..."
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=120s 2>/dev/null || true
sleep 3

echo "3. Deploying Redis..."
kubectl apply -f redis.yaml
echo "   Waiting for deployment..."
kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=60s 2>/dev/null || true
sleep 2

echo "4. Deploying C++ Engine..."
kubectl apply -f hft-engine.yaml
echo "   Waiting for deployment..."
kubectl wait --for=condition=ready pod -l app=hft-engine -n $NAMESPACE --timeout=60s 2>/dev/null || true
sleep 2

echo "5. Deploying Backend APIs (2 replicas)..."
kubectl apply -f hft-backend.yaml
echo "   Waiting for readiness..."
sleep 10

echo "6. Deploying Nginx Load Balancer..."
kubectl apply -f nginx-ingress.yaml
sleep 2

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""

# Show status
echo "Pod Status:"
kubectl get pods -n $NAMESPACE

echo ""
echo "Service Status:"
kubectl get svc -n $NAMESPACE

echo ""
echo "Port Forward Command:"
echo "  kubectl port-forward -n $NAMESPACE svc/nginx-ingress 8080:8080 &"

echo ""
echo "Test Health:"
echo "  curl http://localhost:8080/health"

echo ""
echo "Run Load Test:"
echo "  python3 scripts/distributed_load_test.py"
echo ""
