#!/usr/bin/env python3
"""
GovScheme Advisor — API Latency Benchmark

Sends 50 sequential mock requests to the /api/recommend/benchmark endpoint
and computes the Average End-to-End API Latency.

Usage:
    1. Start the FastAPI server: cd backend && uvicorn main:app --port 8000
    2. Run this script: python test_latency.py

Results are saved to backend/metrics_latency_results.txt
"""

import os
import sys
import time
import json
import statistics

# Try httpx first (in requirements), fallback to urllib
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    import urllib.request
    import urllib.error

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

API_URL = os.getenv("API_URL", "http://localhost:8000/api/recommend/benchmark")
NUM_REQUESTS = 50

# Diverse mock profiles to rotate through
MOCK_PROFILES = [
    {"gender": "male", "age": 35, "caste_category": "obc", "is_farmer": True,
     "annual_family_income": 80000, "state": "Uttar Pradesh", "area_type": "rural", "bpl_status": True},
    {"gender": "female", "age": 20, "caste_category": "sc", "is_student": True,
     "annual_family_income": 150000, "state": "Bihar", "area_type": "urban"},
    {"gender": "female", "age": 55, "caste_category": "general", "is_widow": True,
     "annual_family_income": 60000, "state": "Rajasthan", "area_type": "rural", "bpl_status": True},
    {"gender": "male", "age": 65, "caste_category": "st", "is_senior_citizen": True,
     "annual_family_income": 50000, "state": "Jharkhand", "area_type": "rural", "bpl_status": True},
    {"gender": "male", "age": 28, "caste_category": "general", "employment_status": "unemployed",
     "annual_family_income": 200000, "state": "Maharashtra", "area_type": "urban"},
    {"gender": "female", "age": 25, "caste_category": "obc", "is_student": True,
     "annual_family_income": 90000, "state": "Tamil Nadu", "area_type": "urban", "bpl_status": True},
    {"gender": "male", "age": 45, "caste_category": "sc", "is_farmer": True,
     "annual_family_income": 70000, "state": "Madhya Pradesh", "area_type": "rural", "bpl_status": True},
    {"gender": "female", "age": 30, "caste_category": "sc", "employment_status": "self_employed",
     "annual_family_income": 150000, "state": "Karnataka", "area_type": "urban"},
    {"gender": "male", "age": 22, "caste_category": "ews", "is_student": True,
     "annual_family_income": 200000, "state": "Delhi", "area_type": "urban"},
    {"gender": "female", "age": 70, "caste_category": "sc", "is_widow": True, "bpl_status": True,
     "annual_family_income": 40000, "state": "Chhattisgarh", "area_type": "rural"},
]


def send_request_httpx(profile):
    """Send a POST request using httpx."""
    t_start = time.time()
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(API_URL, json=profile)
        resp.raise_for_status()
        data = resp.json()
    t_end = time.time()
    return (t_end - t_start) * 1000, data.get("timing_ms", {})


def send_request_urllib(profile):
    """Fallback: send a POST request using urllib."""
    t_start = time.time()
    body = json.dumps(profile).encode('utf-8')
    req = urllib.request.Request(API_URL, data=body,
                                headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    t_end = time.time()
    return (t_end - t_start) * 1000, data.get("timing_ms", {})


def main():
    send_fn = send_request_httpx if HAS_HTTPX else send_request_urllib

    print("=" * 70)
    print("API LATENCY BENCHMARK — GovScheme Advisor")
    print("=" * 70)
    print(f"  Endpoint:  {API_URL}")
    print(f"  Requests:  {NUM_REQUESTS}")
    print(f"  HTTP lib:  {'httpx' if HAS_HTTPX else 'urllib'}")
    print()

    latencies = []
    server_timings = []
    errors = 0

    for i in range(NUM_REQUESTS):
        profile = MOCK_PROFILES[i % len(MOCK_PROFILES)]
        try:
            latency_ms, server_timing = send_fn(profile)
            latencies.append(latency_ms)
            if server_timing:
                server_timings.append(server_timing)
            status = "✓"
        except Exception as e:
            errors += 1
            status = f"✗ ({e})"
            latency_ms = 0.0

        print(f"  [{i+1:3d}/{NUM_REQUESTS}] {latency_ms:8.2f} ms  {status}")

    print()
    print("  " + "─" * 60)

    if not latencies:
        print("  ❌ All requests failed. Is the server running?")
        return

    avg_latency = statistics.mean(latencies)
    med_latency = statistics.median(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)
    p95_latency = sorted(latencies)[int(0.95 * len(latencies))]
    std_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0.0

    print(f"  Successful Requests:    {len(latencies)}/{NUM_REQUESTS}")
    print(f"  Failed Requests:        {errors}")
    print(f"  Average Latency:        {avg_latency:.2f} ms")
    print(f"  Median Latency:         {med_latency:.2f} ms")
    print(f"  Min Latency:            {min_latency:.2f} ms")
    print(f"  Max Latency:            {max_latency:.2f} ms")
    print(f"  P95 Latency:            {p95_latency:.2f} ms")
    print(f"  Std Dev:                {std_latency:.2f} ms")

    # Server-side timing averages
    if server_timings:
        avg_db = statistics.mean([t.get("db_fetch", 0) for t in server_timings])
        avg_idx = statistics.mean([t.get("tfidf_indexing", 0) for t in server_timings])
        avg_rec = statistics.mean([t.get("recommendation_scoring", 0) for t in server_timings])
        avg_srv = statistics.mean([t.get("total_end_to_end", 0) for t in server_timings])
        print(f"\n  Server-Side Breakdown (avg):")
        print(f"    DB Fetch:             {avg_db:.2f} ms")
        print(f"    TF-IDF Indexing:      {avg_idx:.2f} ms")
        print(f"    Recommendation:       {avg_rec:.2f} ms")
        print(f"    Server Total:         {avg_srv:.2f} ms")

    print("  " + "─" * 60)

    # Save results
    out_path = os.path.join(os.path.dirname(__file__), "metrics_latency_results.txt")
    with open(out_path, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("API LATENCY METRICS — GovScheme Advisor\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Endpoint:               {API_URL}\n")
        f.write(f"Total Requests:         {NUM_REQUESTS}\n")
        f.write(f"Successful Requests:    {len(latencies)}\n")
        f.write(f"Failed Requests:        {errors}\n\n")
        f.write(f"Average Latency:        {avg_latency:.2f} ms\n")
        f.write(f"Median Latency:         {med_latency:.2f} ms\n")
        f.write(f"Min Latency:            {min_latency:.2f} ms\n")
        f.write(f"Max Latency:            {max_latency:.2f} ms\n")
        f.write(f"P95 Latency:            {p95_latency:.2f} ms\n")
        f.write(f"Std Dev:                {std_latency:.2f} ms\n")
        if server_timings:
            f.write(f"\nServer-Side Breakdown (avg):\n")
            f.write(f"  DB Fetch:             {avg_db:.2f} ms\n")
            f.write(f"  TF-IDF Indexing:      {avg_idx:.2f} ms\n")
            f.write(f"  Recommendation:       {avg_rec:.2f} ms\n")
            f.write(f"  Server Total:         {avg_srv:.2f} ms\n")
        f.write(f"\nPer-Request Latencies (ms):\n")
        for i, lat in enumerate(latencies):
            f.write(f"  Request {i+1:3d}: {lat:.2f}\n")
        f.write("\n")

    print(f"\n  ✅ Latency metrics saved to: {out_path}")


if __name__ == "__main__":
    main()
