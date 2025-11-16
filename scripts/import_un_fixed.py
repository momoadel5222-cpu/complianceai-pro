#!/usr/bin/env python3
import json
import re
from supabase import create_client, Client

SUPABASE_URL = 'https://qwacsyreyuhhlvzcwhnw.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzE0MjI3OCwiZXhwIjoyMDc4NzE4Mjc4fQ.aU_goUIiCubKZ8WrATFD3_5-dukdBAHzvNiZ7HuKMbk'

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fix_date_format(date_str):
    """Fix malformed dates like '2015-04-07-04:00' to '2015-04-07'"""
    if not date_str:
        return None
    
    # Extract YYYY-MM-DD from various formats
    match = re.match(r'(\d{4}-\d{2}-\d{2})', str(date_str))
    if match:
        return match.group(1)
    
    return None

print("\n" + "="*70)
print("IMPORTING UN SANCTIONS LIST (FIXED)")
print("="*70 + "\n")

# Clear existing UN data
print("🗑️  Clearing old UN data...")
supabase.table('sanctions_list').delete().eq('list_source', 'UN').execute()
print("   ✓ Cleared\n")

# Load JSON
print("📂 Loading un_enhanced.json...")
with open('/workspaces/complianceai-pro/data/un_enhanced.json', 'r', encoding='utf-8') as f:
    entities = json.load(f)

print(f"   ✓ Loaded {len(entities)} entities\n")

# Import in batches
print("📥 Importing with fixed dates...")
batch_size = 100
imported = 0
errors = 0
skipped = 0

for i in range(0, len(entities), batch_size):
    batch = entities[i:i+batch_size]
    
    # Prepare records with fixed dates
    records = []
    for entity in batch:
        # Fix date fields
        date_listed = fix_date_format(entity.get('date_listed'))
        date_of_birth = fix_date_format(entity.get('date_of_birth'))
        
        record = {
            'entity_id': entity.get('entity_id'),
            'entity_name': entity.get('entity_name'),
            'first_name': entity.get('first_name'),
            'middle_name': entity.get('middle_name'),
            'last_name': entity.get('last_name'),
            'entity_type': entity.get('entity_type'),
            'gender': entity.get('gender'),
            'date_of_birth': date_of_birth,
            'date_of_birth_text': entity.get('date_of_birth_text'),
            'place_of_birth': entity.get('place_of_birth'),
            'place_of_birth_country': entity.get('place_of_birth_country'),
            'nationalities': entity.get('nationalities', []),
            'aliases': entity.get('aliases', []),
            'addresses': entity.get('addresses', []),
            'countries': entity.get('countries', []),
            'list_source': 'UN',
            'program': entity.get('program'),
            'date_listed': date_listed,
            'remarks': entity.get('remarks')
        }
        records.append(record)
    
    # Insert batch
    try:
        result = supabase.table('sanctions_list').insert(records).execute()
        imported += len(records)
        
        if (imported % 1000 == 0):
            print(f"   Progress: {imported}/{len(entities)} ({imported/len(entities)*100:.1f}%)")
    except Exception as e:
        errors += len(records)
        print(f"   ✗ Error at batch {i//batch_size + 1}: {str(e)[:100]}")

print(f"\n{'='*70}")
print(f"✅ IMPORT COMPLETE!")
print(f"   Total entities: {len(entities)}")
print(f"   Successfully imported: {imported}")
print(f"   Errors: {errors}")
print(f"{'='*70}\n")
