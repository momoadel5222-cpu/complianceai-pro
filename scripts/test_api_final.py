#!/usr/bin/env python3
"""Test ComplianceAI API - /api/screen endpoint"""
import requests
import json
from datetime import datetime

API_URL = "https://complianceai-backend-7n50.onrender.com"
print("=" * 70)
print("🧪 TESTING COMPLIANCEAI PRO API (583K+ RECORDS)")
print("=" * 70)

def log_test(title, result, status=200):
    print(f"\n{title}")
    print(f"   Status: {status}")
    if result: print(f"   Response: {json.dumps(result, indent=2)[:500]}...")
    print()

# 1️⃣ HEALTH CHECK
print("1️⃣ Testing Health...")
try:
    r = requests.get(f"{API_URL}/api/health", timeout=10)
    log_test("Health Check", r.json(), r.status_code)
except Exception as e:
    print(f"   ❌ Health failed: {e}")

# 2️⃣ STATS
print("2️⃣ Testing Stats...")
try:
    r = requests.get(f"{API_URL}/api/stats", timeout=10)
    log_test("Stats", r.json(), r.status_code)
except Exception as e:
    print(f"   ❌ Stats failed: {e}")

# 3️⃣ REAL SCREENING TESTS
tests = [
    ("Vladimir Putin", "High-profile test"),
    ("Dušan Muňko", "DB sample match"),
    ("Trump", "Common name"),
    ("OpenSanctions PEPs", "Source test")
]

for name, desc in tests:
    print(f"3️⃣ Testing Screening: {name}")
    try:
        r = requests.post(
            f"{API_URL}/api/screen",
            json={"name": name},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        result = r.json()
        matches = len(result.get("matches", []))
        log_test(f"Screening '{name}' ({desc})", result, r.status_code)
        print(f"   🔥 MATCHES FOUND: {matches}")
    except Exception as e:
        print(f"   ❌ Screening failed: {e}")

print("=" * 70)
print("🎉 API TESTING COMPLETE!")
print("=" * 70)
