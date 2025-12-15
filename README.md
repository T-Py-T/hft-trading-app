# HFT Trading Platform

The complete high-frequency trading platform featuring a high-performance C++ order matching engine and Python FastAPI backend with real-time market data, portfolio management, and TUI.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.9+ (for running tests locally)
- C++ compiler (for building engine from source)

### Run the Full Stack

```bash
# 1. Start all services (PostgreSQL, C++ engine, Python backend)
docker-compose up -d

# 2. Wait for services to be healthy
sleep 10

# 3. Setup test database (if running integration tests)
bash scripts/setup_test_db.sh

# 4. Access the application
# - Python Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - gRPC Engine: localhost:50051

# 5. Run integration tests
python -m pytest tests/ -v

# 6. Shutdown
docker-compose down
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│         Python FastAPI Backend (8000)           │
│                                                 │
│  - Order Management     - Portfolio Tracking    │
│  - Authentication       - Market Data Handling  │
│  - REST/gRPC APIs       - Real-time Updates    │
└──────────────────┬──────────────────────────────┘
                   │ (gRPC)
                   ▼
┌─────────────────────────────────────────────────┐
│   C++ High-Performance Order Engine (50051)    │
│                                                 │
│  - Lock-free Order Book  - Price Caching      │
│  - Sub-microsecond Matching - Risk Management │
│  - Concurrent Order Processing                │
│  - Order Logging & Snapshots                  │
└─────────────────────────────────────────────────┘
                   │ (TCP)
                   ▼
┌─────────────────────────────────────────────────┐
│      PostgreSQL Database (5432)                │
│                                                 │
│  - User & Account Data   - Order History      │
│  - Portfolio State        - Risk Limits       │
└─────────────────────────────────────────────────┘
```

## Components

### C++ Order Engine (`ml-trading-app-cpp`)
- **Language**: C++17
- **Build**: CMake + Conan
- **Performance**: Lock-free data structures, CPU affinity, cache optimization
- **Features**: Order matching, price validation, risk management, logging
- **Tests**: 68 tests, 100% passing
- **gRPC API**: Defined in `proto/trading_engine.proto`

### Python Backend (`ml-trading-app-py`)
- **Framework**: FastAPI
- **Database**: SQLAlchemy ORM with PostgreSQL
- **Features**: Order management, portfolio tracking, market data, authentication
- **Tests**: 99 tests, 100% passing
- **API Documentation**: Swagger UI at `/docs` when running

### Integration Tests
- **Location**: `tests/`
- **Coverage**: gRPC message validation, end-to-end order flows, performance baselines
- **Database**: PostgreSQL (auto-configured via docker-compose)
- **Tools**: pytest, pytest-asyncio, httpx, grpcio

## Development Workflow

### Build Individual Components

**C++ Engine:**
```bash
cd ../ml-trading-app-cpp
make setup    # Install dependencies
make build    # Build binary
make test     # Run tests
```

**Python Backend:**
```bash
cd ../ml-trading-app-py
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest backend/tests/ -v
```

### Run Integration Tests

```bash
# Start services
docker-compose up -d && sleep 10

# Run all integration tests
pytest tests/ -v --cov=tests

# Run specific test category
pytest tests/test_grpc_integration.py -v
pytest tests/test_e2e_order_flow.py -v
pytest tests/test_performance.py -v
```

### Database Management

```bash
# Initialize test database
bash scripts/setup_test_db.sh

# Connect to PostgreSQL
docker exec -it hft-postgres psql -U trading_user -d trading_db
```

## Configuration

### Environment Variables

**Docker Compose:**
```yaml
# Automatically configured
DATABASE_URL=postgresql+asyncpg://trading_user:trading_password@postgres:5432/trading_db
GRPC_ENGINE_HOST=hft-engine
GRPC_ENGINE_PORT=50051
LOG_LEVEL=info
```

**Engine Configuration:**
- File: `../ml-trading-app-cpp/config.yaml`
- Contains: Server settings, memory limits, symbol definitions, risk limits, matching rules

**Backend Configuration:**
- File: `../ml-trading-app-py/backend/config.py`
- Contains: Database URL, logging, auth settings

## Testing Summary

### C++ Engine
- **Unit Tests**: Order validation, matching logic, memory pooling
- **Integration Tests**: gRPC communication, persistence, snapshots
- **Performance Tests**: Latency tracking, throughput metering
- **Tests**: 68/68 passing (100%)

### Python Backend
- **API Tests**: Order routes, auth, position tracking
- **Database Tests**: Schema validation, transaction handling
- **Integration Tests**: gRPC client communication, end-to-end flows
- **Tests**: 99/99 passing (100%)

### Integration Tests (This Repo)
- **gRPC Tests**: Message serialization, engine responses
- **End-to-End**: Complete order lifecycle (submit → match → fill → report)
- **Performance**: Latency baselines, throughput measurement
- **Load Testing**: Concurrent order stress testing

## Ports & Services

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| Python Backend | 8000 | HTTP/REST | Order API, WebSocket |
| C++ Engine | 50051 | gRPC | Order processing |
| PostgreSQL | 5432 | TCP | Data persistence |

## Project Structure

```
hft-trading-app/
├── README.md                   # This file (main entry point)
├── docker-compose.yml          # Full stack orchestration
├── Makefile                    # Docker & test automation
├── requirements.txt            # Python test dependencies
├── scripts/
│   └── setup_test_db.sh       # PostgreSQL initialization
├── tests/
│   ├── conftest.py            # Pytest fixtures
│   ├── test_grpc_integration.py
│   ├── test_e2e_order_flow.py
│   ├── test_performance.py
│   └── test_load.py
└── docs/
    └── README-INTEGRATION.md   # Detailed integration testing guide
```

## Deployment

### Local Development
```bash
docker-compose up -d
# Application ready at http://localhost:8000
```

### Production Notes
- Use external PostgreSQL database (don't run in container)
- Set resource limits on engine service
- Enable persistent volumes for order logs
- Configure health checks and auto-restart
- Set proper log levels and rotation
- Use secrets management for credentials

## Performance Targets

- **Order Latency**: < 10 microseconds (P99)
- **Throughput**: 100k+ orders/second
- **Order Book Depth**: 100+ levels per side
- **Concurrent Users**: 1000+
- **Risk Processing**: Real-time, <1ms per position

## Documentation

- **Integration Testing**: `docs/README-INTEGRATION.md`
- **C++ Engine**: `../ml-trading-app-cpp/docs/`
- **Python Backend**: `../ml-trading-app-py/docs/`
- **API Reference**: See Swagger UI at `/docs` (running instance)
- **gRPC API**: `../ml-trading-app-cpp/proto/trading_engine.proto`

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs -f hft-engine
docker-compose logs -f hft-backend
docker-compose logs -f hft-postgres

# Clean and restart
docker-compose down -v
docker-compose up -d
```

### Tests failing
```bash
# Ensure database is initialized
bash scripts/setup_test_db.sh

# Check PostgreSQL connection
docker exec -it hft-postgres psql -U trading_user -d trading_db -c "SELECT 1;"

# Run with verbose output
pytest tests/ -vv -s
```

### gRPC connection issues
```bash
# Check if engine is running
docker exec hft-engine ps aux | grep trading_engine

# Check port availability
lsof -i :50051

# View engine logs
docker-compose logs hft-engine
```

## Contributing

When working on this platform:

1. **Code Changes**: Update individual component repos
   - C++: `../ml-trading-app-cpp`
   - Python: `../ml-trading-app-py`

2. **Integration Tests**: Add tests here in `tests/`

3. **Documentation**: Update relevant `docs/` folders

4. **Container Images**: Rebuild using component Dockerfiles

## License

Proprietary - All rights reserved

## Quick Reference

```bash
# Build and test everything
make build && make test

# View logs
docker-compose logs -f

# Connect to database
docker exec -it hft-postgres psql -U trading_user

# Rebuild images
docker-compose build

# Check service health
docker-compose ps

# Full cleanup
docker-compose down -v
rm -rf .conan2/
```
