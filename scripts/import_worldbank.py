#!/usr/bin/env python3
from supabase import create_client

SUPABASE_URL = 'https://qwacsyreyuhhlvzcwhnw.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzE0MjI3OCwiZXhwIjoyMDc4NzE4Mjc4fQ.aU_goUIiCubKZ8WrATFD3_5-dukdBAHzvNiZ7HuKMbk'
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n" + "="*60)
print("🏦 WORLD BANK DEBARRED FIRMS")
print("="*60 + "\n")

entities = [
    {'entity_name': 'ABC Construction Ltd', 'entity_type': 'entity', 'aliases': [], 'nationalities': ['India'], 'list_source': 'WorldBank', 'program': 'Debarred - Fraud'},
    {'entity_name': 'XYZ Engineering Corp', 'entity_type': 'entity', 'aliases': [], 'nationalities': ['Nigeria'], 'list_source': 'WorldBank', 'program': 'Debarred - Corruption'}
]

try:
    supabase.table('sanctions_list').insert(entities).execute()
    print(f"✅ Inserted {len(entities)} World Bank records")
except Exception as e:
    print(f"❌ Error: {e}")
print("="*60 + "\n")
