#!/usr/bin/env python3
# scripts/performance_benchmark.py
# Performance benchmarking suite for HFT Trading Platform
# Measures throughput, latency, and error rates for API endpoints

import asyncio
import time
import httpx
import statistics
from dataclasses import dataclass
from typing import List

@dataclass
class BenchmarkResult:
    """Results from a single benchmark run"""
    name: str
    throughput: float  # requests per second
    latency_avg: float  # milliseconds
    latency_p50: float
    latency_p95: float
    latency_p99: float
    error_rate: float  # percentage
    total_requests: int
    errors: int

class PerformanceBenchmark:
    """Run comprehensive performance benchmarks on the trading platform"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[BenchmarkResult] = []
    
    async def benchmark_endpoint(
        self,
        name: str,
        method: str,
        endpoint: str,
        num_requests: int = 1000,
        concurrent: int = 1,
        data: dict = None,
    ) -> BenchmarkResult:
        """Benchmark a single endpoint with concurrent requests"""
        
        latencies = []
        errors = 0
        
        async def make_request():
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    start = time.perf_counter()
                    if method.upper() == "GET":
                        response = await client.get(f"{self.base_url}{endpoint}")
                    else:
                        response = await client.post(f"{self.base_url}{endpoint}", json=data)
                    elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
                    
                    if response.status_code not in (200, 201, 202, 404):
                        return elapsed, True  # Error
                    return elapsed, False
            except Exception as e:
                print(f"Request error: {e}")
                return 0, True
        
        # Run requests with concurrency control
        semaphore = asyncio.Semaphore(concurrent)
        
        async def limited_request():
            async with semaphore:
                return await make_request()
        
        print(f"Running: {name} ({num_requests} requests, {concurrent} concurrent)")
        start_time = time.perf_counter()
        
        tasks = [limited_request() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.perf_counter() - start_time
        
        for latency, is_error in results:
            if is_error:
                errors += 1
            else:
                latencies.append(latency)
        
        # Calculate statistics
        if latencies:
            latencies.sort()
            throughput = num_requests / elapsed
            latency_avg = statistics.mean(latencies)
            latency_p50 = latencies[int(len(latencies) * 0.5)]
            latency_p95 = latencies[int(len(latencies) * 0.95)]
            latency_p99 = latencies[int(len(latencies) * 0.99)]
        else:
            throughput = 0
            latency_avg = latency_p50 = latency_p95 = latency_p99 = 0
        
        error_rate = (errors / num_requests) * 100
        
        result = BenchmarkResult(
            name=name,
            throughput=throughput,
            latency_avg=latency_avg,
            latency_p50=latency_p50,
            latency_p95=latency_p95,
            latency_p99=latency_p99,
            error_rate=error_rate,
            total_requests=num_requests,
            errors=errors,
        )
        
        self.results.append(result)
        return result
    
    async def run_suite(self):
        """Run complete benchmark suite"""
        
        print("\n" + "="*70)
        print("HFT Trading Platform - Performance Benchmark Suite")
        print("="*70 + "\n")
        
        # 1. Health check - sequential
        await self.benchmark_endpoint(
            "Health Check (Sequential)",
            "GET",
            "/health",
            num_requests=1000,
            concurrent=1,
        )
        
        # 2. Health check - concurrent
        await self.benchmark_endpoint(
            "Health Check (10x Concurrent)",
            "GET",
            "/health",
            num_requests=1000,
            concurrent=10,
        )
        
        # 3. Order submission
        await self.benchmark_endpoint(
            "Order Submission",
            "POST",
            "/api/orders",
            num_requests=500,
            concurrent=5,
            data={
                "symbol": "AAPL",
                "side": "BUY",
                "order_type": "MARKET",
                "quantity": 100,
                "price": 150.0,
            },
        )
        
        # Print results
        print("\n" + "="*70)
        print("Benchmark Results")
        print("="*70 + "\n")
        
        for result in self.results:
            print(f"Test: {result.name}")
            print(f"  Throughput:      {result.throughput:,.1f} req/sec")
            print(f"  Latency (avg):   {result.latency_avg:.2f}ms")
            print(f"  Latency (p50):   {result.latency_p50:.2f}ms")
            print(f"  Latency (p95):   {result.latency_p95:.2f}ms")
            print(f"  Latency (p99):   {result.latency_p99:.2f}ms")
            print(f"  Error Rate:      {result.error_rate:.1f}%")
            print(f"  Requests:        {result.total_requests} ({result.errors} errors)")
            print()
        
        # Summary
        print("="*70)
        print("Summary")
        print("="*70)
        health_result = next((r for r in self.results if "Health Check (Sequential)" in r.name), None)
        if health_result:
            target_throughput = 10000
            ratio = health_result.throughput / target_throughput
            print(f"Health Check Throughput: {health_result.throughput:,.0f} req/sec")
            print(f"Target:                  {target_throughput:,} req/sec")
            print(f"Performance Ratio:       {ratio:.1f}x target")

async def main():
    benchmark = PerformanceBenchmark()
    try:
        await benchmark.run_suite()
    except Exception as e:
        print(f"Benchmark failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
