# Phase 2: C++ Engine Performance Profiling & Analysis Plan

## Objective
Determine if the C++ trading engine can actually process 100,000 orders/sec locally, independent of network/Python overhead.

## Problem Statement
- Current Python API: 946 orders/sec through gRPC
- This is network-limited (1-2ms RTT per call)
- Question: **What is the C++ engine's actual throughput capability?**

## Test Strategy

### Test 1: Direct TCP Load Test
**Objective**: Measure engine throughput without Python or gRPC overhead

**Implementation**:
- Create simple C++ test client that directly connects to engine via TCP
- Bypass gRPC protocol (use raw binary)
- Measure orders/sec for 60+ seconds sustained load
- Record: min/max/avg latency, p99 latency

**Expected Output**:
- Baseline: How fast can engine process orders at all?
- If <10k orders/sec: Engine is bottleneck
- If >100k orders/sec: Network was bottleneck
- If >1M orders/sec: Design is performing well

### Test 2: CPU Profiling
**Objective**: Identify where CPU time is spent

**Tools**: `perf` record/report with Linux

**Steps**:
1. Run engine under sustained 10k+ orders/sec
2. Collect CPU profile for 60 seconds
3. Generate flame graph showing:
   - Which functions consume most time
   - Call stack patterns
   - Potential bottlenecks

**Metrics to Analyze**:
- Instructions per cycle (IPC)
- Cache miss rates
- Branch misprediction rate
- Frontend vs backend stalls

### Test 3: Memory Access Patterns
**Objective**: Understand if memory is bottleneck

**Tools**: `cachegrind` (Valgrind) or Linux perf with events

**Measurement**:
- L1/L2/L3 cache miss rates
- Main memory access frequency
- False sharing between threads

## Expected Findings

### Scenario A: Engine is Fast (>100k orders/sec)
- Implication: Network is THE bottleneck
- Solution: Use UDP, raw socket, or co-locate services
- Next action: Low-latency protocol implementation

### Scenario B: Engine is Slow (<10k orders/sec)
- Implication: Matching algorithm or data structures are inefficient
- Solution: Optimize matching engine (better order book, SIMD, etc)
- Next action: Targeted C++ optimizations

### Scenario C: Engine is Medium (10k-100k orders/sec)
- Implication: Both network and C++ contributing
- Solution: Prioritize based on profiling results
- Next action: Hybrid optimization

## Profiling Commands

```bash
# Record CPU profile during load test
perf record -e cycles,branch-misses,cache-misses \
            -e dTLB-load-misses,LLC-misses \
            -F 99 \
            -p $(pidof trading_engine) \
            -- sleep 60

# Generate report
perf report -n --stdio

# Generate flame graph
perf script > out.perf
stackcollapse-perf.pl out.perf > out.folded
flamegraph.pl out.folded > out.svg
```

## Data Points to Collect

### Performance Metrics
- **Throughput**: Orders/sec (max, min, average)
- **Latency**: p50, p95, p99 in microseconds
- **Consistency**: Jitter (variance in latency)
- **Memory**: Peak usage, allocation rate

### CPU Metrics
- **IPC**: Instructions per cycle (>2 = good)
- **Cache misses**: L1, L2, L3, LLC
- **Branch misses**: Percentage of branches mispredicted
- **Stalls**: Frontend and backend stall cycles

### Scaling
- **Single thread**: Max throughput
- **Two threads**: Scalability check
- **Contention**: Lock wait times (if any)

## Success Criteria

- [ ] Test harness created and compiling
- [ ] Sustained 60+ second load test completing
- [ ] Baseline throughput measured
- [ ] CPU profile generated
- [ ] Flame graph shows clear hot paths
- [ ] Bottleneck identified
- [ ] Recommendations documented

## Timeline
- Estimated: 2-3 hours
- Includes: Test development, profiling, analysis, documentation

## Depends On
- C++ engine source code access
- Linux profiling tools (perf)
- Ability to run sustained load on engine

## Risks
- Engine may crash under sustained 100k+ orders/sec
- Profiling overhead may affect results (use non-intrusive tools)
- Test harness development may take longer than estimated

## Mitigation
- Start with low load, scale gradually
- Use `-p` flag for perf to avoid profiling overhead
- Have rollback plan for test harness
