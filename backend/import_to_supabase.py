#!/usr/bin/env python3
"""
Import sanctions CSV to Supabase using REST API
"""
import os
import csv
import requests
import json

# You need your Supabase URL and ANON KEY
SUPABASE_URL = "https://qwacsyreyuhhlvzcwhnw.supabase.co"
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_KEY:
    print("❌ SUPABASE_KEY not set!")
    print("\nGet your anon key from:")
    print("https://supabase.com/dashboard/project/qwacsyreyuhhlvzcwhnw/settings/api")
    print("\nThen run:")
    print("export SUPABASE_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7e'")
    exit(1)

print("=" * 60)
print("📤 Importing Sanctions to Supabase via REST API")
print("=" * 60)

# Read CSV
print("\n📖 Reading CSV file...")
csv_file = 'sanctions_data/combined_sanctions_complete.csv'

records = []
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        records.append({
            'entity_name': row['entity_name'],
            'entity_type': row['entity_type'],
            'list_source': row['list_source'],
            'program': row['program'],
            'jurisdiction': row['jurisdiction'],
            'remarks': row['remarks'],
            'is_pep': row['is_pep'] == 'True'
        })

print(f"✅ Read {len(records)} records from CSV")

# Insert in batches via REST API
print("\n💾 Inserting into Supabase...")
headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

batch_size = 1000  # Supabase REST API can handle larger batches
total = len(records)
failed = 0

for i in range(0, total, batch_size):
    batch = records[i:i+batch_size]
    
    try:
        response = requests.post(
            f'{SUPABASE_URL}/rest/v1/sanctions_list',
            headers=headers,
            json=batch,
            timeout=60
        )
        
        if response.status_code in [200, 201]:
            progress = min(i + batch_size, total)
            print(f"  ✅ Inserted {progress}/{total} records ({progress*100//total}%)")
        else:
            print(f"  ❌ Batch {i}-{i+batch_size} failed: {response.status_code} {response.text[:200]}")
            failed += len(batch)
    except Exception as e:
        print(f"  ❌ Batch {i}-{i+batch_size} error: {e}")
        failed += len(batch)

if failed == 0:
    print("\n✅ All records inserted successfully!")
else:
    print(f"\n⚠️  {failed} records failed to insert")

# Verify via REST API
print("\n📊 Verifying import...")
try:
    # Get counts
    response = requests.get(
        f'{SUPABASE_URL}/rest/v1/sanctions_list?select=is_pep&is_pep=eq.false',
        headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}', 'Prefer': 'count=exact'},
        timeout=30
    )
    sanctions_count = int(response.headers.get('Content-Range', '0/0').split('/')[1])
    
    response = requests.get(
        f'{SUPABASE_URL}/rest/v1/sanctions_list?select=is_pep&is_pep=eq.true',
        headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}', 'Prefer': 'count=exact'},
        timeout=30
    )
    pep_count = int(response.headers.get('Content-Range', '0/0').split('/')[1])
    
    print(f"\n📈 Database Summary:")
    print(f"  - Total sanctions: {sanctions_count:,}")
    print(f"  - Total PEPs: {pep_count:,}")
    print(f"  - Grand Total: {sanctions_count + pep_count:,}")
except Exception as e:
    print(f"⚠️  Could not verify: {e}")

print("\n" + "=" * 60)
print("🎉 Import Complete!")
print("=" * 60)
