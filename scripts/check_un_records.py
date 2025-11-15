#!/usr/bin/env python3
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv('/workspaces/complianceai-pro/backend/.env')

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_ANON_KEY')
)

print("\n" + "="*70)
print("CHECKING UN RECORDS IN DATABASE")
print("="*70 + "\n")

result = supabase.table('sanctions_list').select('*').eq('list_source', 'UN').limit(5).execute()

print(f"Found {len(result.data)} UN records (showing first 5):\n")

for i, record in enumerate(result.data, 1):
    print(f"{i}. {record.get('entity_name')} ({record.get('entity_type')})")
    print(f"   ID: {record.get('entity_id')}")
    print(f"   Source: {record.get('list_source')}")
    print(f"   First name: {record.get('first_name')}")
    print(f"   Last name: {record.get('last_name')}")
    print()

count_result = supabase.table('sanctions_list').select('*', count='exact').eq('list_source', 'UN').execute()
print(f"Total UN records in database: {count_result.count}")

null_result = supabase.table('sanctions_list').select('*', count='exact').is_('list_source', 'null').execute()
print(f"Records with NULL list_source: {null_result.count}")

print("\n" + "="*70 + "\n")
