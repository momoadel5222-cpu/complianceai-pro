#!/usr/bin/env python3
from supabase import create_client

SUPABASE_URL = 'https://qwacsyreyuhhlvzcwhnw.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzE0MjI3OCwiZXhwIjoyMDc4NzE4Mjc4fQ.aU_goUIiCubKZ8WrATFD3_5-dukdBAHzvNiZ7HuKMbk'
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n" + "="*60)
print("🇪🇺 EU SANCTIONS LIST IMPORTER")
print("="*60 + "\n")

entities = [
    {'entity_name': 'VLADIMIR PUTIN', 'entity_type': 'individual', 'aliases': ['Putin Vladimir Vladimirovich'], 'nationalities': ['Russia'], 'list_source': 'EU', 'program': 'EU Russia Sanctions'},
    {'entity_name': 'SERGEY LAVROV', 'entity_type': 'individual', 'aliases': ['Lavrov Sergey Viktorovich'], 'nationalities': ['Russia'], 'list_source': 'EU', 'program': 'EU Russia Sanctions'},
    {'entity_name': 'ROSNEFT', 'entity_type': 'entity', 'aliases': ['Rosneft Oil Company'], 'nationalities': ['Russia'], 'list_source': 'EU', 'program': 'EU Russia Sanctions'}
]

try:
    supabase.table('sanctions_list').insert(entities).execute()
    print(f"✅ Inserted {len(entities)} EU records")
except Exception as e:
    print(f"❌ Error: {e}")
print("="*60 + "\n")
