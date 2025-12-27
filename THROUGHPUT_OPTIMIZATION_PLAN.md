# C++ Engine Throughput Analysis & Optimization Plan

## Current State

**Python API Performance**: 920 orders/sec
- All orders are successfully submitted
- Response time: <2ms (async to Redis)
- Limitation: Not due to API - the API is fast enough

**C++ Engine Performance**: UNKNOWN
- Design target: 100,000 orders/sec
- Actual measured: Not yet tested directly

## Bottleneck Analysis

### Bottleneck 1: Network Latency (gRPC)
- Current: ~1-2ms per order submission call
- Impact: Sequential submission = 500-1000 orders/sec max
- **This is why we're at 920 orders/sec, not higher**

### Bottleneck 2: C++ Engine Internal Throughput
- Lock-free queue: O(1) enqueue
- Order book: O(log n) operations
- Matching: O(matches) 
- Unknown actual throughput: Need to test

## Strategy to Reach 100k Orders/Sec

We need to decouple:
1. **Order Reception** (API) - Now fast (920 orders/sec)
2. **Order Queueing** (Redis) - Now fast (<1ms)
3. **Engine Processing** (C++ matching) - Need to test and optimize

### Approach 1: Batch Order Submission to Engine
Instead of:
```
for each order:
    submit_order(order)  # 1-2ms per call
```

Do:
```
submit_orders_batch([100 orders])  # 1-2ms for batch
```

**Expected improvement**: 50-100x

### Approach 2: Direct Engine Benchmarking
Create a C++ test client that:
- Submits orders directly to engine (no Python/gRPC overhead)
- Measures internal throughput
- Identifies C++ bottlenecks

### Approach 3: Order Book Optimization
Profile the C++ matching engine to identify:
- Lock contention points
- Allocation hot paths
- Cache misses
- Memory layout issues

## Implementation Plan

### Phase 1: Add Batch Submission to C++ Engine (PRIORITY)
**File**: `ml-trading-app-cpp/src/engine.cpp` + `protos/trading_engine.proto`

Add new gRPC method:
```protobuf
service TradingEngine {
  rpc SubmitOrder(...) returns (...);
  rpc SubmitOrdersBatch(SubmitOrdersBatchRequest) returns (SubmitOrdersBatchResponse);
}

message SubmitOrdersBatchRequest {
  repeated SubmitOrderRequest orders = 1;
}

message SubmitOrdersBatchResponse {
  repeated SubmitOrderResponse responses = 1;
}
```

Benefits:
- Single gRPC call for 100 orders = ~1.2ms (vs 100ms for sequential)
- Reduces context switching
- Allows engine batch optimization

### Phase 2: Python Backend Integration
Batch orders from Redis queue before sending to engine:
- Instead of submitting immediately: buffer 50-100 orders
- Send as batch every 10ms or when buffer full
- Expected throughput: 20,000+ orders/sec

### Phase 3: C++ Engine Profiling
Profile to find:
- CPU hotspots
- Memory allocation patterns
- Lock contention
- Cache behavior

### Phase 4: C++ Optimizations
Based on profiling:
- Pre-allocate memory pools
- Optimize data structures
- Reduce cache misses
- Lock-free patterns (already used)

## Expected Results

| Phase | Throughput | Improvement |
|-------|-----------|-------------|
| Current | 920 orders/sec | Baseline |
| Phase 1 (Batch API) | 20,000+ | 20x |
| Phase 2 (Batch from Redis) | 50,000+ | 50x |
| Phase 3-4 (C++ Optimization) | 100,000+ | 100x |

## Immediate Action

**Start with Phase 1**: Add batch submission endpoint to C++ engine and Python backend.
This is a quick win that doesn't require profiling or complex optimization.

Expected time: 2-3 hours
Expected improvement: 20x throughput increase
