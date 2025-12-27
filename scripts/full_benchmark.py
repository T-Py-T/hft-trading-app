#!/usr/bin/env python3
# scripts/full_benchmark.py
# Run performance benchmarks from inside the Docker network for accurate measurements

import subprocess
import json
import sys

def run_benchmark():
    """Run benchmark inside Docker network"""
    
    # Create a temporary Python script to run in the container
    benchmark_code = """
import asyncio
import time
import httpx
import statistics
from dataclasses import dataclass
from typing import List

@dataclass
class BenchmarkResult:
    name: str
    throughput: float
    latency_avg: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    error_rate: float
    total_requests: int
    errors: int

class PerformanceBenchmark:
    def __init__(self, base_url: str = "http://hft-backend:8000"):
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
                    elapsed = (time.perf_counter() - start) * 1000
                    
                    if response.status_code not in (200, 201, 202, 404):
                        return elapsed, True
                    return elapsed, False
            except Exception as e:
                return 0, True
        
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
        print("\\n" + "="*70)
        print("HFT Trading Platform - Performance Benchmark (Docker Network)")
        print("="*70 + "\\n")
        
        # Health check tests
        await self.benchmark_endpoint(
            "Health Check (Sequential)",
            "GET",
            "/health",
            num_requests=2000,
            concurrent=1,
        )
        
        await self.benchmark_endpoint(
            "Health Check (10x Concurrent)",
            "GET",
            "/health",
            num_requests=2000,
            concurrent=10,
        )
        
        print("\\n" + "="*70)
        print("Benchmark Results")
        print("="*70 + "\\n")
        
        for result in self.results:
            print(f"Test: {result.name}")
            print(f"  Throughput:      {result.throughput:,.1f} req/sec")
            print(f"  Latency (avg):   {result.latency_avg:.2f}ms")
            print(f"  Latency (p50):   {result.latency_p50:.2f}ms")
            print(f"  Latency (p95):   {result.latency_p95:.2f}ms")
            print(f"  Latency (p99):   {result.latency_p99:.2f}ms")
            print(f"  Error Rate:      {result.error_rate:.1f}%")
            print()

async def main():
    benchmark = PerformanceBenchmark()
    await benchmark.run_suite()

asyncio.run(main())
"""
    
    # Write to temp file
    with open("/tmp/benchmark_docker.py", "w") as f:
        f.write(benchmark_code)
    
    # Run in backend container
    cmd = [
        "docker", "run", "--rm",
        "--network", "hft-trading-app_hft-network",
        "-v", "/tmp/benchmark_docker.py:/tmp/benchmark_docker.py",
        "hft-trading-app-hft-backend",
        "python3", "/tmp/benchmark_docker.py"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr, file=sys.stderr)
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_benchmark())
