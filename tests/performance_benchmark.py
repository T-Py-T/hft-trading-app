#!/usr/bin/env python3
"""
tests/performance_benchmark.py
Performance benchmarking suite for HFT Trading Platform
Tests: throughput, latency, memory, scalability, stability
"""

import asyncio
import time
import statistics
import sys
import requests
import json
from dataclasses import dataclass
from typing import List


@dataclass
class BenchmarkResult:
    name: str
    throughput: float  # orders/sec
    latency_avg: float  # milliseconds
    latency_p50: float
    latency_p95: float
    latency_p99: float
    memory_mb: float
    errors: int


class PerformanceBenchmark:
    """Run comprehensive performance benchmarks"""

    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.latencies: List[float] = []
        self.errors = 0

    def measure_latency(self, func, *args, **kwargs) -> float:
        """Measure function execution time in milliseconds"""
        start = time.perf_counter()
        func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        self.latencies.append(elapsed)
        return elapsed

    def test_backend_health(self) -> BenchmarkResult:
        """Test 1: Backend Health Check Response Time"""
        print("\n[Test 1] Backend Health Check Response Time")
        self.latencies = []
        self.errors = 0

        try:
            for i in range(100):
                try:
                    start = time.perf_counter()
                    response = requests.get(f"{self.backend_url}/health", timeout=1)
                    elapsed = (time.perf_counter() - start) * 1000
                    
                    if response.status_code != 200:
                        self.errors += 1
                    else:
                        self.latencies.append(elapsed)
                except Exception as e:
                    self.errors += 1

            if not self.latencies:
                return None

            result = BenchmarkResult(
                name="Backend Health Check",
                throughput=100000 / (sum(self.latencies) / 1000),  # operations/sec
                latency_avg=statistics.mean(self.latencies),
                latency_p50=sorted(self.latencies)[50],
                latency_p95=sorted(self.latencies)[95],
                latency_p99=sorted(self.latencies)[99],
                memory_mb=0,
                errors=self.errors,
            )
            
            print(f"  Throughput: {result.throughput:.0f} req/sec")
            print(f"  Latency (avg): {result.latency_avg:.2f}ms")
            print(f"  Latency (p50): {result.latency_p50:.2f}ms")
            print(f"  Latency (p95): {result.latency_p95:.2f}ms")
            print(f"  Latency (p99): {result.latency_p99:.2f}ms")
            print(f"  Errors: {self.errors}/100")
            
            return result
        except Exception as e:
            print(f"  Error: {e}")
            return None

    def test_concurrent_health_checks(self) -> BenchmarkResult:
        """Test 2: Concurrent Health Checks (Load)"""
        print("\n[Test 2] Concurrent Health Checks (10 concurrent)")
        self.latencies = []
        self.errors = 0

        async def concurrent_requests():
            tasks = []
            for i in range(100):
                tasks.append(self._async_health_check())
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results

        try:
            results = asyncio.run(concurrent_requests())
            
            result = BenchmarkResult(
                name="Concurrent Health Checks (10x concurrent)",
                throughput=len(self.latencies) / (sum(self.latencies) / 1000 / 1000),
                latency_avg=statistics.mean(self.latencies) if self.latencies else 0,
                latency_p50=sorted(self.latencies)[50] if len(self.latencies) > 50 else 0,
                latency_p95=sorted(self.latencies)[95] if len(self.latencies) > 95 else 0,
                latency_p99=sorted(self.latencies)[99] if len(self.latencies) > 99 else 0,
                memory_mb=0,
                errors=self.errors,
            )
            
            print(f"  Throughput: {result.throughput:.0f} req/sec")
            print(f"  Latency (avg): {result.latency_avg:.2f}ms")
            print(f"  Latency (p95): {result.latency_p95:.2f}ms")
            print(f"  Latency (p99): {result.latency_p99:.2f}ms")
            print(f"  Errors: {self.errors}/100")
            
            return result
        except Exception as e:
            print(f"  Error: {e}")
            return None

    async def _async_health_check(self):
        """Helper for concurrent health checks"""
        try:
            start = time.perf_counter()
            response = requests.get(f"{self.backend_url}/health", timeout=1)
            elapsed = (time.perf_counter() - start) * 1000
            
            if response.status_code == 200:
                self.latencies.append(elapsed)
            else:
                self.errors += 1
        except:
            self.errors += 1

    def test_order_submission_latency(self) -> BenchmarkResult:
        """Test 3: Order Submission Latency (if backend implements it)"""
        print("\n[Test 3] Order Submission Latency")
        self.latencies = []
        self.errors = 0

        try:
            for i in range(50):
                try:
                    order_data = {
                        "symbol": "AAPL",
                        "side": "buy",
                        "order_type": "market",
                        "quantity": 100,
                    }
                    
                    start = time.perf_counter()
                    response = requests.post(
                        f"{self.backend_url}/orders",
                        json=order_data,
                        timeout=5,
                    )
                    elapsed = (time.perf_counter() - start) * 1000
                    
                    if response.status_code in [200, 202, 404]:
                        self.latencies.append(elapsed)
                    else:
                        self.errors += 1
                except Exception as e:
                    self.errors += 1

            if not self.latencies:
                print("  Endpoint not implemented (expected)")
                return None

            result = BenchmarkResult(
                name="Order Submission",
                throughput=len(self.latencies) / (sum(self.latencies) / 1000),
                latency_avg=statistics.mean(self.latencies),
                latency_p50=sorted(self.latencies)[len(self.latencies)//2],
                latency_p95=sorted(self.latencies)[int(len(self.latencies)*0.95)],
                latency_p99=sorted(self.latencies)[int(len(self.latencies)*0.99)],
                memory_mb=0,
                errors=self.errors,
            )
            
            print(f"  Throughput: {result.throughput:.0f} orders/sec")
            print(f"  Latency (avg): {result.latency_avg:.2f}ms")
            print(f"  Latency (p99): {result.latency_p99:.2f}ms")
            print(f"  Errors: {self.errors}/50")
            
            return result
        except Exception as e:
            print(f"  Skipped: {e}")
            return None

    def test_sustained_load(self, duration_secs: int = 10) -> BenchmarkResult:
        """Test 4: Sustained Load (health checks for N seconds)"""
        print(f"\n[Test 4] Sustained Load ({duration_secs} seconds)")
        self.latencies = []
        self.errors = 0
        request_count = 0

        try:
            start = time.time()
            while time.time() - start < duration_secs:
                try:
                    req_start = time.perf_counter()
                    response = requests.get(
                        f"{self.backend_url}/health",
                        timeout=1,
                    )
                    elapsed = (time.perf_counter() - req_start) * 1000
                    
                    if response.status_code == 200:
                        self.latencies.append(elapsed)
                        request_count += 1
                    else:
                        self.errors += 1
                except:
                    self.errors += 1

            result = BenchmarkResult(
                name=f"Sustained Load ({duration_secs}s)",
                throughput=request_count / duration_secs,
                latency_avg=statistics.mean(self.latencies) if self.latencies else 0,
                latency_p50=sorted(self.latencies)[len(self.latencies)//2] if self.latencies else 0,
                latency_p95=sorted(self.latencies)[int(len(self.latencies)*0.95)] if len(self.latencies) > 20 else 0,
                latency_p99=sorted(self.latencies)[int(len(self.latencies)*0.99)] if len(self.latencies) > 100 else 0,
                memory_mb=0,
                errors=self.errors,
            )
            
            print(f"  Requests: {request_count} over {duration_secs}s")
            print(f"  Throughput: {result.throughput:.0f} req/sec")
            print(f"  Latency (avg): {result.latency_avg:.2f}ms")
            print(f"  Latency (p99): {result.latency_p99:.2f}ms")
            print(f"  Errors: {self.errors}")
            
            return result
        except Exception as e:
            print(f"  Error: {e}")
            return None

    def print_summary(self, results: List[BenchmarkResult]):
        """Print benchmark summary report"""
        print("\n" + "="*80)
        print("PERFORMANCE BENCHMARK SUMMARY")
        print("="*80)
        
        for result in results:
            if result:
                print(f"\n{result.name}:")
                print(f"  Throughput: {result.throughput:>10.0f} req/sec")
                print(f"  Latency (avg): {result.latency_avg:>10.2f}ms")
                print(f"  Latency (p99): {result.latency_p99:>10.2f}ms")
                print(f"  Error Rate: {(result.errors/100)*100:>10.1f}%")
        
        print("\n" + "="*80)
        print("EXPECTATIONS FOR HFT PLATFORM:")
        print("="*80)
        print("  Throughput: >10,000 req/sec (ideally 100,000+)")
        print("  Latency p99: <10ms (ideally <1ms)")
        print("  Error Rate: <0.1%")
        print("  Stable under sustained load")
        print("="*80)


def main():
    """Run all benchmarks"""
    print("Starting Performance Benchmarks...")
    print("Assuming services running at localhost:8000")
    
    try:
        requests.get("http://localhost:8000/health", timeout=2)
    except:
        print("ERROR: Backend not responding at localhost:8000")
        print("Start services with: docker-compose up -d")
        sys.exit(1)

    benchmark = PerformanceBenchmark()
    results = []

    # Run benchmarks
    results.append(benchmark.test_backend_health())
    results.append(benchmark.test_concurrent_health_checks())
    results.append(benchmark.test_order_submission_latency())
    results.append(benchmark.test_sustained_load(duration_secs=10))

    # Print summary
    benchmark.print_summary([r for r in results if r])

    print("\nBenchmark complete!")


if __name__ == "__main__":
    main()
