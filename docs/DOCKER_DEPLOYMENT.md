# HFT Trading Platform - End-to-End Setup & Testing

## Overview

This document describes how to build, deploy, and test the complete HFT Trading Platform consisting of:

1. **C++ HFT Engine** (`ml-trading-app-cpp`) - High-performance order matching and execution
2. **Python Backend** (`ml-trading-app-py`) - API server and gRPC client
3. **Frontend UI** - React/Node.js dashboard
4. **PostgreSQL** - Order and user data persistence

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
│                   :3000 (Browser)                           │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
┌─────────────────────────▼────────────────────────────────────┐
│           Python Backend (FastAPI)                          │
│                :8000 (http://backend)                       │
│  ✓ Order validation                                         │
│  ✓ Risk limit enforcement                                   │
│  ✓ Order state tracking                                     │
│  ✓ Database persistence                                     │
└────────┬──────────────────────┬────────────────────────────────┘
         │ gRPC                 │ SQL
         │ :50051               │ :5432
┌────────▼────────────────┐  ┌──▼──────────────────┐
│  C++ HFT Engine         │  │ PostgreSQL Database │
│ (:50051)                │  │  (trading_db)       │
│ ✓ Order matching        │  │  ✓ Users            │
│ ✓ Order book            │  │  ✓ Orders           │
│ ✓ Price tracking        │  │  ✓ Fills            │
│ ✓ Risk management       │  │  ✓ Positions        │
│ ✓ Performance tracking  │  │                     │
└────────────────────────┘  └─────────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM and 10GB disk space
- Git with workspace configured

### Build All Images

#### Option 1: Build Locally (Recommended for Development)

```bash
cd /Users/taylor/Library/CloudStorage/Dropbox/_GitHub/hft-trading-app
./scripts/build-docker-images.sh local latest
```

This will:
1. Build C++ engine image (`hft-engine:latest`)
2. Build Python backend image (`hft-backend:latest`)
3. Build Frontend image (`hft-frontend:latest`)
4. Run all health checks

#### Option 2: Build and Push to Docker Registry

```bash
./scripts/build-docker-images.sh docker.io/yourusername 1.0.0
```

This will build and push images to Docker Hub as:
- `docker.io/yourusername/hft-engine:1.0.0`
- `docker.io/yourusername/hft-backend:1.0.0`
- `docker.io/yourusername/hft-frontend:1.0.0`

### Start the Full Stack

```bash
cd /Users/taylor/Library/CloudStorage/Dropbox/_GitHub/hft-trading-app
docker-compose up -d
```

Wait for health checks to pass:

```bash
docker-compose ps
```

All services should show `(healthy)` after 30-60 seconds.

### Verify Services

```bash
# Check C++ engine is running
curl http://localhost:50051

# Check Python backend API
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000

# View logs
docker-compose logs -f

# Check individual service logs
docker-compose logs hft-engine
docker-compose logs hft-backend
docker-compose logs hft-frontend
docker-compose logs postgres
```

## End-to-End Testing

### Run Full Test Suite

```bash
cd /Users/taylor/Library/CloudStorage/Dropbox/_GitHub/hft-trading-app

# Install test dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio requests grpcio

# Run E2E tests
pytest tests/test_e2e_real_trading.py -v -s
```

### Test Coverage

#### 1. Market Order Execution
- Places market buy order
- Verifies execution at market price
- Validates fill confirmation

#### 2. Limit Order with Price Validation
- Fetches real stock price from Yahoo Finance
- Places limit order 5% below market
- Verifies order accepted but not filled

#### 3. Order Cancellation
- Places order
- Cancels order
- Verifies status updated to CANCELLED

#### 4. Portfolio Tracking
- Fetches real prices for holdings
- Calculates portfolio value
- Displays position breakdown

#### 5. Risk Limit Enforcement
- Attempts to exceed position limit
- Verifies order is rejected
- Confirms risk validation works

#### 6. gRPC Server Availability
- Connects to C++ engine on :50051
- Verifies service is responding

#### 7. Backend Health Check
- Calls /health endpoint
- Verifies backend is operational

#### 8. Database Connectivity
- Tests database connection
- Verifies persistence working

### Real Stock Price Testing

The test suite includes real market price fetching via Yahoo Finance API:

```python
price = await get_real_stock_price("AAPL")
print(f"Real AAPL price: ${price:.2f}")
```

This validates that our mock prices are realistic against actual market data.

## Production Deployment

### Docker Registry Setup

#### Option 1: Docker Hub

```bash
docker login
./scripts/build-docker-images.sh docker.io/yourusername 1.0.0
```

#### Option 2: Private Registry

```bash
./scripts/build-docker-images.sh my-registry.io:5000 1.0.0
```

#### Option 3: ECR (AWS)

```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

./scripts/build-docker-images.sh <account-id>.dkr.ecr.us-east-1.amazonaws.com 1.0.0
```

### Kubernetes Deployment

See `docs/KUBERNETES_DEPLOYMENT.md` for full K8s manifests and deployment steps.

### Performance Tuning

For production deployments, adjust in `docker-compose.yml`:

```yaml
hft-engine:
  resources:
    limits:
      cpus: '2'
      memory: 1G
    reservations:
      cpus: '2'
      memory: 1G

hft-backend:
  environment:
    - WORKER_THREADS=4
    - MAX_POOL_SIZE=100
```

## Monitoring & Observability

### Logs

All services write to `/var/log/trading/`:

```bash
docker-compose exec hft-engine tail -f /var/log/trading/engine.log
docker-compose exec hft-backend tail -f /var/log/trading/backend.log
```

### Health Checks

Each service exposes health endpoints:

```bash
# C++ Engine (gRPC)
grpcurl -plaintext localhost:50051 trading.pb.TradingEngine/HealthCheck

# Python Backend (HTTP)
curl http://localhost:8000/health

# Database
docker-compose exec postgres pg_isready -U trading_user
```

### Metrics Export

Backend exports Prometheus metrics:

```bash
curl http://localhost:8000/metrics
```

### Performance Monitoring

View latency and throughput metrics:

```bash
curl http://localhost:8000/metrics | grep hft_
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs hft-engine

# Check health
docker-compose ps

# Rebuild container
docker-compose build --no-cache hft-engine
docker-compose up -d hft-engine
```

### gRPC Connection Failed

```bash
# Check if port is open
netstat -an | grep 50051

# Test connectivity
grpcurl -plaintext localhost:50051 list

# Check firewall
sudo ufw allow 50051
```

### Database Connection Error

```bash
# Verify database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
psql -h localhost -U trading_user -d trading_db
```

### High Memory Usage

```bash
# Check container memory
docker-compose stats

# Reduce pool sizes in config.yaml
memory:
  order_pool_size: 50000    # Default: 100000
  fill_pool_size: 250000    # Default: 500000
```

## Cleanup

### Stop All Services

```bash
docker-compose down
```

### Remove All Data

```bash
docker-compose down -v
```

### Remove Images

```bash
docker rmi hft-engine hft-backend hft-frontend
```

## Next Steps

1. **Customize Configuration**: Edit `config.yaml` for your trading parameters
2. **Deploy to Production**: Follow Kubernetes guide for cloud deployment
3. **Enable TLS**: Configure certificates for secure gRPC communication
4. **Setup Monitoring**: Integrate with Prometheus/Grafana for dashboards
5. **Load Testing**: Run stress tests with >100k orders/second

## Support

For issues or questions:

1. Check logs: `docker-compose logs`
2. Run health checks: `docker-compose exec hft-engine grpcurl -plaintext localhost:50051 trading.pb.TradingEngine/HealthCheck`
3. Verify connectivity: `docker-compose ps`
4. Review test results: `pytest -v`

---

**Version**: 1.0.0  
**Last Updated**: December 2024  
**Maintainer**: Taylor (AI Engineering)
