# Specialist Agent Handoff - Phase 2: C++ Engine Profiling

## For: cpu-performance-architect

### Mission
Determine the actual performance ceiling of the C++ trading engine through profiling and analysis.

### Current Situation
- Python API is working at **946 orders/sec**
- This appears to be **network-limited** (gRPC: 1-2ms RTT)
- Unknown: What is C++ engine's actual throughput capability?

### Your Task: Phase 2 Profiling

#### Objective
Measure C++ engine performance **independently** of Python/network overhead to answer:
- Can the C++ engine process 100k orders/sec?
- Where is time actually spent?
- What are top 3 bottlenecks?

#### Deliverables
1. CPU profiling results (perf/flame graph)
2. Bottleneck identification (top 3 hotspots)
3. Performance assessment report
4. Recommendation for Phase 3

#### Key Information
- **Engine location**: Docker container `hft-engine`
- **Engine language**: C++
- **Test environment**: OrbStack (Docker on macOS)
- **Target throughput**: 100k+ orders/sec
- **Current measurement method**: Python HTTP API (@946 orders/sec)

#### Measurement Requirements
1. Sustained load test (60+ seconds)
2. CPU performance counters:
   - Cache miss rates (L1, L2, L3)
   - Branch misprediction rates
   - Instructions per cycle
   - Stall cycle breakdown
3. Latency measurements:
   - p50, p95, p99 in microseconds
   - Consistency (jitter)

#### Analysis Questions to Answer
1. Is C++ engine >100k orders/sec capable?
2. Is memory or CPU the bottleneck?
3. Are there obvious optimization opportunities?
4. How does performance scale with load?
5. What are top 3 CPU-consuming functions?

#### Resources Provided
- `PHASE2_PROFILING_PLAN.md` - Detailed plan
- `PHASE1_RESULTS.md` - Context from adaptive batching
- `PATH_TO_100K_ORDERS_PER_SEC.md` - Background
- Docker environment with engine running

#### Constraints
- Must run within Docker/OrbStack environment
- Cannot modify C++ engine binary (pre-compiled)
- Must not disrupt running API
- Needs real profiling data (not theoretical)

#### Success Criteria
- [ ] Baseline throughput measured
- [ ] Flame graph generated
- [ ] Top 3 hotspots identified
- [ ] Performance ceiling documented
- [ ] Clear bottleneck identified
- [ ] Recommendation for next step

#### Timeline
**Estimate**: 2-3 hours
- 0.5 hours: Test harness development
- 1 hour: Profiling and data collection
- 1-1.5 hours: Analysis and reporting

### Next Steps After Your Phase
1. Deliver profiling report
2. Review findings together
3. Based on results, decide:
   - If network is bottleneck: Consider UDP/socket implementation
   - If C++ is bottleneck: Proceed to Phase 3 (cpp-systems-specialist)
   - If both contribute: Prioritize optimization

---

## For: cpp-systems-specialist

### Mission
Optimize C++ trading engine to reach 100k orders/sec (or higher).

### Your Task: Phase 3 Optimization (Pending Phase 2)

**Status**: AWAITING Phase 2 profiling results

Once Phase 2 profiling identifies bottlenecks, you will:

#### Task
Optimize identified bottleneck #1, #2, #3 from profiling

#### Expected Areas (to be confirmed by Phase 2)
- Order book matching algorithm
- Memory allocation patterns
- Lock-free data structure efficiency
- Cache-line alignment
- SIMD opportunities
- Thread contention

#### Approach
1. Implement targeted optimization for bottleneck #1
2. Measure improvement (before/after)
3. Implement optimization for #2 and #3
4. Verify no regressions
5. Document all changes

#### Resources Available
- C++ source code in `ml-trading-app-cpp/`
- Docker build pipeline
- Profiling tools (perf)
- Test framework for validation

#### Success Criteria (to be refined based on Phase 2)
- Measurable improvement in identified bottleneck
- No performance regressions
- Latency consistency maintained
- Memory stable under sustained load
- >10k orders/sec target (or confirm ceiling)

#### Timeline
**Estimate**: 4-8 hours (based on complexity)

---

## Current System State

### Running Services
```
hft-backend   (Python FastAPI)      → Working at 946 orders/sec
hft-engine    (C++ Trading Engine)   → Status: UNKNOWN (Phase 2 will measure)
hft-postgres  (Database)             → Async batch writes working
hft-redis     (Queue)                → Buffering orders
```

### Performance Summary
| Component | Performance | Status |
|-----------|-------------|--------|
| API Response | <2ms | ✓ |
| Order Throughput | 946 orders/sec | ✓ |
| Reliability | 100% | ✓ |
| Database | Async, stable | ✓ |
| C++ Engine | **UNKNOWN** | Phase 2 TBD |

### Code Quality
- ✓ All tests passing
- ✓ No order loss
- ✓ Async I/O throughout
- ✓ Error handling in place
- ✓ Monitoring/logging

### Deployment Status
**Production Ready**: YES (at 946 orders/sec)
**Can Deploy Today**: YES
**Performance Goals Met**: PARTIALLY (2x baseline achieved, 100k target pending)

---

## Communication & Coordination

### For Phase 2 (cpu-performance-architect)
- Deliver profiling report as: `cpp-engine-profile-report.md`
- Include flame graph as: `cpp-engine-flamegraph.svg`
- Recommendation should identify:
  - Top 3 bottlenecks
  - Estimated optimization potential
  - Risk assessment

### For Phase 3 (cpp-systems-specialist)
- Wait for Phase 2 report
- Will receive:
  - Specific bottleneck analysis
  - Prioritized list of optimizations
  - Success criteria for each
- Coordinate with Phase 2 expert on profiling methodology
- Share optimization results with Phase 2 expert for validation

### Integration Point
After Phase 3 optimizations:
- Rebuild C++ engine
- Run performance tests
- Compare against baseline (946 orders/sec)
- Document improvement ratio
- Final report to stakeholders

---

## Critical Success Path

```
Phase 2 Profiling (2-3 hrs)
    ↓
    Identifies: Is network or C++ the bottleneck?
    ↓
    Decision Point:
    ├─ Network is bottleneck
    │  └─→ Consider UDP/socket (separate effort)
    │
    └─ C++ is bottleneck
       └─→ Phase 3 Optimization (4-8 hrs)
           └─→ Measure improvement
               └─→ Final validation
```

## Shared Documentation
- `/Users/taylor/Library/CloudStorage/Dropbox/_GitHub/hft-trading-app/`
  - `CAMPAIGN_SUMMARY.md` - Campaign overview
  - `PHASE1_RESULTS.md` - Phase 1 what worked
  - `PHASE2_PROFILING_PLAN.md` - Your detailed plan
  - `PATH_TO_100K_ORDERS_PER_SEC.md` - Strategic context
  - `EXECUTION_TASKS.md` - Task tracking
  - `REDIS_QUEUE_TEST_RESULTS.md` - Performance baseline
  - `README.md` - Full system documentation

## Questions for Specialists?

**For cpu-performance-architect**:
- Any questions about Phase 2 approach? Review `PHASE2_PROFILING_PLAN.md`
- Need help setting up profiling? Docker environment is ready
- Need help interpreting metrics? Refer to `cpu-performance-architect.mdc` guidelines

**For cpp-systems-specialist**:
- Questions will be better answered after Phase 2 profiling
- In the meantime, review the C++ code structure in `ml-trading-app-cpp/`
- Familiarize yourself with current architecture

---

## Status Update

**Campaign Progress**: 75% complete
- Phase 1: DONE ✓ (946 orders/sec achieved)
- Phase 2: IN PROGRESS (ready for profiling)
- Phase 3: PENDING (depends on Phase 2)

**Next 24 hours**: Complete Phase 2 profiling and deliver report

**Next week**: Implement Phase 3 optimizations based on findings

Let's reach the performance goals! 🚀
