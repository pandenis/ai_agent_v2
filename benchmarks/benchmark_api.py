"""
Performance Benchmarks for AI Agent API.

Measures:
- Response time per strategy (direct, enhanced, deep_reasoning)
- Throughput (requests per second)
- Cache hit rate
- Concurrent request handling

Usage:
    python benchmarks/benchmark_api.py --host localhost --port 8000

Results are saved to benchmarks/results/benchmark_YYYYMMDD_HHMMSS.json
"""

import argparse
import asyncio
import json
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx


class APIBenchmark:
    """Benchmark suite for AI Agent API."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "benchmarks": {}
        }

    async def health_check(self) -> bool:
        """Verify API is accessible."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
            except Exception as e:
                print(f"Health check failed: {e}")
                return False

    async def create_session(self, client: httpx.AsyncClient) -> Optional[str]:
        """Create a test session."""
        response = await client.post(
            f"{self.base_url}/sessions",
            json={"agent_name": "mistral"}
        )
        if response.status_code == 201:
            return response.json()["session_id"]
        return None

    async def benchmark_single_request(
            self,
            client: httpx.AsyncClient,
            session_id: str,
            query: str
    ) -> dict:
        """Benchmark a single orchestrate request."""
        start_time = time.perf_counter()

        response = await client.post(
            f"{self.base_url}/orchestrate",
            json={"query": query, "session_id": session_id},
            timeout=60.0
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        result = {
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
            "strategy": None,
            "cost_usd": None
        }

        if response.status_code == 200:
            data = response.json()
            metadata = data.get("metadata", {})
            result["strategy"] = metadata.get("strategy")
            result["cost_usd"] = metadata.get("cost_usd")
            result["api_elapsed_ms"] = metadata.get("elapsed_time_ms")

        return result

    async def run_response_time_benchmark(self, iterations: int = 5) -> dict:
        """Benchmark response times for different query types."""
        print("\n📊 Running Response Time Benchmark...")

        queries = {
            "simple": "What is 2+2?",
            "medium": "Explain the difference between Python lists and tuples",
            "complex": "Compare and contrast machine learning and deep learning approaches for natural language processing"
        }

        results = {}

        async with httpx.AsyncClient() as client:
            session_id = await self.create_session(client)
            if not session_id:
                print("Failed to create session")
                return {"error": "Failed to create session"}

            for query_type, query in queries.items():
                print(f"  Testing {query_type} query ({iterations} iterations)...")
                times = []
                strategies = []

                for i in range(iterations):
                    result = await self.benchmark_single_request(client, session_id, query)
                    if result["status_code"] == 200:
                        times.append(result["elapsed_ms"])
                        strategies.append(result["strategy"])
                    await asyncio.sleep(0.5)  # Small delay between requests

                if times:
                    results[query_type] = {
                        "iterations": len(times),
                        "min_ms": round(min(times), 2),
                        "max_ms": round(max(times), 2),
                        "avg_ms": round(statistics.mean(times), 2),
                        "median_ms": round(statistics.median(times), 2),
                        "std_dev_ms": round(statistics.stdev(times), 2) if len(times) > 1 else 0,
                        "strategies": list(set(strategies))
                    }
                    print(
                        f"    ✅ Avg: {results[query_type]['avg_ms']}ms, Strategy: {results[query_type]['strategies']}")

        return results

    async def run_throughput_benchmark(self, duration_seconds: int = 10) -> dict:
        """Measure requests per second."""
        print(f"\n📊 Running Throughput Benchmark ({duration_seconds}s)...")

        async with httpx.AsyncClient() as client:
            session_id = await self.create_session(client)
            if not session_id:
                return {"error": "Failed to create session"}

            request_count = 0
            errors = 0
            start_time = time.perf_counter()

            while (time.perf_counter() - start_time) < duration_seconds:
                try:
                    response = await client.post(
                        f"{self.base_url}/orchestrate",
                        json={"query": "Hello", "session_id": session_id},
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        request_count += 1
                    else:
                        errors += 1
                except Exception:
                    errors += 1

            elapsed = time.perf_counter() - start_time
            rps = request_count / elapsed if elapsed > 0 else 0

            result = {
                "duration_seconds": round(elapsed, 2),
                "total_requests": request_count,
                "errors": errors,
                "requests_per_second": round(rps, 2)
            }
            print(f"  ✅ {result['requests_per_second']} req/s ({request_count} requests)")
            return result

    async def run_concurrent_benchmark(self, concurrent_users: int = 5) -> dict:
        """Test concurrent request handling."""
        print(f"\n📊 Running Concurrent Benchmark ({concurrent_users} users)...")

        async def user_request(user_id: int) -> dict:
            async with httpx.AsyncClient() as client:
                session_id = await self.create_session(client)
                if not session_id:
                    return {"user_id": user_id, "error": "No session"}

                start = time.perf_counter()
                result = await self.benchmark_single_request(
                    client, session_id, f"Hello from user {user_id}"
                )
                result["user_id"] = user_id
                result["total_ms"] = (time.perf_counter() - start) * 1000
                return result

        tasks = [user_request(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks)

        successful = [r for r in results if r.get("status_code") == 200]
        times = [r["elapsed_ms"] for r in successful]

        summary = {
            "concurrent_users": concurrent_users,
            "successful": len(successful),
            "failed": concurrent_users - len(successful),
            "avg_response_ms": round(statistics.mean(times), 2) if times else 0,
            "max_response_ms": round(max(times), 2) if times else 0
        }
        print(f"  ✅ {summary['successful']}/{concurrent_users} succeeded, avg {summary['avg_response_ms']}ms")
        return summary

    async def run_cache_benchmark(self, iterations: int = 5) -> dict:
        """Test cache effectiveness."""
        print(f"\n📊 Running Cache Benchmark ({iterations} iterations)...")

        query = "What is the capital of France?"

        async with httpx.AsyncClient() as client:
            session_id = await self.create_session(client)
            if not session_id:
                return {"error": "Failed to create session"}

            times = []
            for i in range(iterations):
                result = await self.benchmark_single_request(client, session_id, query)
                if result["status_code"] == 200:
                    times.append(result["elapsed_ms"])
                await asyncio.sleep(0.2)

            if len(times) >= 2:
                first_request = times[0]
                subsequent_avg = statistics.mean(times[1:])
                speedup = first_request / subsequent_avg if subsequent_avg > 0 else 1

                result = {
                    "first_request_ms": round(first_request, 2),
                    "subsequent_avg_ms": round(subsequent_avg, 2),
                    "speedup_factor": round(speedup, 2),
                    "cache_effective": speedup > 1.5
                }
                print(
                    f"  ✅ First: {result['first_request_ms']}ms, Cached: {result['subsequent_avg_ms']}ms, Speedup: {result['speedup_factor']}x")
                return result

        return {"error": "Insufficient data"}

    async def run_all_benchmarks(self) -> dict:
        """Run complete benchmark suite."""
        print("=" * 60)
        print("🚀 AI Agent API Performance Benchmark")
        print("=" * 60)
        print(f"Target: {self.base_url}")

        # Health check
        if not await self.health_check():
            return {"error": "API not accessible"}
        print("✅ API Health Check Passed\n")

        # Run benchmarks
        self.results["benchmarks"]["response_time"] = await self.run_response_time_benchmark()
        self.results["benchmarks"]["throughput"] = await self.run_throughput_benchmark(duration_seconds=10)
        self.results["benchmarks"]["concurrent"] = await self.run_concurrent_benchmark(concurrent_users=5)
        self.results["benchmarks"]["cache"] = await self.run_cache_benchmark()

        return self.results

    def save_results(self, output_dir: str = "benchmarks/results") -> str:
        """Save results to JSON file."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/benchmark_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)

        return filename

    def print_summary(self):
        """Print benchmark summary."""
        print("\n" + "=" * 60)
        print("📊 BENCHMARK SUMMARY")
        print("=" * 60)

        benchmarks = self.results.get("benchmarks", {})

        # Response Time Summary
        if "response_time" in benchmarks and "error" not in benchmarks["response_time"]:
            print("\n⏱️  Response Times:")
            for query_type, data in benchmarks["response_time"].items():
                print(f"   {query_type}: {data['avg_ms']}ms avg ({data['strategies']})")

        # Throughput
        if "throughput" in benchmarks and "error" not in benchmarks["throughput"]:
            tp = benchmarks["throughput"]
            print(f"\n🚀 Throughput: {tp['requests_per_second']} req/s")

        # Concurrent
        if "concurrent" in benchmarks and "error" not in benchmarks["concurrent"]:
            cc = benchmarks["concurrent"]
            print(f"\n👥 Concurrent ({cc['concurrent_users']} users): {cc['avg_response_ms']}ms avg")

        # Cache
        if "cache" in benchmarks and "error" not in benchmarks["cache"]:
            cache = benchmarks["cache"]
            status = "✅ Effective" if cache.get("cache_effective") else "⚠️ Limited"
            print(f"\n💾 Cache: {cache['speedup_factor']}x speedup ({status})")

        print("\n" + "=" * 60)


async def main():
    parser = argparse.ArgumentParser(description="AI Agent API Benchmark")
    parser.add_argument("--host", default="localhost", help="API host")
    parser.add_argument("--port", default=8000, type=int, help="API port")
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}/api/v1"

    benchmark = APIBenchmark(base_url)
    await benchmark.run_all_benchmarks()

    # Save and print results
    filename = benchmark.save_results()
    benchmark.print_summary()
    print(f"\n📁 Results saved to: {filename}")


if __name__ == "__main__":
    asyncio.run(main())