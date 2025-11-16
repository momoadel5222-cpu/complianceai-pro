from supabase import create_client

SUPABASE_URL = "https://qwacsyreyuhhlvzcwhnw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7es"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🇪🇬 Searching for Egyptian PEPs in database...\n")

# Search for Egyptian PEPs
result = supabase.table('sanctions_list')\
    .select('entity_name, position, jurisdiction')\
    .eq('is_pep', True)\
    .contains('nationalities', ['eg'])\
    .limit(20)\
    .execute()

if result.data:
    print(f"✅ Found {len(result.data)} Egyptian PEPs (showing first 20):\n")
    for i, pep in enumerate(result.data, 1):
        name = pep.get('entity_name', 'N/A')
        position = pep.get('position', 'N/A')
        jurisdiction = pep.get('jurisdiction', 'N/A')
        print(f"{i}. {name}")
        print(f"   Position: {position}")
        print(f"   Country: {jurisdiction}\n")
else:
    print("❌ No Egyptian PEPs found with 'eg' in nationalities")
    print("Trying alternative search...")
    
    # Try searching by jurisdiction
    result2 = supabase.table('sanctions_list')\
        .select('entity_name, position, jurisdiction')\
        .eq('is_pep', True)\
        .ilike('jurisdiction', '%eg%')\
        .limit(10)\
        .execute()
    
    if result2.data:
        print(f"\n✅ Found Egyptian PEPs by jurisdiction:\n")
        for pep in result2.data:
            print(f"- {pep.get('entity_name')} ({pep.get('position', 'N/A')})")
