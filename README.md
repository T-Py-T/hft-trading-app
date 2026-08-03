# HFT Trading Platform

High-performance trading platform: C++17 matching engine, Go API + TUI, Postgres durability.

## Quick Start

```bash
export POSTGRES_PASSWORD="$(openssl rand -hex 24)"
export JWT_SECRET="$(openssl rand -hex 32)"
export DATABASE_URL="postgres://trading_user:${POSTGRES_PASSWORD}@postgres:5432/trading_db?sslmode=disable"
docker-compose up -d
sleep 10
curl http://localhost:8000/healthz
```

## Architecture

```text
              ┌─────────────────┐
              │   Go TUI        │   ./scripts/tui.sh
              │ (Bubble Tea)    │   or `make tui`
              └────────┬────────┘
                       │ HTTP + WebSocket (8000)
              ┌────────▼────────┐
              │  Go Backend     │   in-memory ledger
              │ (chi + pgx)     │   write-behind outbox
              └────┬─────┬──────┘
                   │     │
       gRPC (50051)│     │ async pgx batches
                   │     ▼
        ┌──────────▼──┐  ┌─────────────────┐
        │ C++ Engine  │  │   PostgreSQL    │
        │ (matching)  │  │  (durability)   │
        └─────────────┘  └─────────────────┘
```

**Pattern:** in-memory ledger + write-behind outbox.

- API takes `POST /orders` → engine.Submit (sub-ms gRPC) → in-memory ledger → outbox.enqueue → 201 response
- Background drainer batches up to 50 events / 50 ms into one Postgres transaction with one COMMIT per batch — fsync amortizes to O(1)/batch
- Reads always hit the in-memory ledger, which is hydrated from Postgres at boot
- Graceful shutdown drains the outbox before pgxpool close; `/healthz` reports outbox depth + lag and flips to `degraded` when over half capacity or older than `OUTBOX_LAG_THRESHOLD`

Result: `POST /orders` p99 = **465 µs** against dockerized Postgres (down from p99 = 78 ms with the synchronous-PG path). Full report in [`ml-trading-app-go/docs/perf.md`](https://github.com/T-Py-T/ml-trading-app-go/blob/main/docs/perf.md).

## Components

| Component | Repository | Purpose | Tech |
|-----------|------------|---------|------|
| API + TUI | [`ml-trading-app-go`](https://github.com/T-Py-T/ml-trading-app-go) | Order management, portfolio, terminal client | Go 1.26, chi, pgx, Bubble Tea |
| Engine    | [`ml-trading-app-cpp`](https://github.com/T-Py-T/ml-trading-app-cpp) | Order matching, risk | C++17, gRPC |
| Database  | (this repo)  | Persistence | PostgreSQL 16 |

The historical Python implementation lives in [`ml-trading-app-py`](https://github.com/T-Py-T/ml-trading-app-py) and is preserved for reference; the platform now runs the Go backend.

## Performance

| Metric | Value | Notes |
|--------|-------|-------|
| `POST /orders` p99 | 465 µs | 10 traders, 500 req/s, dockerized Postgres |
| `POST /orders` p95 | 242 µs | same |
| `GET /portfolio` p99 | 258 µs | same |
| `GET /market/quote` p99 | 236 µs | same |
| Order success rate | 100% | 7,500-request runs |

vs the Python PRD budgets: `< 50 ms` order submission → comfortably under by 100×; `< 10 ms` position query → under by 38×.

See [`ml-trading-app-go/docs/perf.md`](https://github.com/T-Py-T/ml-trading-app-go/blob/main/docs/perf.md) for the full methodology.

## Deployment

### Local (docker-compose)

Set the three runtime credentials from [Quick Start](#quick-start), then run:

```bash
docker-compose up -d            # postgres + C++ engine + Go backend
curl http://localhost:8000/healthz
```

The Go TUI is interactive (TTY required) so it isn't part of the long-running compose stack. Run it directly:

```bash
docker run --rm -it \
  -e ML_TRADING_API_BASE=http://host.docker.internal:8000 \
  ghcr.io/t-py-t/ml-trading-app-go-tui:latest
```

…or grab a native binary from [`ml-trading-app-go` releases](https://github.com/T-Py-T/ml-trading-app-go/releases).

### Kubernetes

```bash
cd k8s
./deploy.sh dev          # 1 backend replica
./deploy.sh production   # 4 backend replicas
```

Production images are pinned to auditable versions; the development overlay
expects locally loaded images. See the Kubernetes
[image version guidance](k8s/README.md#image-versions).

## Configuration

| Setting               | Default                                       | Purpose |
|-----------------------|-----------------------------------------------|---------|
| `POSTGRES_PASSWORD`   | required                                      | PostgreSQL password; never committed |
| `DATABASE_URL`        | required                                      | Primary DB connection URL; never committed |
| `ENGINE_ADDR`         | `hft-engine:50051`                            | C++ matching engine gRPC |
| `ENGINE_ENABLED`      | `true`                                        | `false` swaps the in-process mock client |
| `WRITE_BEHIND`        | `true`                                        | `false` reverts to synchronous PG writes |
| `OUTBOX_BUFFER`       | `10000`                                       | Outbox channel capacity |
| `OUTBOX_BATCH`        | `50`                                          | Max events per drainer flush |
| `OUTBOX_FLUSH`        | `50ms`                                        | Max wait before partial-batch flush |
| `OUTBOX_LAG_THRESHOLD`| `5s`                                          | `/healthz` flips degraded above this |
| `JWT_SECRET`          | required                                      | Required secret; never committed |
| `LOG_LEVEL`           | `info`                                        | `debug` / `info` / `warn` / `error` |
| `LOG_FORMAT`          | `text`                                        | `text` or `json` |
| `APP_ENV`             | `development`                                 | `production` enforces JWT-secret guard + refuses `dev@local` registration |

## Ports & Services

| Service     | Port  | Protocol |
|-------------|-------|----------|
| Backend API | 8000  | HTTP + WebSocket |
| C++ Engine  | 50051 | gRPC |
| PostgreSQL  | 5432  | TCP |

## Troubleshooting

### Services won't start

```bash
docker-compose logs -f
docker-compose down -v && docker-compose up -d
```

### Backend healthz reports `degraded`

The outbox is over half capacity or has events older than `OUTBOX_LAG_THRESHOLD`. Inspect:

```bash
curl -s http://localhost:8000/healthz | python3 -m json.tool
```

Look at `outbox.depth`, `outbox.dropped_total`, `outbox.oldest_pending_ms`. A non-zero `dropped_total` means the in-process synchronous fallback is firing and durability is preserved, but the buffer needs to be bigger.

### Database issues

```bash
docker exec -it hft-postgres psql -U trading_user -d trading_db
```

## Project Structure

```text
hft-trading-app/
├── README.md              # This file
├── docker-compose.yml     # Postgres + C++ engine + Go backend
├── Makefile               # Compose orchestration + integration tests
├── docs/
│   ├── QUICKSTART.md      # 5-minute setup
│   └── PERFORMANCE.md     # Benchmarks & scaling
├── k8s/                   # Kustomize manifests
├── tests/                 # Manifest checks + historical integration reference
└── scripts/
```

## Migration notes

`tests/integration_test.py` targets the historical Python FastAPI surface, including
`/api/v1/...` paths and request/response shapes that do not match the current Go
backend. It remains reference-only and is excluded from default pytest discovery by
`pytest.ini`. Active infrastructure regression checks live in
`tests/test_gitroll_manifests.py`. The Go backend's own end-to-end tests live in
[`ml-trading-app-go/internal/server`](https://github.com/T-Py-T/ml-trading-app-go/tree/main/internal/server)
and run on every PR there.
