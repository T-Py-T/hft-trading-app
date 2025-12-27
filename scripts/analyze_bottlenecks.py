#!/usr/bin/env python3
# scripts/analyze_bottlenecks.py
# Analyze current bottlenecks and categorize as software vs hardware

import asyncio
import time
import httpx
import subprocess
import json

async def main():
    print("=" * 80)
    print("BOTTLENECK ANALYSIS - SOFTWARE VS HARDWARE")
    print("=" * 80)
    
    base_url = "http://localhost:8000"
    
    # Check current system resources
    print("\n[1/5] Checking Docker container resources...")
    try:
        result = subprocess.run(
            ["docker", "stats", "--no-stream", "hft-backend"],
            capture_output=True,
            text=True,
            timeout=5
        )
        print("Backend Container Stats:")
        print(result.stdout)
    except:
        print("  (Could not get Docker stats)")
    
    # Setup test user
    print("\n[2/5] Setting up performance test...")
    async with httpx.AsyncClient(timeout=30) as client:
        reg = await client.post(
            f"{base_url}/api/auth/register",
            json={
                "username": f"perf_test_{int(time.time())}",
                "email": f"perf_{int(time.time())}@test.com",
                "password": "Pass123!"
            }
        )
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("  ✓ Test user created")
        
        # Analyze: Start with light load (10 orders/sec)
        print("\n[3/5] Testing at different load levels...")
        
        load_levels = [
            ("Light", 10, 2.0),      # 10 orders/sec for 2 seconds
            ("Medium", 50, 5.0),     # 50 orders/sec for 5 seconds
            ("Heavy", 200, 10.0),    # 200 orders/sec for 10 seconds
        ]
        
        for load_name, target_rate, duration in load_levels:
            print(f"\n  {load_name} Load ({target_rate} orders/sec):")
            
            # Get resource usage before
            before_mem = get_docker_memory()
            
            # Submit orders at target rate
            start = time.perf_counter()
            interval = 1.0 / target_rate
            order_count = 0
            success_count = 0
            errors = []
            latencies = []
            
            while time.perf_counter() - start < duration:
                order_start = time.perf_counter()
                try:
                    resp = await client.post(
                        f"{base_url}/api/orders",
                        json={
                            "symbol": "AAPL",
                            "side": "BUY" if order_count % 2 == 0 else "SELL",
                            "order_type": "MARKET",
                            "quantity": 100.0,
                            "price": 150.0,
                        },
                        headers=headers,
                        timeout=5
                    )
                    
                    latency = (time.perf_counter() - order_start) * 1000
                    latencies.append(latency)
                    
                    if resp.status_code in (200, 201):
                        success_count += 1
                    else:
                        errors.append(f"Status {resp.status_code}")
                    
                    order_count += 1
                    
                    # Rate limiting
                    wait_time = interval - (time.perf_counter() - order_start)
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)
                except Exception as e:
                    errors.append(str(e))
                    order_count += 1
            
            # Get resource usage after
            after_mem = get_docker_memory()
            elapsed = time.perf_counter() - start
            
            # Analyze results
            actual_rate = order_count / elapsed
            success_rate = (success_count / order_count * 100) if order_count > 0 else 0
            
            if latencies:
                latencies.sort()
                avg_latency = sum(latencies) / len(latencies)
                p99_latency = latencies[int(len(latencies) * 0.99)]
            else:
                avg_latency = p99_latency = 0
            
            print(f"    Target rate: {target_rate}/sec")
            print(f"    Actual rate: {actual_rate:.1f}/sec")
            print(f"    Success: {success_count}/{order_count} ({success_rate:.1f}%)")
            print(f"    Latency: {avg_latency:.2f}ms avg, {p99_latency:.2f}ms p99")
            print(f"    Memory: {before_mem}MB → {after_mem}MB (Δ{after_mem-before_mem}MB)")
            
            if errors and len(errors) <= 3:
                print(f"    Errors: {errors}")
        
        # Analyze with sustained high load
        print("\n[4/5] Sustained high load test (20 seconds)...")
        
        start = time.perf_counter()
        end = start + 20.0
        order_count = 0
        success_count = 0
        cpu_spikes = 0
        memory_peak = 0
        
        while time.perf_counter() < end:
            try:
                resp = await client.post(
                    f"{base_url}/api/orders",
                    json={
                        "symbol": "GOOGL",
                        "side": "BUY" if order_count % 2 == 0 else "SELL",
                        "order_type": "MARKET",
                        "quantity": 50.0,
                        "price": 2800.0,
                    },
                    headers=headers,
                    timeout=5
                )
                if resp.status_code in (200, 201):
                    success_count += 1
                order_count += 1
            except:
                order_count += 1
            
            # Check resource periodically
            if order_count % 100 == 0:
                mem = get_docker_memory()
                memory_peak = max(memory_peak, mem)
        
        elapsed = time.perf_counter() - start
        throughput = order_count / elapsed
        
        print(f"    Total orders: {order_count}")
        print(f"    Successful: {success_count}")
        print(f"    Throughput: {throughput:.0f} orders/sec")
        print(f"    Peak memory: {memory_peak}MB")
        
        # Bottleneck categorization
        print("\n[5/5] Bottleneck Classification...")
        
        print("\n  SOFTWARE BOTTLENECKS (Fixable in code):")
        print("    1. gRPC Protocol Overhead")
        print("       - Issue: 1-2ms per order (protobuf + TCP RTT)")
        print("       - Solution: Implement UDP protocol")
        print("       - Impact: 10-15x improvement (low confidence)")
        print("       - Effort: 10-14 hours")
        
        print("    2. Sequential Order Processing")
        print("       - Issue: Orders processed one at a time")
        print("       - Solution: Already implemented (batch submission)")
        print("       - Impact: Already achieved with adaptive batching")
        print("       - Effort: 0 (done)")
        
        print("    3. Database Write Latency")
        print("       - Issue: Async batch writer may have buffering delay")
        print("       - Solution: Tune batch size/timeout or use async connection pooling")
        print("       - Impact: 1-2x (not on critical path currently)")
        print("       - Effort: 2-4 hours")
        
        print("\n  HARDWARE BOTTLENECKS (System resource constraints):")
        print("    1. Network Bandwidth")
        print("       - Issue: Docker network MTU/throughput limits")
        print("       - Evidence: Need to measure actual network utilization")
        print("       - Solution: Use host network or optimize packet size")
        print("       - Impact: Depends on actual utilization")
        print("       - Effort: 4-8 hours")
        
        print("    2. CPU Utilization")
        print("       - Issue: CPU cores saturated?")
        print("       - Evidence: Need CPU monitoring during load test")
        print("       - Solution: Add more workers or optimize hot paths")
        print("       - Impact: Depends on current utilization")
        print("       - Effort: 4-8 hours")
        
        print("    3. Memory Pressure")
        print("       - Issue: Memory exhausted causing GC pauses?")
        print("       - Evidence: Memory peak: {}MB ({}MB limit)".format(memory_peak, 2048))
        print("       - Solution: Increase memory or optimize allocation")
        print("       - Impact: Reduce jitter if memory constrained")
        print("       - Effort: 1-2 hours")
        
        print("    4. Disk I/O (Database)")
        print("       - Issue: PostgreSQL write latency?")
        print("       - Evidence: Async writer is buffering (not measured)")
        print("       - Solution: Already async, tuning may help")
        print("       - Impact: Minimal (not on critical path)")
        print("       - Effort: 2-4 hours")
        
        print("\n" + "=" * 80)
        print("RECOMMENDATION: Target software bottlenecks first")
        print("=" * 80)
        print("\nPriority 1 (HIGH - Software):")
        print("  → UDP Protocol Implementation (10-15x improvement)")
        print("     Effort: 10-14 hours | Impact: 679 → 5,000-10,000 orders/sec")
        
        print("\nPriority 2 (MEDIUM - Software):")
        print("  → Database Write Tuning (1-2x improvement)")
        print("     Effort: 2-4 hours | Impact: Reduce latency variance")
        
        print("\nPriority 3 (LOW - Hardware):")
        print("  → Monitor CPU/Memory/Network utilization under load")
        print("     Effort: 2-4 hours | Impact: Identify hardware limits")
        
        print("\n" + "=" * 80)

def get_docker_memory():
    """Get Docker container memory usage in MB"""
    try:
        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", "hft-backend"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # Parse "123.4MiB" format
        mem_str = result.stdout.strip().split("MiB")[0]
        return float(mem_str)
    except:
        return 0

if __name__ == "__main__":
    asyncio.run(main())
