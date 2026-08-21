# GitRoll triage for revision `d0ed512`

This ledger records every finding in the seven open `gitroll:` issues created
from revision `d0ed512e1af73c1164fcb3aa33837f26022b1582`. All 22 findings still
applied to the default branch and are corrected by this change; no generated,
vendored, upstream, reference, stale, or unsafe-to-change findings were skipped.

| Issue | File | Findings | Disposition |
| --- | --- | ---: | --- |
| [#2](https://github.com/T-Py-T/trading-platform-orchestration/issues/2) | `docker-compose.yml` | 1 | Removed the embedded database URL/password and made all secrets required runtime inputs. |
| [#3](https://github.com/T-Py-T/trading-platform-orchestration/issues/3) | `k8s/base/hft-backend.yaml` | 3 | Disabled token automounting, added ephemeral-storage bounds, and pinned the published backend release. |
| [#4](https://github.com/T-Py-T/trading-platform-orchestration/issues/4) | `k8s/base/hft-engine.yaml` | 3 | Disabled token automounting, added ephemeral-storage bounds, and pinned the engine source revision. |
| [#5](https://github.com/T-Py-T/trading-platform-orchestration/issues/5) | `k8s/base/nginx-ingress.yaml` | 2 | Disabled token automounting and added ephemeral-storage bounds. |
| [#6](https://github.com/T-Py-T/trading-platform-orchestration/issues/6) | `k8s/base/postgres-sharded.yaml` | 9 | Secured all three optional shard workloads and removed their unreported embedded passwords. |
| [#7](https://github.com/T-Py-T/trading-platform-orchestration/issues/7) | `k8s/base/postgres.yaml` | 3 | Disabled token automounting, added ephemeral-storage bounds, and removed the unreported embedded password. |
| [#8](https://github.com/T-Py-T/trading-platform-orchestration/issues/8) | `k8s/overlays/production/secrets.yaml` | 1 | Removed the unused committed secret template; deployment now creates required Secrets from runtime inputs. |
| **Total** | | **22** | **All findings corrected.** |

Focused regression tests validate the workload security controls, image pins,
runtime-only credential flow, Nginx routing, and liveness behavior. Kustomize
builds for base, development, and production validate the rendered manifests.
