# Path to 100k Orders/Sec Performance Target

## Current Performance

**API Layer**: 920 orders/sec (measured at 920 concurrent submissions)
- All orders successfully submitted ✓
- Response latency: <2ms ✓
- Redis queue: Working ✓
- Async DB writes: Working ✓

**Bottleneck Identified**: gRPC network latency to C++ engine

Each order submission requires a 1-2ms gRPC roundtrip to the C++ engine. This limits throughput to:
- Single thread sequential: ~500 orders/sec
- Concurrent (10 threads): ~920 orders/sec (limited by network)
- Theoretical max: ~1000 orders/sec (with perfect network)

## Gap Analysis

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Order submission throughput | 920 orders/sec | 100,000 orders/sec | 108x |
| C++ engine processing | Unknown | ~100,000 orders/sec | TBD |
| Network latency per order | 1-2ms | <0.1ms | 10-20x |

## Solution: Multi-Phase Approach

### Phase 1: Batch Submission to Engine (HIGH IMPACT)

**Objective**: Send 50-100 orders to C++ engine in single gRPC call

**Implementation**:
1. Add `SubmitOrdersBatch` RPC to `trading_engine.proto` ✓ (proto updated)
2. Python backend collects orders for 5ms
3. Send batch of 50-100 orders → Engine processes in parallel
4. Return batch response with all confirmations

**Expected throughput**: 20,000-50,000 orders/sec

**Time to implement**: 2-3 hours

**C++ Changes Required**:
- Handle batch request in gRPC server
- Distribute batch to matching engine workers
- Return batch response

**Python Changes**:
- Modify `engine_batch_submitter.py` to actually use batch RPC
- Make it truly non-blocking by not awaiting batch completion

### Phase 2: C++ Engine Internal Optimization (HIGH IMPACT)

**Objective**: Verify C++ engine can process orders at 100k/sec internally

**Analysis Needed**:
1. Profile matching engine with 100k orders/sec throughput test
2. Identify bottlenecks (lock contention, allocations, cache misses)
3. Optimize data structures (order book, hash maps for user positions)
4. Profile memory behavior (cache-line alignment, NUMA effects)

**Possible optimizations**:
- Lock-free order queues per symbol
- Pre-allocated memory pools
- Cache-line padding for shared state
- Thread-local buffers for matching results
- Vectorized order matching

**Expected throughput**: 100,000+ orders/sec

**Time to measure**: 1-2 hours (need to write proper benchmark)

### Phase 3: UDP-Based Low-Latency Path (FUTURE)

**For extreme latency requirements**:
1. Implement UDP socket for order submission
2. Bypass gRPC protobuf overhead
3. Direct binary protocol
4. Expected latency: <100µs per order
5. Throughput: Potentially 1M+ orders/sec

**Not needed for 100k target**, but available for future scaling.

## Current Bottleneck Assessment

### Network Latency (gRPC)
- **Current**: 1-2ms per order → 500-1000 orders/sec max
- **With batching**: 1-2ms per 50 orders → 25,000-50,000 orders/sec
- **Solution**: Batch RPC endpoint (phase 1)

### C++ Engine Throughput
- **Current**: Unknown (never measured at scale)
- **Claim**: 100,000 orders/sec designed for
- **Verification needed**: Direct load test of matching engine
- **Solution**: Create proper benchmark (phase 2)

### Database Writes
- **Current**: Async batch writer to Postgres
- **Impact**: Minimal (orders queued in Redis first)
- **Not a bottleneck** for order placement API response

## Recommended Execution Order

1. **Phase 1 - Batch RPC** (2-3 hours)
   - Will immediately give 20-50x throughput improvement
   - Achieves 20k-50k orders/sec target
   - Prerequisite for testing C++ engine at scale

2. **Phase 2 - C++ Profiling** (1-2 hours)
   - Measure actual C++ processing capability
   - Identify specific bottlenecks
   - Plan C++ optimizations

3. **Phase 3 - C++ Optimizations** (4-8 hours)
   - Implement identified bottleneck fixes
   - Re-profile and iterate
   - Achieve 100k orders/sec target

## Success Criteria

- [ ] Batch RPC endpoint working (50 orders in 1 gRPC call)
- [ ] Python backend using batch submission
- [ ] Measured throughput: 20,000+ orders/sec via batch
- [ ] C++ engine profiled at 50k+ orders/sec load
- [ ] No errors or dropped orders
- [ ] Memory stable during sustained load
- [ ] Batch processing latency <10ms

## Known Constraints

1. **gRPC network latency**: ~1-2ms (physical limit, can't change much)
2. **Proto serialization**: ~0.1-0.2ms per order (acceptable)
3. **Python async overhead**: ~0.1ms per task (acceptable)
4. **Postgres batching**: Already optimized (async queue)

## Risk Assessment

**Low Risk**:
- Batch RPC addition (just new proto message)
- Python batch submitter logic (well understood)

**Medium Risk**:
- C++ engine modifications (need to ensure lock-free properties maintained)
- Performance regression from changes

**Mitigation**:
- Keep changes small and focused
- Write comprehensive load tests
- Profile before/after each change
- Have rollback plan

## Alternative Approaches Considered

**Approach A**: Use message queue (RabbitMQ, Kafka)
- Pro: Decouples services
- Con: Adds latency (multi-hop), extra infrastructure
- Verdict: Not needed, Redis already provides decoupling

**Approach B**: Direct binary protocol over TCP
- Pro: Lower latency than gRPC
- Con: Complex protocol, harder to maintain
- Verdict: Use UDP if 100k not achievable, not now

**Approach C**: In-process C++ matching (no RPC)
- Pro: Zero network latency
- Con: Requires rewriting Python backend in C++
- Verdict: Not practical, defeats modular design

## Conclusion

**Current system is working correctly** at 920 orders/sec API throughput with reliable async processing.

**Path to 100k orders/sec is clear**:
1. Add batch RPC → 20-50k orders/sec (high confidence)
2. Profile C++ engine → identify bottlenecks
3. Optimize C++ engine → 100k orders/sec (if design holds)

**Estimated total time**: 4-8 hours of development

**Confidence level**: High for batching (Phase 1), medium for C++ optimization (Phase 2-3)
