from supabase import create_client

SUPABASE_URL = "https://qwacsyreyuhhlvzcwhnw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7es"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🔍 Searching for KAHANE CHAI...")

# Search in database
result = supabase.table('sanctions_list')\
    .select('entity_name, entity_type, list_source, program')\
    .ilike('entity_name', '%KAHANE%')\
    .execute()

if result.data:
    print(f"✅ Found {len(result.data)} matches:")
    for item in result.data:
        print(f"  - {item['entity_name']} ({item['entity_type']}) - {item['list_source']}")
else:
    print("❌ NOT FOUND in database!")
    print("This might have been lost during the PEP import.")
