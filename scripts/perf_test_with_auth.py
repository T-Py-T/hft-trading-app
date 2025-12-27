#!/usr/bin/env python3
# scripts/perf_test_with_auth.py
# Performance test with proper authentication

import asyncio
import time
import httpx
import statistics
import json

async def test_order_performance():
    """Test order submission performance with Redis queue"""
    
    base_url = "http://localhost:8000"
    
    print("="*70)
    print("HFT Trading Platform - Order Submission Performance Test")
    print("Redis Queue + Async Batch Writer")
    print("="*70 + "\n")
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Step 1: Register a test user
        print("Step 1: Registering test user...")
        test_email = f"test_{int(time.time())}@example.com"
        test_username = f"testuser_{int(time.time())}"
        
        register_response = await client.post(
            f"{base_url}/api/auth/register",
            json={
                "username": test_username,
                "email": test_email,
                "password": "TestPassword123!"
            }
        )
        
        if register_response.status_code != 201:
            print(f"Registration failed: {register_response.status_code}")
            print(f"Response: {register_response.text}")
            return
        
        token_data = register_response.json()
        token = token_data.get("access_token")
        print(f"  User registered: {test_username}")
        print(f"  Token obtained: {token[:20]}...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        print("\nStep 2: Running order submission benchmark...")
        print("  Submitting 200 orders with 10 concurrent workers...\n")
        
        num_orders = 200
        concurrent = 10
        order_latencies = []
        errors = 0
        
        async def submit_order(index: int):
            try:
                start = time.perf_counter()
                
                response = await client.post(
                    f"{base_url}/api/orders",
                    json={
                        "symbol": "AAPL",
                        "side": "BUY" if index % 2 == 0 else "SELL",
                        "order_type": "MARKET",
                        "quantity": 100.0 + (index % 50),
                        "price": 150.0 + (index % 10),
                    },
                    headers=headers
                )
                
                latency = (time.perf_counter() - start) * 1000
                
                if response.status_code in (200, 201, 202):
                    return latency, False
                else:
                    print(f"  Order {index}: {response.status_code}")
                    return latency, True
            except Exception as e:
                print(f"  Order {index} error: {e}")
                return 0, True
        
        # Submit with concurrency control
        semaphore = asyncio.Semaphore(concurrent)
        
        async def limited_submit(index):
            async with semaphore:
                return await submit_order(index)
        
        start_time = time.perf_counter()
        
        tasks = [limited_submit(i) for i in range(num_orders)]
        results = await asyncio.gather(*tasks)
        
        total_time = time.perf_counter() - start_time
        
        for latency, is_error in results:
            if is_error:
                errors += 1
            else:
                order_latencies.append(latency)
        
        # Calculate statistics
        if order_latencies:
            order_latencies.sort()
            throughput = num_orders / total_time
            avg_latency = statistics.mean(order_latencies)
            p50_latency = order_latencies[len(order_latencies)//2]
            p95_latency = order_latencies[int(len(order_latencies)*0.95)]
            p99_latency = order_latencies[int(len(order_latencies)*0.99)]
            min_latency = min(order_latencies)
            max_latency = max(order_latencies)
        else:
            throughput = 0
            avg_latency = p50_latency = p95_latency = p99_latency = 0
            min_latency = max_latency = 0
        
        error_rate = (errors / num_orders) * 100
        
        print("\n" + "="*70)
        print("PERFORMANCE RESULTS")
        print("="*70)
        print(f"\nExecution:")
        print(f"  Total Time:       {total_time:.2f}s")
        print(f"  Orders Submitted: {num_orders}")
        print(f"  Successful:       {num_orders - errors}")
        print(f"  Failed:           {errors}")
        
        print(f"\nThroughput:")
        print(f"  Orders/sec:       {throughput:.1f}")
        print(f"  Target:           1000 orders/sec")
        print(f"  Achievement:      {(throughput/1000)*100:.1f}% of target")
        
        print(f"\nLatency (milliseconds):")
        print(f"  Min:              {min_latency:.2f}ms")
        print(f"  Average:          {avg_latency:.2f}ms")
        print(f"  P50:              {p50_latency:.2f}ms")
        print(f"  P95:              {p95_latency:.2f}ms")
        print(f"  P99:              {p99_latency:.2f}ms")
        print(f"  Max:              {max_latency:.2f}ms")
        
        print(f"\nReliability:")
        print(f"  Error Rate:       {error_rate:.1f}%")
        
        # Check Redis queue
        print(f"\nRedis Queue Status:")
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "exec", "hft-redis", "redis-cli", "LLEN", "hft:orders:queue"],
                capture_output=True, text=True, timeout=5
            )
            queue_size = int(result.stdout.strip())
            print(f"  Pending Orders:   {queue_size}")
            print(f"  (Orders queued for batch write to Postgres)")
        except Exception as e:
            print(f"  Could not check queue: {e}")
        
        print("\n" + "="*70)
        print("PERFORMANCE TEST COMPLETE")
        print("="*70)

async def main():
    await test_order_performance()

if __name__ == "__main__":
    asyncio.run(main())
