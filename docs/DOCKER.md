# Docker Deployment

## Quick Start

```bash
cd hft-trading-app
docker-compose up -d
docker-compose ps
```

Services available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- gRPC Engine: localhost:50051
- PostgreSQL: localhost:5432

## Build & Push

```bash
./scripts/build-docker-images.sh docker.io/username 1.0.0
```

Images pushed to:
- docker.io/username/hft-engine:1.0.0
- docker.io/username/hft-backend:1.0.0
- docker.io/username/hft-frontend:1.0.0

## Services

- **PostgreSQL**: Database (postgres:15-alpine)
- **C++ Engine**: gRPC server on :50051
- **Python Backend**: FastAPI on :8000
- **Frontend**: React/Node on :3000

All services have health checks and will restart on failure.

## Configuration

Edit `docker-compose.yml` to:
- Change ports
- Adjust resource limits
- Add environment variables
- Configure volumes

## Logs

```bash
docker-compose logs -f hft-engine
docker-compose logs -f hft-backend
docker-compose logs -f postgres
```

## Stop

```bash
docker-compose down
```

## Troubleshooting

**Container won't start?**
```bash
docker-compose logs <service>
```

**Port already in use?**
```bash
docker-compose down  # Stop all services
# Or change ports in docker-compose.yml
```

**Database connection error?**
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d    # Restart with fresh DB
```
