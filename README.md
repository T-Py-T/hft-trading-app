# HFT Trading Platform

Public integration and deployment configuration for a componentized trading
platform.

This repository contains the Docker Compose and Kubernetes orchestration,
runtime configuration contracts, manifest regression tests, and operator
documentation. It does not contain the Go API/TUI or C++ matching-engine
implementations. Those component source repositories are private, so an
anonymous reader can inspect this integration surface but cannot rebuild or
audit the complete application from public source alone.

## Evidence status

- Publicly inspectable here: orchestration, image references, runtime inputs,
  deployment previews, active manifest tests, and documentation.
- Not publicly inspectable here: component implementation, component test
  suites, and the source-to-image build chain.
- No latency, throughput, scaling, or success-rate outcome is claimed as
  publicly verified. See [docs/PERFORMANCE.md](docs/PERFORMANCE.md) for the
  evidence required before a measured claim may be restored.

## Quick Start

### Public repository checks

These checks exercise the material that is present in this repository. They do
not start the trading services or measure performance.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt pre-commit
python -m pytest tests/test_gitroll_manifests.py -v
pre-commit run --config .pre-commit/.pre-commit-config.yaml --all-files
```

### Full-stack operator setup

`docker-compose.yml` builds the Go and C++ services from sibling directories
that are not included in this public repository. The following workflow is for
an operator who already has authorized access to both private component
checkouts:

```text
workspace/
├── hft-trading-app/
├── ml-trading-app-go/   # private component source
└── ml-trading-app-cpp/  # private component source
```

From `hft-trading-app/`, supply runtime credentials and start the composition:

```bash
export POSTGRES_PASSWORD="$(openssl rand -hex 24)"
export JWT_SECRET="$(openssl rand -hex 32)"
export DATABASE_URL="postgres://trading_user:${POSTGRES_PASSWORD}@postgres:5432/trading_db?sslmode=disable"
docker-compose up -d
curl http://localhost:8000/healthz
```

These commands describe the integration contract; they are not an anonymous
source-reproduction path or benchmark procedure.

## Architecture

```text
Public hft-trading-app repository
┌────────────────────────────────────────────────────────────┐
│ Compose and Kubernetes manifests                           │
│ runtime inputs · service wiring · probes · manifest tests  │
└───────────────┬─────────────────┬──────────────────────────┘
                │                 │
        HTTP / WebSocket       gRPC
                │                 │
       ┌────────▼────────┐  ┌─────▼──────────┐
       │ Go API and TUI  │  │ C++ engine     │
       │ private source  │  │ private source │
       └────────┬────────┘  └────────────────┘
                │
       ┌────────▼────────┐
       │ PostgreSQL      │
       │ public image    │
       └─────────────────┘
```

The public manifests document the service boundaries, ports, environment
variables, health probes, resource limits, and image tags. Statements about
component internals belong to the component repositories and are not treated
as independently verified by this integration repository.

## Components

| Component | Public evidence in this repository | Source availability |
|-----------|------------------------------------|---------------------|
| Integration surface | Compose, Kubernetes, tests, and operator docs | Public here |
| Go API and TUI | Service configuration and pinned backend image reference | Private source |
| C++ matching engine | Service configuration and pinned engine tag | Private source |
| PostgreSQL | Runtime configuration using the official PostgreSQL image | Public upstream image |

Private component names are identifiers for the integration boundary, not
links offered as public supporting evidence.

## Performance

This repository currently publishes no verified performance result. Earlier
headline latency, throughput, scaling, and success-rate figures were not
accompanied here by the complete source revisions, environment, commands, raw
output, and derivation artifacts needed for independent review.

The [performance evidence contract](docs/PERFORMANCE.md) records the current
status, non-goals, and the exact artifact set required for any future measured
claim.

## Deployment

### Local Compose

Compose requires the authorized sibling component checkouts described in
[Quick Start](#full-stack-operator-setup). It is not a standalone public build.

```bash
docker-compose up -d
curl http://localhost:8000/healthz
```

The interactive TUI is also supplied by the private Go component and is not
part of this repository.

### Kubernetes

The Kubernetes manifests are public and can be inspected or rendered locally.
A real deployment additionally requires component images, a cluster, and
runtime credentials; none are created by this README.

```bash
cd k8s
DRY_RUN=true ./deploy.sh dev
DRY_RUN=true ./deploy.sh production
```

See [k8s/README.md](k8s/README.md) for image and runtime-input contracts. A dry
run renders manifests locally; it does not prove component behavior or a
performance outcome.

## Configuration

The values below are integration settings, not benchmark results.

| Setting | Default | Purpose |
|---------|---------|---------|
| `POSTGRES_PASSWORD` | required | PostgreSQL password; never committed |
| `DATABASE_URL` | required | Primary database connection URL; never committed |
| `ENGINE_ADDR` | `hft-engine:50051` | Engine service endpoint |
| `ENGINE_ENABLED` | `true` | Enables the configured engine client |
| `WRITE_BEHIND` | `true` | Enables the configured write-behind mode |
| `OUTBOX_BUFFER` | `10000` | Configured outbox channel capacity |
| `OUTBOX_BATCH` | `50` | Configured maximum batch size |
| `OUTBOX_FLUSH` | `50ms` | Configured partial-batch interval |
| `OUTBOX_LAG_THRESHOLD` | `5s` | Configured health threshold |
| `JWT_SECRET` | required | Application secret; never committed |
| `LOG_LEVEL` | `info` | Logging level |
| `LOG_FORMAT` | `text` | Logging format |
| `APP_ENV` | `development` | Runtime environment selector |

## Ports and Services

| Service | Port | Protocol |
|---------|------|----------|
| Backend API | 8000 | HTTP and WebSocket |
| C++ engine | 50051 | gRPC |
| PostgreSQL | 5432 | TCP |

## Troubleshooting

### Services will not start

Confirm that both authorized sibling component checkouts exist and that all
required runtime inputs are set, then inspect the composition:

```bash
docker-compose config
docker-compose ps
docker-compose logs
```

### Manifest validation

Run the active public regression suite without starting a service:

```bash
python -m pytest tests/test_gitroll_manifests.py -v
```

## Project Structure

```text
hft-trading-app/
├── README.md              # Public scope and integration contract
├── docker-compose.yml     # PostgreSQL plus private-source component builds
├── Makefile               # Compose orchestration and active test notes
├── docs/
│   ├── QUICKSTART.md      # Repository development workflow
│   └── PERFORMANCE.md     # Public performance evidence contract
├── k8s/                   # Kustomize manifests and dry-run deployment helper
├── tests/                 # Active manifest checks and historical reference
└── scripts/               # Public orchestration and load-generation helpers
```

## Migration notes

`tests/integration_test.py` targets a historical Python FastAPI surface and is
excluded from default pytest discovery by `pytest.ini`. Active public
infrastructure regression checks live in `tests/test_gitroll_manifests.py`.
Component-owned end-to-end tests are outside this public repository and are not
presented here as public evidence.
