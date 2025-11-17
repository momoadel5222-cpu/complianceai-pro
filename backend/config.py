import os
from dotenv import load_dotenv

load_dotenv()

# Use DATABASE_URL for Supabase (formerly COCKROACH_URL)
DATABASE_URL = os.getenv("DATABASE_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Other config
API_VERSION = "3.0.0"
SERVICE_NAME = "ComplianceAI Pro"
DATABASE_TYPE = "Supabase"
