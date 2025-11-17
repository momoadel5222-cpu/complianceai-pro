import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def get_supabase_client():
    """Returns Supabase client for database operations"""
    return supabase

def test_connection():
    """Test database connection"""
    try:
        result = supabase.table('sanctions_list').select("*", count='exact').limit(1).execute()
        return {"status": "connected", "records": result.count}
    except Exception as e:
        return {"status": "error", "message": str(e)}
