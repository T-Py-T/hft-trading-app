#!/usr/bin/env python3
"""
scripts/measure-grpc-latency.py
Measure actual C++ gRPC engine latency with detailed breakdown
"""

import time
import grpc
import statistics
from concurrent.futures import ThreadPoolExecutor
import sys

# Try to import generated protobuf code
try:
    from proto import trading_engine_pb2, trading_engine_pb2_grpc
except ImportError:
    print("Warning: Could not import protobuf stubs")
    print("gRPC measurement will be limited")
    PROTO_AVAILABLE = False
else:
    PROTO_AVAILABLE = True


def measure_grpc_connection_latency():
    """Measure latency of establishing gRPC connection"""
    print("\n[Test 1] gRPC Connection Establishment")
    
    latencies = []
    errors = 0
    
    for i in range(20):
        try:
            start = time.perf_counter()
            channel = grpc.aio.insecure_channel('localhost:50051')
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)
            channel.close()
        except Exception as e:
            errors += 1
    
    if latencies:
        print(f"  Connection Establishment (20 attempts):")
        print(f"  - Avg: {statistics.mean(latencies):.3f}ms")
        print(f"  - p50: {sorted(latencies)[10]:.3f}ms")
        print(f"  - p99: {sorted(latencies)[int(len(latencies)*0.99)]:.3f}ms")
        print(f"  - Errors: {errors}/20")


def measure_grpc_channel_creation():
    """Measure channel creation with reuse"""
    print("\n[Test 2] gRPC Channel Reuse")
    
    try:
        start = time.perf_counter()
        channel = grpc.aio.insecure_channel('localhost:50051')
        creation_time = (time.perf_counter() - start) * 1000
        
        print(f"  Channel creation time: {creation_time:.3f}ms")
        
        # Test with async operations
        print(f"  Channel status: {channel}")
        channel.close()
        
    except Exception as e:
        print(f"  Error: {e}")


def measure_concurrent_connections():
    """Measure concurrent connection handling"""
    print("\n[Test 3] Concurrent Connections (10 workers)")
    
    def worker():
        latencies = []
        for i in range(10):
            try:
                start = time.perf_counter()
                channel = grpc.aio.insecure_channel('localhost:50051')
                elapsed = (time.perf_counter() - start) * 1000
                latencies.append(elapsed)
                channel.close()
            except:
                pass
        return latencies
    
    try:
        start = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker) for _ in range(10)]
            all_latencies = []
            for future in futures:
                all_latencies.extend(future.result())
        
        duration = time.time() - start
        
        if all_latencies:
            print(f"  Total connections: {len(all_latencies)}")
            print(f"  Duration: {duration:.2f}s")
            print(f"  Avg latency: {statistics.mean(all_latencies):.3f}ms")
            print(f"  p99 latency: {sorted(all_latencies)[int(len(all_latencies)*0.99)]:.3f}ms")
    except Exception as e:
        print(f"  Error: {e}")


def measure_rpc_call_latency():
    """Measure actual RPC call latency if protobuf available"""
    if not PROTO_AVAILABLE:
        print("\n[Test 4] RPC Call Latency - SKIPPED")
        print("  (protobuf stubs not available)")
        return
    
    print("\n[Test 4] RPC Call Latency (HealthCheck)")
    
    latencies = []
    errors = 0
    
    try:
        channel = grpc.insecure_channel('localhost:50051')
        stub = trading_engine_pb2_grpc.TradingEngineStub(channel)
        
        for i in range(50):
            try:
                start = time.perf_counter()
                # Call HealthCheck RPC
                request = trading_engine_pb2.HealthCheckRequest()
                response = stub.HealthCheck(request, timeout=1)
                elapsed = (time.perf_counter() - start) * 1000000  # microseconds
                latencies.append(elapsed)
            except Exception as e:
                errors += 1
        
        if latencies:
            print(f"  RPC Call Latency (50 calls):")
            print(f"  - Avg: {statistics.mean(latencies):.1f}µs")
            print(f"  - p50: {sorted(latencies)[25]:.1f}µs")
            print(f"  - p95: {sorted(latencies)[int(len(latencies)*0.95)]:.1f}µs")
            print(f"  - p99: {sorted(latencies)[int(len(latencies)*0.99)]:.1f}µs")
            print(f"  - Errors: {errors}/50")
        
        channel.close()
    except Exception as e:
        print(f"  Error: {e}")


def print_summary():
    """Print interpretation of results"""
    print("\n" + "="*80)
    print("C++ ENGINE gRPC LATENCY ANALYSIS")
    print("="*80)
    print("\nExpected Baselines (OrbStack):")
    print("  - Channel creation: ~0.5-1ms")
    print("  - RPC call roundtrip: 50-200µs (if kernel bypass active)")
    print("  - Concurrent scaling: Linear with workers")
    print("\nTarget for optimization:")
    print("  - RPC latency p99: <100µs")
    print("  - Connection pooling benefit: 30-50% latency reduction")
    print("="*80)


if __name__ == "__main__":
    print("Starting C++ gRPC Latency Measurement...")
    print("Targeting: localhost:50051")
    
    try:
        # Quick check if engine is running
        channel = grpc.aio.insecure_channel('localhost:50051')
        channel.close()
    except Exception as e:
        print(f"\nERROR: Cannot connect to gRPC engine on localhost:50051")
        print("Make sure services are running: docker-compose up -d")
        sys.exit(1)
    
    measure_grpc_connection_latency()
    measure_grpc_channel_creation()
    measure_concurrent_connections()
    measure_rpc_call_latency()
    print_summary()
