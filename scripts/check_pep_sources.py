from supabase import create_client

SUPABASE_URL = "https://qwacsyreyuhhlvzcwhnw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7es"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🔍 Analyzing PEP Database...\n")

# Check total PEPs
peps = supabase.table('sanctions_list').select('*', count='exact').eq('is_pep', True).execute()
print(f"📊 Total PEPs: {peps.count}")

# Check sources
sources = supabase.table('sanctions_list').select('list_source').eq('is_pep', True).execute()
source_counts = {}
for item in sources.data:
    source = item.get('list_source', 'Unknown')
    source_counts[source] = source_counts.get(source, 0) + 1

print(f"\n📋 PEP Sources:")
for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  • {source}: {count:,} entities")

# Check MENA countries
print(f"\n🌍 MENA Region PEPs:")
mena_countries = ['Egypt', 'Saudi Arabia', 'UAE', 'Jordan', 'Lebanon', 'Kuwait', 'Qatar', 'Bahrain', 'Oman', 'Iraq', 'Syria', 'Yemen', 'Palestine', 'Morocco', 'Tunisia', 'Algeria', 'Libya']

for country in mena_countries:
    result = supabase.table('sanctions_list')\
        .select('entity_name', count='exact')\
        .eq('is_pep', True)\
        .or_(f'jurisdiction.ilike.%{country}%,nationalities.cs.{{"{country}"}}').execute()
    
    if result.count > 0:
        print(f"  • {country}: {result.count} PEPs")

# Sample some PEP names
print(f"\n📝 Sample PEP Names:")
samples = supabase.table('sanctions_list')\
    .select('entity_name, position, jurisdiction')\
    .eq('is_pep', True)\
    .limit(10).execute()

for pep in samples.data:
    print(f"  • {pep['entity_name']} - {pep.get('position', 'N/A')} ({pep.get('jurisdiction', 'N/A')})")
