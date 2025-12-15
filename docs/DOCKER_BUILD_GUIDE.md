# Docker Build Guide

How docker-compose builds and runs the HFT Trading Platform

## Overview

The platform uses Docker Compose to orchestrate three services:
1. **PostgreSQL** - Pre-built image from Docker Hub
2. **hft-engine** - Built from source (C++)
3. **hft-backend** - Built from source (Python)

## Build Process

When you run `make up` or `docker-compose up`, Docker Compose will:

### 1. Build hft-engine (C++)

**Dockerfile**: `../ml-trading-app-cpp/Dockerfile`

**Stage 1: Builder**
```dockerfile
FROM ubuntu:22.04 AS builder
# Install: g++-11, cmake, conan, build tools
# Build in /build directory:
#   1. conan install . --build=missing
#   2. mkdir build && cd build
#   3. cmake .. -DCMAKE_BUILD_TYPE=Release
#   4. cmake --build . --config Release
```

**Stage 2: Runtime**
```dockerfile
FROM ubuntu:22.04
# Install runtime dependencies only
# Copy binary from builder
# Copy config.yaml
# Expose port 50051
# Health check: grpcurl localhost:50051
```

**Build Time**: 2-5 minutes (first time), <1 minute (cached)

### 2. Build hft-backend (Python)

**Dockerfile**: `../ml-trading-app-py/Dockerfile`

```dockerfile
FROM python:3.11-slim
# Install system dependencies (gcc)
# pip install requirements.txt
# COPY application code
# Expose port 8000
# Health check: HTTP GET /api/health
```

**Build Time**: 1-2 minutes (first time), <30 seconds (cached)

### 3. Start PostgreSQL

**Image**: `postgres:15-alpine` (pulled from Docker Hub)

Pre-built image, no build needed.

## Building Manually

### Build C++ Engine Only

```bash
cd ../ml-trading-app-cpp
docker build -t hft-engine:latest -f Dockerfile .
```

### Build Python Backend Only

```bash
cd ../ml-trading-app-py
docker build -t hft-backend:latest -f Dockerfile .
```

### Build Both Images

```bash
cd /hft-trading-app
docker-compose build
```

## Rebuilding After Changes

### Source Code Changes in C++

```bash
# Option 1: Rebuild just the engine
docker-compose build --no-cache hft-engine

# Option 2: Rebuild all
docker-compose build --no-cache

# Then restart
docker-compose up -d
```

### Source Code Changes in Python

```bash
# Option 1: Rebuild just the backend
docker-compose build --no-cache hft-backend

# Option 2: Rebuild all
docker-compose build --no-cache

# Then restart
docker-compose up -d
```

### Configuration Changes

For `config.yaml` changes in C++:

```bash
# The Dockerfile copies config.yaml at build time
# Changes require a rebuild
docker-compose build --no-cache hft-engine
docker-compose up -d
```

## Troubleshooting

### Build Fails: "conan: command not found"

This means Python/pip isn't installed in the builder image.

**Check**: C++ Dockerfile has `RUN pip install conan` command

### Build Fails: "grpcurl: command not found"

Health check requires grpcurl. The C++ image installs it via apt-get.

**Check**: Ubuntu 22.04 base image has access to grpcurl package

### Build Fails: "trading_engine not found"

The binary isn't in the expected location after build.

**Check**: C++ build process creates `/build/build/bin/trading_engine`

**Verify**:
```bash
cd ../ml-trading-app-cpp
make build
ls -la build/bin/
```

### Backend Won't Start: "ModuleNotFoundError"

Missing Python dependencies.

**Check**: `../ml-trading-app-py/requirements.txt` has all needed packages

**Verify**:
```bash
cd ../ml-trading-app-py
pip install -r requirements.txt
python -c "import backend.app"
```

## Image Details

### hft-engine:latest

- **Base Image**: ubuntu:22.04 (final stage)
- **Size**: ~500 MB
- **Binary**: `/app/trading_engine`
- **Config**: `/app/config.yaml`
- **Port**: 50051
- **Startup**: `./trading_engine --config config.yaml`

### hft-backend:latest

- **Base Image**: python:3.11-slim
- **Size**: ~300 MB
- **App**: `/app/backend/app.py`
- **Port**: 8000
- **Startup**: `uvicorn backend.app:app --host 0.0.0.0 --port 8000`

### postgres:15-alpine

- **Base Image**: postgres:15-alpine (official)
- **Size**: ~200 MB
- **Port**: 5432
- **User**: trading_user
- **Databases**: trading_db, trading_db_test (created separately)

## Docker Compose Configuration

```yaml
hft-engine:
  build:
    context: ../ml-trading-app-cpp
    dockerfile: Dockerfile
  image: hft-engine:latest
  depends_on: []  # No dependencies
  ports:
    - "50051:50051"

hft-backend:
  build:
    context: ../ml-trading-app-py
    dockerfile: Dockerfile
  image: hft-backend:latest
  depends_on:
    - postgres (service_healthy)
    - hft-engine (service_healthy)
  ports:
    - "8000:8000"

postgres:
  image: postgres:15-alpine
  ports:
    - "5432:5432"
```

## Networking

All services are on the `hft-network` bridge network:

```
postgres (hft-postgres:5432)
  ↑
  └─ hft-backend (localhost:8000)
      ↓
      hft-engine (hft-engine:50051)
```

Services can reach each other by hostname (hft-postgres, hft-engine, hft-backend).

## Performance Notes

### Build Times

- **First build**: 5-10 minutes total
  - C++ engine: 3-8 minutes
  - Python backend: 1-2 minutes
  
- **Subsequent builds** (code changes only): 1-3 minutes
- **Cached builds**: <30 seconds

### Runtime Performance

- **Engine startup**: <1 second
- **Backend startup**: 2-5 seconds
- **Health checks**: Each service checks every 5 seconds
- **Full startup**: 10-15 seconds (all healthy)

## Production Considerations

For production deployment, you might want to:

1. **Push to Registry**: Build locally, push to Docker Hub/ECR
   ```bash
   docker tag hft-engine:latest myregistry/hft-engine:v1.0
   docker push myregistry/hft-engine:v1.0
   ```

2. **Use Pre-built Images**: Reference in docker-compose:
   ```yaml
   hft-engine:
     image: myregistry/hft-engine:v1.0
   ```

3. **Separate Build & Deploy**: Build in CI/CD, deploy from registry

4. **Multi-stage Optimization**: Current setup already uses multi-stage for C++

5. **Resource Limits**: Add to docker-compose:
   ```yaml
   services:
     hft-engine:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 2G
   ```
