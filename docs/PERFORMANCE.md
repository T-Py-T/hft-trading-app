# Public Performance Evidence Contract

## Current status

This public repository contains no verified benchmark outcome.

Earlier revisions mixed current-looking latency, throughput, scaling, and
success-rate statements with historical experiments and private component
evidence. The complete raw outputs, exact component revisions, runner
environment, and public source-to-binary chain were not retained here, so those
figures are not independently reproducible from this repository and are not
repeated as current results.

The public repository currently supports inspection of the integration surface
and validation of its manifests. It does not support an anonymous rebuild or
performance audit of the complete platform because the Go API/TUI and C++
engine source repositories are private.

## What the public checks establish

The active test suite can establish that:

- tracked Kubernetes workload manifests satisfy the repository's security and
  resource-bound contracts;
- application image references use the versions expected by the manifest
  tests;
- Compose and Kubernetes configuration require credentials at runtime instead
  of committing values;
- the deployment helper's dry-run path renders locally without contacting or
  mutating a cluster;
- the public documentation and integration configuration pass their configured
  formatting, link, and secret-pattern checks.

These checks do not establish latency, throughput, capacity, scalability,
success rate, durability, or component implementation quality.

## Required artifacts for a future measured claim

A quantified performance outcome may be described as publicly verified only
when the public repository retains all of the following in the same revision:

1. **Claim definition** — metric name, unit, population, percentile or
   aggregation, success criteria, and error definition.
2. **Exact revisions** — this repository commit plus immutable source revisions
   and image digests for every measured component.
3. **Public build path** — Dockerfiles, build commands, dependency locks, and
   any patches required to reproduce the measured binaries.
4. **Environment record** — hardware, operating system, architecture,
   container runtime, database version, kernel settings, and resource limits.
5. **Topology and configuration** — replica count, database layout, networking,
   runtime flags, and sanitized non-secret configuration.
6. **Workload definition** — request mix, input data, warm-up policy, duration,
   concurrency or arrival model, and the exact public load-generator revision.
7. **Executable command** — one documented command or script that runs the
   measurement without relying on an untracked local step.
8. **Raw output** — machine-readable, unedited tool output retained in the
   repository or a durable public artifact tied to the commit.
9. **Derivation** — a public script that converts raw output into every table,
   chart, percentile, and comparison used in the claim.
10. **Run identity** — timestamp, runner identity, exit status, logs, and a
    stable public link to the retained execution record.
11. **Repetition and uncertainty** — repeat count, run-to-run variation, and
    any discarded run with its reason.
12. **Baseline provenance** — the same artifact set for any baseline or
    before/after comparison.

If one item is absent, the number must be labeled as a target, projection, or
historical unverified observation rather than a publicly verified outcome.

## Suggested public artifact layout

Future evidence should be added without overwriting prior runs:

```text
benchmarks/<date>-<scenario>/
├── README.md             # Claim, scope, exact command, and limitations
├── revisions.json        # Repository SHAs and image digests
├── environment.json      # Runner and dependency inventory
├── config/               # Sanitized workload and service configuration
├── raw/                  # Immutable tool outputs
├── derive/               # Scripts that generate summaries
└── summary/              # Generated tables and charts
```

The run README should link every published number to its raw input and
derivation command. Generated summaries must be reproducible from the retained
raw files.

## Review gate for restoring a claim

Before adding a measured result to the root README:

- confirm the complete artifact set is public and reachable without special
  repository access;
- reproduce the summary from the retained raw output in a clean checkout;
- verify that the documented environment and revisions match the run record;
- state limitations and distinguish observed results from targets;
- link the claim directly to the retained artifact directory, not to a private
  component repository;
- run the repository's manifest, formatting, Markdown, link, secret-pattern,
  and diff checks.

## Non-goals of this change

This evidence contract does not:

- run or invent a benchmark;
- validate or publish private component source;
- claim that an image tag proves the corresponding source revision;
- deploy the stack or contact a trading service;
- turn configuration values, capacity settings, or design targets into
  measured outcomes;
- restore any historical headline metric.

Until a future run satisfies this contract, the honest public result remains:
**no verified benchmark outcome is published by this repository.**
