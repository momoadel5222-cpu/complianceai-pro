#!/usr/bin/env python3
"""
Test if Mostafa Madbouly exists in database
"""

from supabase import create_client

SUPABASE_URL = "https://qwacsyreyuhhlvzcwhnw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7es"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🔍 Searching for: Mostafa Madbouly\n")
print("=" * 60)

# Test 1: Exact match
print("\n1️⃣ Testing EXACT match:")
result = supabase.table('sanctions_list').select('*').eq('entity_name', 'Mostafa Madbouly').execute()
print(f"   Results: {len(result.data)} matches")
if result.data:
    print(f"   ✅ Found: {result.data[0]['entity_name']}")

# Test 2: Case-insensitive match
print("\n2️⃣ Testing CASE-INSENSITIVE match:")
result = supabase.table('sanctions_list').select('*').ilike('entity_name', 'mostafa madbouly').execute()
print(f"   Results: {len(result.data)} matches")
if result.data:
    print(f"   ✅ Found: {result.data[0]['entity_name']}")

# Test 3: Partial match (contains)
print("\n3️⃣ Testing PARTIAL match (contains 'Madbouly'):")
result = supabase.table('sanctions_list').select('*').ilike('entity_name', '%madbouly%').execute()
print(f"   Results: {len(result.data)} matches")
if result.data:
    for item in result.data[:3]:
        print(f"   ✅ Found: {item['entity_name']} ({item['list_source']})")

# Test 4: Search with PEP filter
print("\n4️⃣ Testing with PEP FILTER:")
result = supabase.table('sanctions_list').select('*').ilike('entity_name', '%madbouly%').eq('is_pep', True).execute()
print(f"   Results: {len(result.data)} matches")
if result.data:
    for item in result.data[:3]:
        print(f"   ✅ Found: {item['entity_name']} (PEP: {item['is_pep']})")

# Test 5: Check exact name variations
print("\n5️⃣ Testing NAME VARIATIONS:")
variations = [
    'Mostafa Madbouly',
    'Mustafa Madbouly', 
    'Mostafa Kamal Madbouly',
    'Madbouly'
]

for name in variations:
    result = supabase.table('sanctions_list').select('*').ilike('entity_name', f'%{name}%').execute()
    if result.data:
        print(f"   ✅ '{name}': {len(result.data)} matches - {result.data[0]['entity_name']}")
    else:
        print(f"   ❌ '{name}': No matches")

print("\n" + "=" * 60)
