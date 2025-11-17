#!/usr/bin/env python3
"""Test ComplianceAI API"""

import requests
import json
from datetime import datetime

def log(msg):
    print(f"{datetime.now().strftime('%H:%M:%S')} | {msg}")

API_URL = "https://complianceai-backend-7n50.onrender.com"

log("="*70)
log("🧪 TESTING COMPLIANCEAI API")
log("="*70)

# Test 1: Health Check
log("\n1️⃣ Testing Health Endpoint...")
try:
    r = requests.get(f"{API_URL}/health", timeout=10)
    log(f"   Status: {r.status_code}")
    log(f"   Response: {r.json()}")
except Exception as e:
    log(f"   ❌ Failed: {e}")

# Test 2: Root Endpoint
log("\n2️⃣ Testing Root Endpoint...")
try:
    r = requests.get(f"{API_URL}/", timeout=10)
    log(f"   Status: {r.status_code}")
    if r.status_code == 200:
        log(f"   ✅ API is responding!")
except Exception as e:
    log(f"   ❌ Failed: {e}")

# Test 3: Check Database Count
log("\n3️⃣ Testing Database Status...")
try:
    r = requests.get(f"{API_URL}/api/stats", timeout=10)
    if r.status_code == 200:
        stats = r.json()
        log(f"   ✅ Records in DB: {stats.get('total_records', 'N/A'):,}")
    else:
        log(f"   Status: {r.status_code}")
except Exception as e:
    log(f"   ⚠️  No stats endpoint (normal)")

# Test 4: Compliance Check with Known Name
log("\n4️⃣ Testing Compliance Check...")
test_names = [
    "Vladimir Putin",
    "Osama bin Laden", 
    "John Smith",
    "Donald Trump"
]

for name in test_names:
    log(f"\n   Testing: {name}")
    try:
        r = requests.post(
            f"{API_URL}/api/check-compliance",
            json={"name": name, "country": "", "dateOfBirth": ""},
            timeout=15
        )
        
        if r.status_code == 200:
            result = r.json()
            risk = result.get('riskLevel', 'N/A')
            score = result.get('matchScore', 0)
            matches = len(result.get('matches', []))
            
            log(f"   ✅ Status: {r.status_code}")
            log(f"      Risk: {risk} | Score: {score} | Matches: {matches}")
            
            if matches > 0:
                top = result['matches'][0]
                log(f"      Top Match: {top.get('name', 'N/A')} ({top.get('score', 0):.1f}%)")
        else:
            log(f"   ⚠️  Status: {r.status_code}")
            log(f"      {r.text[:200]}")
            
    except Exception as e:
        log(f"   ❌ Failed: {e}")

log("\n" + "="*70)
log("🎉 API Testing Complete!")
log("="*70)
