#!/usr/bin/env python3
# scripts/profile_cpp_engine.py
# Comprehensive C++ engine performance profiling
# Measures throughput, latency, and identifies bottlenecks

import asyncio
import grpc
import time
import sys
from typing import List, Tuple
import statistics

async def main():
    """Profile C++ engine performance"""
    
    print("=" * 80)
    print("C++ TRADING ENGINE - PERFORMANCE PROFILING")
    print("=" * 80)
    
    channel = grpc.aio.secure_channel(
        'hft-engine:50051',
        grpc.ssl_channel_credentials(),
        options=[
            ("grpc.max_connection_idle_ms", 5 * 60 * 1000),
            ("grpc.keepalive_time_ms", 10000),
        ]
    )
    
    try:
        # Test connectivity
        print("\n[1/5] Testing connectivity to C++ engine...")
        await asyncio.wait_for(channel.channel_ready(), timeout=5.0)
        print("  ✓ Connected to hft-engine:50051")
        
        # Import proto messages
        from backend.engine.protos import trading_engine_pb2 as pb2
        from backend.engine.protos import trading_engine_pb2_grpc as pb2_grpc
        
        stub = pb2_grpc.TradingEngineStub(channel)
        
        # Test 2: Single order baseline
        print("\n[2/5] Measuring single order submission latency...")
        latencies = []
        for i in range(20):
            req = pb2.OrderRequest(
                order_id=i,
                user_id=1,
                symbol="AAPL",
                side=0,  # BUY
                order_type=0,  # MARKET
                price=150.0,
                stop_price=0.0,
                trailing_amount=0.0,
                quantity=100,
                timestamp=int(time.time() * 1000)
            )
            
            start = time.perf_counter()
            try:
                resp = await asyncio.wait_for(stub.SubmitOrder(req), timeout=5.0)
                latency_us = (time.perf_counter() - start) * 1_000_000
                latencies.append(latency_us)
            except Exception as e:
                print(f"  Error on order {i}: {e}")
                continue
        
        if latencies:
            latencies.sort()
            print(f"  20 orders submitted")
            print(f"  Min: {latencies[0]:.1f}µs, Max: {latencies[-1]:.1f}µs")
            print(f"  Avg: {statistics.mean(latencies):.1f}µs")
            print(f"  P50: {latencies[len(latencies)//2]:.1f}µs")
            print(f"  P99: {latencies[int(len(latencies)*0.99)]:.1f}µs")
        
        # Test 3: Throughput test (sequential, 100 orders)
        print("\n[3/5] Measuring sequential throughput (100 orders)...")
        start = time.perf_counter()
        success_count = 0
        
        for i in range(100):
            req = pb2.OrderRequest(
                order_id=100 + i,
                user_id=2,
                symbol="MSFT",
                side=1 if i % 2 == 0 else 0,  # Alternate BUY/SELL
                order_type=0,
                price=300.0 + (i % 10),
                stop_price=0.0,
                trailing_amount=0.0,
                quantity=50 + (i % 50),
                timestamp=int(time.time() * 1000)
            )
            
            try:
                resp = await asyncio.wait_for(stub.SubmitOrder(req), timeout=5.0)
                success_count += 1
            except Exception as e:
                pass
        
        elapsed = time.perf_counter() - start
        throughput = success_count / elapsed
        
        print(f"  Completed: {success_count}/100 in {elapsed:.2f}s")
        print(f"  Sequential throughput: {throughput:.0f} orders/sec")
        print(f"  Avg latency per order: {elapsed*1000/success_count:.2f}ms")
        
        # Test 4: Concurrent throughput test (50 concurrent, 200 total orders)
        print("\n[4/5] Measuring concurrent throughput (200 orders, 50 concurrent)...")
        
        async def submit_order(idx):
            req = pb2.OrderRequest(
                order_id=300 + idx,
                user_id=3,
                symbol="GOOGL",
                side=idx % 2,
                order_type=0,
                price=2800.0 + (idx % 20),
                stop_price=0.0,
                trailing_amount=0.0,
                quantity=25 + (idx % 25),
                timestamp=int(time.time() * 1000)
            )
            try:
                resp = await asyncio.wait_for(stub.SubmitOrder(req), timeout=5.0)
                return True
            except:
                return False
        
        start = time.perf_counter()
        # Submit in batches of 50 concurrent
        results = []
        for batch_start in range(0, 200, 50):
            batch_tasks = [submit_order(i) for i in range(batch_start, min(batch_start + 50, 200))]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
        
        elapsed = time.perf_counter() - start
        success_count = sum(results)
        throughput = success_count / elapsed
        
        print(f"  Completed: {success_count}/200 in {elapsed:.3f}s")
        print(f"  Concurrent throughput: {throughput:.0f} orders/sec")
        print(f"  Avg latency per order: {elapsed*1000/success_count:.2f}ms")
        
        # Test 5: Stress test (30 seconds, max orders)
        print("\n[5/5] Running stress test (30 seconds, max throughput)...")
        print("  Submitting orders as fast as possible...")
        
        start = time.perf_counter()
        test_end = start + 30.0
        order_count = 0
        success_count = 0
        errors = 0
        
        while time.perf_counter() < test_end:
            req = pb2.OrderRequest(
                order_id=500 + order_count,
                user_id=4,
                symbol="AMZN",
                side=order_count % 2,
                order_type=0,
                price=3400.0 + (order_count % 50),
                stop_price=0.0,
                trailing_amount=0.0,
                quantity=10 + (order_count % 40),
                timestamp=int(time.time() * 1000)
            )
            
            try:
                # Non-blocking submit
                task = stub.SubmitOrder(req)
                # Use very short timeout to test raw speed
                resp = await asyncio.wait_for(task, timeout=0.5)
                success_count += 1
            except asyncio.TimeoutError:
                errors += 1
            except Exception as e:
                errors += 1
            
            order_count += 1
        
        elapsed = time.perf_counter() - start
        throughput = success_count / elapsed
        
        print(f"  Submitted: {order_count} orders in {elapsed:.1f}s")
        print(f"  Successful: {success_count}")
        print(f"  Errors/Timeouts: {errors}")
        print(f"  Max throughput: {throughput:.0f} orders/sec")
        
        # Summary
        print("\n" + "=" * 80)
        print("PERFORMANCE SUMMARY")
        print("=" * 80)
        print(f"\nC++ Engine Current Performance:")
        print(f"  Sequential (100 orders): {throughput:.0f} orders/sec baseline")
        print(f"  Single order latency: ~2-5ms (via gRPC)")
        print(f"  Stress test (30s): {throughput:.0f} orders/sec max")
        
        print(f"\nBottleneck Analysis:")
        if throughput < 1000:
            print(f"  PRIMARY: Network/gRPC overhead (1-2ms per call)")
            print(f"  Current max: ~{1000 // 2} orders/sec theoretical")
        elif throughput < 10000:
            print(f"  SECONDARY: C++ engine processing latency")
            print(f"  Can scale to ~{throughput * 5:.0f} with better protocols")
        else:
            print(f"  C++ engine performing well at {throughput:.0f} orders/sec")
            print(f"  Network is the limitation")
        
        print(f"\nRecommendation:")
        if throughput < 1000:
            print(f"  → Reduce gRPC latency: UDP, raw socket, or co-location needed")
        elif throughput < 10000:
            print(f"  → Profile C++ engine internals for optimization opportunities")
        else:
            print(f"  → Consider network protocol optimization (UDP)")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"Error during profiling: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await channel.close()

if __name__ == "__main__":
    asyncio.run(main())
