#!/usr/bin/env python3
# Simple integration test focused on response times and system behavior

import asyncio
import time
import httpx
from datetime import datetime
import statistics

BASE_URL = "http://localhost:8000"


async def run_performance_test():
    """Test backend response times and stability."""
    print("\n" + "=" * 70)
    print("HFT TRADING PLATFORM - PERFORMANCE TEST")
    print("=" * 70)
    print(f"Start time: {datetime.now().isoformat()}")
    print(f"Backend URL: {BASE_URL}\n")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # Test 1: Health check
        print("=== TEST 1: Health Endpoint ===")
        response_times = []
        for i in range(20):
            start = time.time()
            try:
                response = await client.get("/health")
                elapsed = (time.time() - start) * 1000
                response_times.append(elapsed)
                if response.status_code == 200:
                    print(f"  Request {i+1}: {elapsed:.2f}ms - Status 200")
                else:
                    print(f"  Request {i+1}: {elapsed:.2f}ms - Status {response.status_code}")
            except Exception as e:
                print(f"  Request {i+1}: ERROR - {e}")

        if response_times:
            print(f"\nHealth Endpoint Stats:")
            print(f"  Avg: {statistics.mean(response_times):.2f}ms")
            print(f"  Median: {statistics.median(response_times):.2f}ms")
            print(f"  Min: {min(response_times):.2f}ms")
            print(f"  Max: {max(response_times):.2f}ms")
            print(f"  P95: {sorted(response_times)[int(len(response_times) * 0.95)]:.2f}ms")
            print(f"  RPS: {20 / (sum(response_times) / 1000):.2f}")

        # Test 2: API Docs endpoint
        print("\n=== TEST 2: API Docs Endpoint ===")
        response_times = []
        for i in range(10):
            start = time.time()
            try:
                response = await client.get("/docs")
                elapsed = (time.time() - start) * 1000
                response_times.append(elapsed)
                print(f"  Request {i+1}: {elapsed:.2f}ms - Status {response.status_code}")
            except Exception as e:
                print(f"  Request {i+1}: ERROR - {e}")

        if response_times:
            print(f"\nAPI Docs Stats:")
            print(f"  Avg: {statistics.mean(response_times):.2f}ms")
            print(f"  Median: {statistics.median(response_times):.2f}ms")
            print(f"  Min: {min(response_times):.2f}ms")
            print(f"  Max: {max(response_times):.2f}ms")

        # Test 3: Concurrent requests
        print("\n=== TEST 3: Concurrent Requests ===")
        start_time = time.time()
        tasks = [client.get("/health") for _ in range(50)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start_time

        success = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)
        print(f"  Submitted: 50 concurrent requests")
        print(f"  Success: {success}")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  RPS: {50 / elapsed:.2f}")

    print("\n" + "=" * 70)
    print(f"End time: {datetime.now().isoformat()}")
    print("=" * 70)
    print("\n✓ PERFORMANCE TEST COMPLETE\n")


if __name__ == "__main__":
    asyncio.run(run_performance_test())
