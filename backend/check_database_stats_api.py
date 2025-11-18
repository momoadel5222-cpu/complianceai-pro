#!/usr/bin/env python3
"""
Check database statistics via Supabase REST API
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://qwacsyreyuhhlvzcwhnw.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_KEY:
    print("❌ SUPABASE_KEY not set!")
    exit(1)

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Prefer': 'count=exact'
}

print("=" * 60)
print("📊 Database Statistics (via REST API)")
print("=" * 60)

try:
    # Total records
    response = requests.get(
        f'{SUPABASE_URL}/rest/v1/sanctions_list?select=id',
        headers=headers,
        timeout=30
    )
    total = int(response.headers.get('Content-Range', '0/0').split('/')[1])
    print(f"\n📁 Total Records: {total:,}")
    
    # PEPs count
    response = requests.get(
        f'{SUPABASE_URL}/rest/v1/sanctions_list?select=id&is_pep=eq.true',
        headers=headers,
        timeout=30
    )
    peps = int(response.headers.get('Content-Range', '0/0').split('/')[1])
    print(f"👔 PEPs: {peps:,}")
    
    # Sanctions count
    sanctions = total - peps
    print(f"⚠️  Sanctions: {sanctions:,}")
    
    # Get sample PEPs
    print(f"\n🌟 Sample PEPs:")
    response = requests.get(
        f'{SUPABASE_URL}/rest/v1/sanctions_list?select=entity_name,program,nationalities,list_source&is_pep=eq.true&limit=10',
        headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'},
        timeout=30
    )
    
    if response.status_code == 200:
        peps_data = response.json()
        for i, pep in enumerate(peps_data, 1):
            nats = ', '.join(pep.get('nationalities', [])) if pep.get('nationalities') else 'N/A'
            print(f"   {i}. {pep['entity_name']}")
            print(f"      Program: {pep['program']}")
            print(f"      Source: {pep['list_source']}")
            print(f"      Nationalities: {nats}")
            print()
    
    # Check for Mostafa Madbouly specifically
    print(f"\n🔍 Searching for Mostafa Madbouly:")
    response = requests.get(
        f'{SUPABASE_URL}/rest/v1/sanctions_list?entity_name=ilike.*Madbouly*',
        headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'},
        timeout=30
    )
    
    if response.status_code == 200:
        results = response.json()
        if results:
            print(f"✅ Found {len(results)} match(es):")
            for result in results:
                print(f"   - {result['entity_name']}")
                print(f"     Program: {result['program']}")
                print(f"     Aliases: {', '.join(result.get('aliases', []))}")
        else:
            print("❌ Not found in database")
    
    print("\n" + "=" * 60)
    print("✅ Statistics Complete!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
