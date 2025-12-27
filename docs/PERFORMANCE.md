# Performance Benchmarks

## Quick Start

```bash
# Test API performance
python3 tests/performance_benchmark.py

# Test C++ engine specifications
python3 scripts/benchmark-engine.py
```

## Performance Targets

### API/Backend
- Throughput: >10,000 req/sec
- Latency (p99): <10ms
- Error Rate: <0.1%
- Concurrent Connections: >1000

### C++ HFT Engine
- Order Latency (p99): <100 microseconds
- Throughput: >100,000 orders/second
- Memory: ~256MB baseline
- Lock-Free: Yes (no contention)

## Benchmark Tests

### Test 1: Backend Health Check
- **What**: Measures API health endpoint latency
- **Why**: Baseline for API performance
- **Expected**: <1ms p99

### Test 2: Concurrent Health Checks
- **What**: 10 concurrent health check requests
- **Why**: Tests request queuing and parallelism
- **Expected**: >1000 req/sec with <10ms p99

### Test 3: Order Submission Latency
- **What**: End-to-end order submission time
- **Why**: Core trading operation
- **Expected**: <50ms (when implemented)

### Test 4: Sustained Load
- **What**: Continuous requests for 10 seconds
- **Why**: Stability verification
- **Expected**: Stable throughput, no memory leak

### Test 5: C++ Engine Specifications
- **What**: gRPC communication latency
- **Why**: Ultra-low latency requirement for HFT
- **Expected**: <100µs p99 (design target)

## Performance Characteristics

### Lock-Free Design
The C++ engine uses lock-free data structures:
- Memory Pool: O(1) allocation/deallocation
- Order Book: O(log n) price lookup (std::map)
- Atomic Operations: CAS-based synchronization
- Result: No mutexes in hot paths

### Cache Efficiency
- Order/Fill structs: 64-byte aligned (CPU cache line)
- Pre-allocated pools: No heap fragmentation
- NUMA-aware: Pin threads to specific cores
- Result: Optimal CPU cache utilization

### Scalability
- Horizontal: Multiple engines per symbol
- Vertical: CPU pinning, SIMD, LTO
- Concurrent: Thread-safe order matching
- Result: Scales with hardware

## How to Interpret Results

**Throughput**: Orders or requests per second
- Higher is better
- Track across versions for regression detection

**Latency**: Time from request to response
- p50: Median (50th percentile)
- p95: 95% of requests faster than this
- p99: 99% of requests faster than this (most important for HFT)

**Error Rate**: Failed requests / total requests
- Should be <0.1% in production
- Zero errors in ideal conditions

## Baseline Measurements

After first run, results become baseline for:
- Regression testing (catch performance drops)
- Optimization targets (identify bottlenecks)
- Capacity planning (how many users?)

## Running Regular Benchmarks

### Daily Development
```bash
python3 tests/performance_benchmark.py  # Quick check
```

### Before Release
```bash
python3 tests/performance_benchmark.py
python3 scripts/benchmark-engine.py
# Compare against baseline
```

### After Optimization
```bash
# Run before and after
# Calculate improvement percentage
# Document in commit message
```

## Expected Performance by Component

| Component | Metric | Target | Current |
|-----------|--------|--------|---------|
| API Health | Latency p99 | <1ms | Measured |
| API Health | Throughput | >10k req/s | Measured |
| Order Submit | Latency p99 | <50ms | Measured |
| Order Submit | Throughput | >1k orders/s | Measured |
| C++ Engine | Latency p99 | <100µs | Design target |
| C++ Engine | Throughput | >100k orders/s | Design target |

## Next Steps

1. Run benchmarks and capture baseline
2. Document any performance issues
3. Profile hotspots using `perf` or `flamegraph`
4. Optimize based on profiling data
5. Re-benchmark and compare
6. Document improvements in commit messages
