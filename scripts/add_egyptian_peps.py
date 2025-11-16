from supabase import create_client
import sys
sys.path.append('../backend')

SUPABASE_URL = "https://qwacsyreyuhhlvzcwhnw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7es"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

egyptian_officials = [
    {
        "entity_name": "Abdel Fattah el-Sisi",
        "entity_type": "individual",
        "list_source": "Egypt-Government-PEP",
        "program": "Politically Exposed Person",
        "is_pep": True,
        "pep_level": "direct",
        "position": "President of Egypt",
        "jurisdiction": "Egypt",
        "nationalities": ["EG", "Egypt"]
    },
    {
        "entity_name": "Mostafa Madbouly",
        "entity_type": "individual",
        "list_source": "Egypt-Government-PEP",
        "program": "Politically Exposed Person",
        "is_pep": True,
        "pep_level": "direct",
        "position": "Prime Minister of Egypt",
        "jurisdiction": "Egypt",
        "nationalities": ["EG", "Egypt"]
    },
    {
        "entity_name": "Sameh Shoukry",
        "entity_type": "individual",
        "list_source": "Egypt-Government-PEP",
        "program": "Politically Exposed Person",
        "is_pep": True,
        "pep_level": "direct",
        "position": "Former Foreign Minister of Egypt, Former Deputy Prime Minister",
        "jurisdiction": "Egypt",
        "nationalities": ["EG", "Egypt"]
    },
    {
        "entity_name": "Abdel Fattah Saeed Hussein Khalil El-Sisi",
        "entity_type": "individual",
        "list_source": "Egypt-Government-PEP",
        "program": "Politically Exposed Person",
        "is_pep": True,
        "pep_level": "direct",
        "position": "President of Egypt (Full Name)",
        "jurisdiction": "Egypt",
        "nationalities": ["EG", "Egypt"],
        "aliases": ["Abdel Fattah el-Sisi", "Al-Sisi", "El-Sisi"]
    }
]

print("🇪🇬 Adding Egyptian government officials to PEP database...")
try:
    result = supabase.table('sanctions_list').insert(egyptian_officials).execute()
    print(f"✅ Successfully added {len(egyptian_officials)} Egyptian officials!")
    print("\nAdded:")
    for official in egyptian_officials:
        print(f"  • {official['entity_name']} - {official['position']}")
except Exception as e:
    print(f"❌ Error: {e}")
