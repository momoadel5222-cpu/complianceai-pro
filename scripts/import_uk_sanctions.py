#!/usr/bin/env python3
from supabase import create_client

SUPABASE_URL = 'https://qwacsyreyuhhlvzcwhnw.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzE0MjI3OCwiZXhwIjoyMDc4NzE4Mjc4fQ.aU_goUIiCubKZ8WrATFD3_5-dukdBAHzvNiZ7HuKMbk'
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n" + "="*60)
print("🇬🇧 UK HM TREASURY SANCTIONS")
print("="*60 + "\n")

entities = [
    {'entity_name': 'ALEXANDER LUKASHENKO', 'entity_type': 'individual', 'aliases': ['Lukashenka Alyaksandr'], 'nationalities': ['Belarus'], 'list_source': 'UK', 'program': 'Belarus Sanctions'},
    {'entity_name': 'RAMZAN KADYROV', 'entity_type': 'individual', 'aliases': ['Kadyrov Ramzan Akhmatovich'], 'nationalities': ['Russia'], 'list_source': 'UK', 'program': 'Russia Sanctions'}
]

try:
    supabase.table('sanctions_list').insert(entities).execute()
    print(f"✅ Inserted {len(entities)} UK records")
except Exception as e:
    print(f"❌ Error: {e}")
print("="*60 + "\n")
