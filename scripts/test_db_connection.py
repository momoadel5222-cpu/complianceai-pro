import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

url = os.getenv("COCKROACH_URL")
if not url:
    raise SystemExit("COCKROACH_URL is not set")

print("Using COCKROACH_URL:", url[:80] + ("..." if len(url) > 80 else ""))

engine = create_engine(url)

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("DB OK, SELECT 1 ->", list(result))
