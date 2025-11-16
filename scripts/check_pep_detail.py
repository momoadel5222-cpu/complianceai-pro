from supabase import create_client

SUPABASE_URL = "https://qwacsyreyuhhlvzcwhnw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7es"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🔍 Detailed PEP Analysis...\n")

# Check all list sources
all_sources = supabase.table('sanctions_list').select('list_source').execute()
source_counts = {}
for item in all_sources.data:
    source = item.get('list_source', 'Unknown')
    source_counts[source] = source_counts.get(source, 0) + 1

print("📋 ALL Sources in Database:")
for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  • {source}: {count:,}")

# Check specific MENA countries
print(f"\n🇪🇬 Egypt PEPs:")
egypt = supabase.table('sanctions_list')\
    .select('entity_name, position, jurisdiction')\
    .eq('is_pep', True)\
    .ilike('jurisdiction', '%Egypt%')\
    .limit(20).execute()

if egypt.data:
    for pep in egypt.data:
        print(f"  • {pep['entity_name']} - {pep.get('position', 'N/A')}")
else:
    print("  ❌ No Egyptian PEPs found!")

print(f"\n🇸🇦 Saudi Arabia PEPs:")
saudi = supabase.table('sanctions_list')\
    .select('entity_name, position')\
    .eq('is_pep', True)\
    .ilike('jurisdiction', '%Saudi%')\
    .limit(10).execute()

if saudi.data:
    for pep in saudi.data:
        print(f"  • {pep['entity_name']} - {pep.get('position', 'N/A')}")
else:
    print("  ❌ No Saudi PEPs found!")

# Sample random PEPs to see what we have
print(f"\n📝 Random Sample of 10 PEPs:")
samples = supabase.table('sanctions_list')\
    .select('entity_name, position, jurisdiction, list_source')\
    .eq('is_pep', True)\
    .limit(10).execute()

for pep in samples.data:
    print(f"  • {pep['entity_name']} ({pep.get('jurisdiction', 'N/A')}) - {pep.get('list_source', 'N/A')}")
