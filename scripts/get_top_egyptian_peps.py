from supabase import create_client

SUPABASE_URL = "https://qwacsyreyuhhlvzcwhnw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7es"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🇪🇬 Top 20 Egyptian PEPs for Testing:\n")
print("=" * 70)

# Get Egyptian PEPs with actual names (not just titles)
result = supabase.table('sanctions_list')\
    .select('entity_name, position, jurisdiction')\
    .eq('is_pep', True)\
    .eq('jurisdiction', 'eg')\
    .order('entity_name')\
    .limit(50)\
    .execute()

# Filter for actual person names (not just titles)
actual_people = []
for pep in result.data:
    name = pep.get('entity_name', '')
    # Skip if it's just a title/position
    if not any(word in name.lower() for word in ['minister', 'ambassador', 'q10']):
        actual_people.append(pep)

print("\n✅ REAL PERSON NAMES (Use these for testing):\n")
for i, pep in enumerate(actual_people[:20], 1):
    print(f"{i}. {pep.get('entity_name')}")

print("\n" + "=" * 70)
print(f"\n📊 Total Egyptian PEPs with actual names: {len(actual_people)}")
print("\n�� Copy any of these names and test them in your screening tool!")
