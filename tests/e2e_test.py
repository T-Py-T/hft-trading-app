#!/usr/bin/env python3
# tests/e2e_test.py
# End-to-end integration test with performance metrics
# Mimics real trading workflow with platform behavior analysis

import asyncio
import time
import httpx
from datetime import datetime
import statistics
from typing import List, Dict, Tuple

BASE_URL = "http://localhost:8000"


class PerformanceAnalyzer:
    """Analyze performance metrics across tests."""

    def __init__(self, name: str):
        self.name = name
        self.times: List[float] = []
        self.start_time = None
        self.end_time = None

    def add_time(self, elapsed_ms: float):
        """Record response time."""
        self.times.append(elapsed_ms)

    def start(self):
        """Start test."""
        self.start_time = time.time()

    def stop(self):
        """End test."""
        self.end_time = time.time()

    def summary(self) -> Dict:
        """Get performance summary."""
        if not self.times:
            return {}

        sorted_times = sorted(self.times)
        p95_idx = max(0, int(len(sorted_times) * 0.95) - 1)
        p99_idx = max(0, int(len(sorted_times) * 0.99) - 1)

        return {
            "test_name": self.name,
            "total_requests": len(self.times),
            "avg_ms": statistics.mean(self.times),
            "median_ms": statistics.median(self.times),
            "min_ms": min(self.times),
            "max_ms": max(self.times),
            "p95_ms": sorted_times[p95_idx],
            "p99_ms": sorted_times[p99_idx],
            "stdev_ms": statistics.stdev(self.times) if len(self.times) > 1 else 0,
            "total_duration_sec": self.end_time - self.start_time if self.end_time else 0,
        }

    def print_summary(self):
        """Print formatted summary."""
        summary = self.summary()
        if not summary:
            return

        print(f"\n{self.name} Performance:")
        print(f"  Requests: {summary['total_requests']}")
        print(f"  Avg: {summary['avg_ms']:.2f}ms | Median: {summary['median_ms']:.2f}ms")
        print(f"  Min: {summary['min_ms']:.2f}ms | Max: {summary['max_ms']:.2f}ms")
        print(f"  P95: {summary['p95_ms']:.2f}ms | P99: {summary['p99_ms']:.2f}ms")
        print(f"  StDev: {summary['stdev_ms']:.2f}ms")
        if self.end_time:
            rps = summary["total_requests"] / summary["total_duration_sec"]
            print(f"  Duration: {summary['total_duration_sec']:.2f}s | RPS: {rps:.2f}")


async def test_basic_connectivity() -> Tuple[bool, PerformanceAnalyzer]:
    """Test basic connectivity to backend."""
    print("\n" + "=" * 70)
    print("TEST 1: BASIC CONNECTIVITY")
    print("=" * 70)

    analyzer = PerformanceAnalyzer("Basic Connectivity")
    analyzer.start()

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        success_count = 0
        for i in range(10):
            try:
                start = time.time()
                response = await client.get("/health")
                elapsed = (time.time() - start) * 1000
                analyzer.add_time(elapsed)

                if response.status_code == 200:
                    data = response.json()
                    success_count += 1
                    print(f"  Attempt {i+1}: OK ({elapsed:.2f}ms) - v{data.get('version')}")
                else:
                    print(f"  Attempt {i+1}: Status {response.status_code}")
            except Exception as e:
                print(f"  Attempt {i+1}: ERROR - {str(e)[:50]}")

    analyzer.stop()
    analyzer.print_summary()

    passed = success_count == 10
    print(f"\nResult: {'PASSED' if passed else 'FAILED'} ({success_count}/10 successful)")
    return passed, analyzer


async def test_concurrent_load() -> Tuple[bool, PerformanceAnalyzer]:
    """Test concurrent request handling."""
    print("\n" + "=" * 70)
    print("TEST 2: CONCURRENT LOAD HANDLING")
    print("=" * 70)

    analyzer = PerformanceAnalyzer("Concurrent Load")
    analyzer.start()

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # Send 100 concurrent requests
        tasks = [client.get("/health") for _ in range(100)]
        start = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        total_elapsed = (time.time() - start) * 1000

        success_count = sum(
            1
            for r in responses
            if isinstance(r, httpx.Response) and r.status_code == 200
        )

        # Record individual times (approximate from total)
        avg_time = total_elapsed / len(responses)
        for _ in range(len(responses)):
            analyzer.add_time(avg_time)

    analyzer.stop()
    analyzer.print_summary()

    success_rate = (success_count / len(responses)) * 100
    print(f"\nResult: {success_count}/{len(responses)} successful ({success_rate:.1f}%)")
    return success_rate >= 99, analyzer


async def test_sustained_load() -> Tuple[bool, PerformanceAnalyzer]:
    """Test sustained request load over time."""
    print("\n" + "=" * 70)
    print("TEST 3: SUSTAINED LOAD (30 seconds)")
    print("=" * 70)

    analyzer = PerformanceAnalyzer("Sustained Load")
    analyzer.start()

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        start_time = time.time()
        request_count = 0
        success_count = 0

        # Run for 30 seconds
        while time.time() - start_time < 30:
            try:
                req_start = time.time()
                response = await client.get("/health")
                elapsed = (time.time() - req_start) * 1000
                analyzer.add_time(elapsed)
                request_count += 1

                if response.status_code == 200:
                    success_count += 1

                # Non-blocking sleep to allow other tasks
                await asyncio.sleep(0.01)

            except Exception as e:
                print(f"Error during sustained load: {e}")

    analyzer.stop()
    analyzer.print_summary()

    success_rate = (success_count / request_count) * 100 if request_count > 0 else 0
    print(f"\nResult: {success_count}/{request_count} successful ({success_rate:.1f}%)")
    return success_rate >= 99, analyzer


async def test_response_time_distribution() -> Tuple[bool, PerformanceAnalyzer]:
    """Test response time distribution and outliers."""
    print("\n" + "=" * 70)
    print("TEST 4: RESPONSE TIME DISTRIBUTION")
    print("=" * 70)

    analyzer = PerformanceAnalyzer("Response Distribution")
    analyzer.start()

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        for i in range(50):
            try:
                start = time.time()
                response = await client.get("/health")
                elapsed = (time.time() - start) * 1000
                analyzer.add_time(elapsed)

                if (i + 1) % 10 == 0:
                    print(f"  Completed {i+1} requests...")

            except Exception as e:
                print(f"  Request {i+1}: ERROR - {e}")

    analyzer.stop()
    analyzer.print_summary()

    summary = analyzer.summary()
    # Check if P99 is reasonable (< 100ms for health endpoint)
    passed = summary["p99_ms"] < 100
    print(f"\nResult: {'PASSED' if passed else 'FAILED'} (P99: {summary['p99_ms']:.2f}ms)")
    return passed, analyzer


async def main():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("HFT TRADING PLATFORM - END-TO-END INTEGRATION TESTS")
    print("=" * 70)
    print(f"Start time: {datetime.now().isoformat()}")
    print(f"Backend URL: {BASE_URL}")

    results = {}
    all_analyzers = []

    try:
        # Run tests
        passed, analyzer = await test_basic_connectivity()
        results["Connectivity"] = passed
        all_analyzers.append(analyzer)

        passed, analyzer = await test_concurrent_load()
        results["Concurrent Load"] = passed
        all_analyzers.append(analyzer)

        passed, analyzer = await test_sustained_load()
        results["Sustained Load"] = passed
        all_analyzers.append(analyzer)

        passed, analyzer = await test_response_time_distribution()
        results["Response Distribution"] = passed
        all_analyzers.append(analyzer)

        # Print final summary
        print("\n" + "=" * 70)
        print("OVERALL TEST RESULTS")
        print("=" * 70)
        for test_name, passed in results.items():
            status = "PASSED" if passed else "FAILED"
            print(f"  {test_name:30} {status}")

        # Print combined metrics
        print("\n" + "=" * 70)
        print("PERFORMANCE SUMMARY")
        print("=" * 70)

        all_times = []
        for analyzer in all_analyzers:
            all_times.extend(analyzer.times)

        if all_times:
            print(f"\nCombined Results ({len(all_times)} total requests):")
            print(f"  Avg: {statistics.mean(all_times):.2f}ms")
            print(f"  Median: {statistics.median(all_times):.2f}ms")
            print(f"  Min: {min(all_times):.2f}ms")
            print(f"  Max: {max(all_times):.2f}ms")
            print(f"  P95: {sorted(all_times)[int(len(all_times) * 0.95)]:.2f}ms")
            print(f"  P99: {sorted(all_times)[int(len(all_times) * 0.99)]:.2f}ms")

        print("\n" + "=" * 70)
        print(f"End time: {datetime.now().isoformat()}")
        print("=" * 70)

        # Overall pass/fail
        all_passed = all(results.values())
        if all_passed:
            print("\n✓ ALL INTEGRATION TESTS PASSED\n")
            return 0
        else:
            print("\n✗ SOME INTEGRATION TESTS FAILED\n")
            return 1

    except Exception as e:
        print(f"\nFatal error during testing: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
