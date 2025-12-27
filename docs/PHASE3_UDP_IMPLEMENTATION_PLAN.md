# Phase 3: UDP Protocol Implementation Plan

## Objective
Implement UDP-based order submission to bypass gRPC overhead and reach **10k+ orders/sec**.

## Current Situation
- **gRPC latency**: 1-2ms per order (immutable network physics)
- **Current throughput**: 679-907 orders/sec ceiling
- **Root cause**: Protocol overhead (protobuf, TCP handshake, etc.)
- **Solution**: UDP with binary protocol

## Expected Improvement

### Network Latency Reduction
```
gRPC (TCP + Protobuf):  1-2ms per order
UDP (binary):          0.1-0.3ms per order  
Improvement:           5-20x latency reduction
```

### Throughput Projection
```
Current (gRPC):  679-907 orders/sec
With UDP:        3,000-18,000 orders/sec
Target:          10,000+ orders/sec
```

## Implementation Strategy

### Phase 3.1: UDP Protocol Design (1-2 hours)

Define binary protocol for order submission:

```
ORDER_SUBMIT (1 byte command)
  order_id (8 bytes, uint64)
  user_id (8 bytes, uint64)
  symbol (4 bytes, enum)
  side (1 byte, BUY=0/SELL=1)
  order_type (1 byte, MARKET=0/LIMIT=1/STOP=2)
  quantity (8 bytes, double)
  price (8 bytes, double)
  timestamp (8 bytes, uint64)
  ────────────────────────────────────
  Total: 47 bytes per order

RESPONSE (binary):
  order_id (8 bytes)
  status (1 byte)
  filled_qty (8 bytes)
  fill_price (8 bytes)
  ────────────────────
  Total: 25 bytes per response
```

### Phase 3.2: Python UDP Client (2-3 hours)

```python
class UDPOrderClient:
    def __init__(self, engine_host, engine_port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.engine_addr = (engine_host, engine_port)
    
    async def submit_order(self, order_dict) -> dict:
        # Serialize to binary
        data = pack_order_binary(order_dict)
        
        # Send UDP
        self.sock.sendto(data, self.engine_addr)
        
        # Receive response
        response_data, _ = await self.sock.recvfrom(25)
        
        # Parse response
        return parse_response_binary(response_data)
```

**Benefits**:
- No TCP handshake
- No protobuf overhead
- Minimal serialization
- Sub-millisecond latency

### Phase 3.3: C++ UDP Server (2-3 hours)

Implement UDP listener in C++ engine:

```cpp
class UDPServer {
    void run() {
        udp::socket socket(io_service, udp::endpoint(udp::v4(), port));
        
        while (true) {
            char buffer[512];
            udp::endpoint sender_endpoint;
            
            // Receive order
            size_t len = socket.receive_from(
                buffer(buffer), 
                sender_endpoint
            );
            
            // Parse binary order
            Order order = parse_order_binary(buffer, len);
            
            // Process (existing matching engine)
            OrderConfirmation resp = matching_engine.submit_order(order);
            
            // Send binary response
            char response[32];
            serialize_response(response, resp);
            socket.send_to(buffer(response), sender_endpoint);
        }
    }
};
```

### Phase 3.4: Integration (1-2 hours)

Update Python backend:

```python
# In backend/app.py lifespan
from backend.engine.udp_client import UDPOrderClient

async def lifespan(app):
    # Initialize UDP client (instead of gRPC)
    udp_client = UDPOrderClient('hft-engine', 50052)
    app.state.engine_client = udp_client
    
    yield
    
    # Cleanup
    udp_client.close()

# In backend/orders/handler.py
async def submit_order(...):
    # Use UDP instead of gRPC
    response = await app.state.engine_client.submit_order(order_data)
    # Rest same as before
```

### Phase 3.5: Testing & Validation (1-2 hours)

```python
# Test UDP throughput
async def test_udp_performance():
    # Same tests as Phase 2, but measure improvement
    - Sequential 100 orders
    - Concurrent 500 orders
    - Sustained 30-second stress test
    
    Expected: 10x+ improvement
```

## Implementation Timeline

```
Phase 3.1: Protocol Design       1-2 hours
Phase 3.2: Python UDP Client     2-3 hours
Phase 3.3: C++ UDP Server        2-3 hours
Phase 3.4: Integration           1-2 hours
Phase 3.5: Testing               1-2 hours
────────────────────────────────────────
Total:                           8-12 hours

Realistic: 10-14 hours with iteration
```

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| UDP packet loss | Medium | Add retry logic, ACKs for critical orders |
| Firewall issues | Low | UDP port 50052 in docker-compose |
| Message size limits | Low | Keep order <512 bytes |
| Out-of-order delivery | Low | Use sequence numbers |
| C++ implementation | Medium | Use Boost.Asio or libuv |

## Success Criteria

- [ ] UDP protocol designed and documented
- [ ] Python UDP client implemented
- [ ] C++ UDP server implemented
- [ ] Integration complete
- [ ] Sequential throughput: >5000 orders/sec
- [ ] Concurrent throughput: >3000 orders/sec
- [ ] Sustained throughput: >3000 orders/sec
- [ ] Zero order loss
- [ ] <1ms average latency per order

## Performance Targets

| Metric | Current | UDP Target | Improvement |
|--------|---------|-----------|-------------|
| Throughput | 679 orders/sec | 5,000+ | 7-10x |
| Latency | 1.10ms avg | 0.2ms avg | 5-5x |
| P99 latency | 2.78ms | <1ms | 3x |
| Max concurrent | 500 | 1000+ | 2x |

## Fallback Plan

If UDP implementation faces issues:
1. **Co-location fallback** - Use Unix sockets instead (4-6 hours, 2-5x improvement)
2. **gRPC optimization** - Tune gRPC settings (1-2 hours, minimal improvement)
3. **Accept current throughput** - Deploy at 679 orders/sec (0 hours, proven stable)

## Dependencies

- Python 3.11+ (async socket support)
- C++17+ (Boost.Asio recommended)
- Docker port 50052 accessible between containers
- Network MTU >=512 bytes

## Next Steps

1. Design binary protocol (1-2 hours)
2. Implement Python UDP client (2-3 hours)
3. Implement C++ UDP server (2-3 hours)
4. Integrate and test (2-3 hours)
5. Validate performance targets
6. Decide on 100k pursuit (Phase 3b)

## Assignment

**Primary**: cpp-systems-specialist (C++ UDP server)
**Secondary**: Python backend engineer (UDP client + integration)
**Support**: cpu-performance-architect (profiling improvements)

---

**Status**: Ready to implement
**Effort**: 10-14 hours
**Expected ROI**: 7-10x throughput improvement
**Target**: 5,000-10,000 orders/sec
