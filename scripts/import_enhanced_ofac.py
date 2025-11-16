#!/usr/bin/env python3
import json
import os
from supabase import create_client, Client

# Supabase credentials
SUPABASE_URL = "https://qwacsyreyuhhlvzcwhnw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzE0MjI3OCwiZXhwIjoyMDc4NzE4Mjc4fQ.aU_goUIiCubKZ8WrATFD3_5-dukdBAHzvNiZ7HuKMbk"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n" + "="*70)
print("IMPORTING ENHANCED OFAC DATA")
print("="*70 + "\n")

# Load JSON
print("📂 Loading ofac_enhanced.json...")
with open('../data/ofac_enhanced.json', 'r', encoding='utf-8') as f:
    entities = json.load(f)

print(f"   ✓ Loaded {len(entities)} entities\n")

# Clear existing OFAC data
print("🗑️  Clearing old OFAC data...")
result = supabase.table('sanctions_list').delete().eq('list_source', 'OFAC').execute()
print(f"   ✓ Cleared old records\n")

# Import in batches
print("📥 Importing enhanced data...")
batch_size = 100
imported = 0

for i in range(0, len(entities), batch_size):
    batch = entities[i:i+batch_size]
    
    # Prepare records
    records = []
    for entity in batch:
        record = {
            'entity_id': entity.get('entity_id'),
            'entity_name': entity.get('entity_name'),
            'first_name': entity.get('first_name'),
            'middle_name': entity.get('middle_name'),
            'last_name': entity.get('last_name'),
            'entity_type': entity.get('entity_type'),
            'gender': entity.get('gender'),
            'date_of_birth': entity.get('date_of_birth'),
            'date_of_birth_text': entity.get('date_of_birth_text'),
            'place_of_birth': entity.get('place_of_birth'),
            'place_of_birth_country': entity.get('place_of_birth_country'),
            'nationalities': entity.get('nationalities', []),
            'aliases': entity.get('aliases', []),
            'addresses': entity.get('addresses', []),
            'countries': entity.get('countries', []),
            'list_source': 'OFAC',
            'program': entity.get('program'),
            'remarks': entity.get('remarks')
        }
        records.append(record)
    
    # Insert batch
    result = supabase.table('sanctions_list').insert(records).execute()
    imported += len(records)
    
    if (imported % 1000 == 0):
        print(f"   Progress: {imported}/{len(entities)} ({imported/len(entities)*100:.1f}%)")

print(f"\n✅ IMPORT COMPLETE!")
print(f"   Total imported: {imported} entities")
print("="*70 + "\n")
