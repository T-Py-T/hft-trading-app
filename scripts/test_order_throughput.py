#!/usr/bin/env python3
# scripts/test_order_throughput.py
# Test order submission throughput with Redis queue

import asyncio
import time
import httpx
import statistics
from typing import List

async def test_order_throughput(num_orders: int = 500, concurrent: int = 5):
    """Test order submission throughput"""
    
    base_url = "http://localhost:8000"
    
    print("="*70)
    print(f"Order Submission Throughput Test ({num_orders} orders, {concurrent} concurrent)")
    print("="*70 + "\n")
    
    order_latencies = []
    errors = 0
    
    async def submit_order():
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                start = time.perf_counter()
                
                response = await client.post(
                    f"{base_url}/api/orders",
                    json={
                        "symbol": "AAPL",
                        "side": "BUY",
                        "order_type": "MARKET",
                        "quantity": 100.0,
                        "price": 150.0,
                    },
                    headers={"Authorization": "Bearer test-token"}
                )
                
                latency = (time.perf_counter() - start) * 1000
                
                if response.status_code in (200, 201, 202):
                    return latency, False
                else:
                    return latency, True
        except Exception as e:
            print(f"Error: {e}")
            return 0, True
    
    # Run orders with concurrency control
    semaphore = asyncio.Semaphore(concurrent)
    
    async def limited_submit():
        async with semaphore:
            return await submit_order()
    
    print(f"Submitting {num_orders} orders...")
    start_time = time.perf_counter()
    
    tasks = [limited_submit() for _ in range(num_orders)]
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
        p99_latency = order_latencies[int(len(order_latencies)*0.99)]
    else:
        throughput = 0
        avg_latency = p50_latency = p99_latency = 0
    
    error_rate = (errors / num_orders) * 100
    
    print(f"\nResults:")
    print(f"  Total Time:      {total_time:.2f}s")
    print(f"  Throughput:      {throughput:.1f} orders/sec")
    print(f"  Latency (avg):   {avg_latency:.2f}ms")
    print(f"  Latency (p50):   {p50_latency:.2f}ms")
    print(f"  Latency (p99):   {p99_latency:.2f}ms")
    print(f"  Error Rate:      {error_rate:.1f}%")
    print(f"  Successful:      {num_orders - errors}/{num_orders}")
    
    print(f"\nTarget: 1000 orders/sec")
    ratio = throughput / 1000 if throughput > 0 else 0
    print(f"Achievement: {ratio:.1%} of target")
    
    # Check Redis queue
    try:
        import aioredis
        redis = await aioredis.from_url("redis://localhost:6379/0")
        queue_size = await redis.llen("hft:orders:queue")
        print(f"\nRedis Queue Status:")
        print(f"  Pending Orders: {queue_size}")
        await redis.close()
    except Exception as e:
        print(f"Could not check Redis: {e}")

async def main():
    await test_order_throughput(num_orders=500, concurrent=5)

if __name__ == "__main__":
    asyncio.run(main())
