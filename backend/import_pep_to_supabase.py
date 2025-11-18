#!/usr/bin/env python3
"""
Import PEP data to Supabase
"""
import os
import csv
import requests
import json

SUPABASE_URL = "https://qwacsyreyuhhlvzcwhnw.supabase.co"
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_KEY:
    print("❌ SUPABASE_KEY not set!")
    print("\nGet your anon key from:")
    print("https://supabase.com/dashboard/project/qwacsyreyuhhlvzcwhnw/settings/api")
    print("\nThen run:")
    print("export SUPABASE_KEY='your_key_here'")
    print("python3 import_pep_to_supabase.py")
    exit(1)

print("=" * 60)
print("📤 Importing PEP Data to Supabase")
print("=" * 60)

# Read PEP CSV
print("\n📖 Reading PEP CSV file...")
csv_file = 'data/pep_data.csv'

records = []
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Convert pipe-separated values to arrays
        aliases = row['aliases'].split('|') if row['aliases'] else []
        nationalities = row['nationalities'].split('|') if row['nationalities'] else []
        
        records.append({
            'entity_name': row['entity_name'],
            'entity_type': row['entity_type'],
            'list_source': row['list_source'],
            'program': row['program'],
            'nationalities': nationalities,
            'aliases': aliases,
            'remarks': row.get('remarks', ''),
            'is_pep': True
        })

print(f"✅ Read {len(records)} PEP records from CSV")

# Insert via Supabase REST API
print("\n💾 Inserting into Supabase...")
headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

try:
    response = requests.post(
        f'{SUPABASE_URL}/rest/v1/sanctions_list',
        headers=headers,
        json=records,
        timeout=60
    )
    
    if response.status_code in [200, 201]:
        print(f"✅ Inserted {len(records)} PEP records successfully")
    else:
        print(f"❌ Insert failed: {response.status_code}")
        print(f"Response: {response.text}")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Verify
print("\n📊 Verifying import...")
try:
    response = requests.get(
        f'{SUPABASE_URL}/rest/v1/sanctions_list?entity_name=ilike.*Madbouly*',
        headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'},
        timeout=30
    )
    
    if response.status_code == 200:
        results = response.json()
        if results:
            print(f"\n✅ Found Mostafa Madbouly in database:")
            for record in results:
                print(f"    {record['entity_name']} - {record['program']}")
                print(f"    Aliases: {', '.join(record.get('aliases', []))}")
        else:
            print("\n⚠️  Mostafa Madbouly not found")
    else:
        print(f"⚠️  Verification failed: {response.status_code}")
except Exception as e:
    print(f"⚠️  Could not verify: {e}")

print("\n" + "=" * 60)
print("🎉 PEP Import Complete!")
print("=" * 60)
