#!/usr/bin/env python3
# scripts/performance_test.py
# Real-world performance test - measures actual API latency from within Docker network

import subprocess
import json
import sys
import tempfile
import os

benchmark_script = '''
import asyncio
import time
import httpx
import json
import statistics

async def run_benchmark():
    """Run health check benchmarks"""
    
    base_url = "http://hft-backend:8000"
    
    # Test 1: Sequential requests
    print("Test 1: Sequential Health Checks (1000 requests)")
    latencies_seq = []
    errors = 0
    
    start = time.perf_counter()
    for i in range(1000):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                req_start = time.perf_counter()
                response = await client.get(f"{base_url}/health")
                req_latency = (time.perf_counter() - req_start) * 1000
                if response.status_code == 200:
                    latencies_seq.append(req_latency)
                else:
                    errors += 1
        except Exception as e:
            errors += 1
    
    elapsed_seq = time.perf_counter() - start
    throughput_seq = 1000 / elapsed_seq
    
    if latencies_seq:
        latencies_seq.sort()
        print(f"  Throughput: {throughput_seq:.1f} req/sec")
        print(f"  Latency avg: {statistics.mean(latencies_seq):.2f}ms")
        print(f"  Latency p50: {latencies_seq[len(latencies_seq)//2]:.2f}ms")
        print(f"  Latency p99: {latencies_seq[int(len(latencies_seq)*0.99)]:.2f}ms")
        print(f"  Errors: {errors}/1000\\n")
    
    # Test 2: Concurrent requests
    print("Test 2: Concurrent Health Checks (1000 requests, 10 concurrent)")
    
    async def make_request(client):
        try:
            req_start = time.perf_counter()
            response = await client.get(f"{base_url}/health")
            req_latency = (time.perf_counter() - req_start) * 1000
            return (response.status_code == 200, req_latency)
        except:
            return (False, 0)
    
    async with httpx.AsyncClient(timeout=10) as client:
        latencies_conc = []
        errors = 0
        
        start = time.perf_counter()
        
        # Create tasks in batches of 10
        for batch in range(100):
            tasks = [make_request(client) for _ in range(10)]
            results = await asyncio.gather(*tasks)
            for success, lat in results:
                if success:
                    latencies_conc.append(lat)
                else:
                    errors += 1
        
        elapsed_conc = time.perf_counter() - start
        throughput_conc = 1000 / elapsed_conc
    
    if latencies_conc:
        latencies_conc.sort()
        print(f"  Throughput: {throughput_conc:.1f} req/sec")
        print(f"  Latency avg: {statistics.mean(latencies_conc):.2f}ms")
        print(f"  Latency p50: {latencies_conc[len(latencies_conc)//2]:.2f}ms")
        print(f"  Latency p99: {latencies_conc[int(len(latencies_conc)*0.99)]:.2f}ms")
        print(f"  Errors: {errors}/1000\\n")
    
    # Summary
    print("="*50)
    print("Summary:")
    print(f"  Sequential: {throughput_seq:.1f} req/sec")
    print(f"  Concurrent: {throughput_conc:.1f} req/sec")
    print(f"  Improvement: {throughput_conc/throughput_seq:.1f}x")

asyncio.run(run_benchmark())
'''

def main():
    # Write script to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(benchmark_script)
        temp_script = f.name
    
    try:
        # Run in backend container
        cmd = [
            "docker", "exec",
            "hft-backend",
            "python3", "-"
        ]
        
        result = subprocess.run(
            cmd,
            input=benchmark_script,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr, file=sys.stderr)
        return result.returncode
    finally:
        os.unlink(temp_script)

if __name__ == "__main__":
    sys.exit(main())
