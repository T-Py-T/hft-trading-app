# HFT Trading Platform

High-performance order matching engine (C++17) + Python FastAPI backend. Processes 2,600+ orders/sec with <5ms latency.

## Quick Start

```bash
# Prerequisites
docker-compose up -d

# Wait for services
sleep 10

# Access
open http://localhost:8000/docs
```

## Architecture

```
Python FastAPI (8000)
  ↓ gRPC
C++ Engine (50051)
  ↓ TCP
PostgreSQL (5432) + Redis (6379)
```

## Components

| Component | Purpose | Tech |
|-----------|---------|------|
| Backend | Order management, portfolio tracking | Python 3.9+, FastAPI |
| Engine | Order matching, risk management | C++17, lock-free |
| Database | User/order/position persistence | PostgreSQL 15 |
| Cache | Order queuing | Redis 7 |

## Performance

| Metric | Value |
|--------|-------|
| API Latency (p99) | 4.3ms |
| Order Throughput | 2,600 ops/sec |
| With 3-way Sharding | 7,800 ops/sec |
| Error Rate | 0% |

See `docs/PERFORMANCE.md` for benchmarks.

## Deployment

### Local
```bash
docker-compose up -d
pytest tests/ -v
```

### Kubernetes
```bash
cd k8s
./deploy.sh dev          # Development
./deploy.sh production   # Production
```

See `k8s/README.md` for details.

## Documentation

| Doc | Purpose | Time |
|-----|---------|------|
| [QUICKSTART.md](docs/QUICKSTART.md) | 5-minute setup | 5m |
| [PERFORMANCE.md](docs/PERFORMANCE.md) | Benchmarks & scaling | 10m |

## Development

### Integration Tests

```bash
pytest tests/ -v --cov=tests
```

### Component Repositories

For C++ Engine or Python Backend development, see:
- **C++ Engine**: `../ml-trading-app-cpp/` repository
- **Python Backend**: `../ml-trading-app-py/` repository

## Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| DATABASE_URL | postgresql://... | Primary DB |
| ENGINE_HOST | localhost | gRPC server |
| ENGINE_PORT | 50051 | gRPC port |
| LOG_LEVEL | INFO | Logging |

## Scaling

**Current:** 2,600 orders/sec (single instance)

**Next:** 7,800 orders/sec (3-way database sharding)

Edit `k8s/overlays/production/kustomization.yaml` to scale.

## Ports & Services

| Service | Port | Protocol |
|---------|------|----------|
| Backend API | 8000 | HTTP |
| C++ Engine | 50051 | gRPC |
| PostgreSQL | 5432 | TCP |
| Redis | 6379 | TCP |

## Troubleshooting

### Services won't start
```bash
docker-compose logs -f
docker-compose down -v && docker-compose up -d
```

### Tests failing
```bash
pytest tests/ -vv -s
```

### Database issues
```bash
docker exec -it hft-postgres psql -U trading_user -d trading_db
```

## Project Structure

```
hft-trading-app/
├── README.md              # This file
├── docker-compose.yml     # Full stack
├── Makefile              # Build automation
├── requirements.txt      # Python deps
├── docs/
│   ├── QUICKSTART.md    # Setup guide
│   └── PERFORMANCE.md   # Benchmarks
├── k8s/                 # Kubernetes
├── tests/               # Integration tests
└── scripts/             # Utilities
```

## Status

---

**Start:** `docker-compose up -d` → `http://localhost:8000/docs`
