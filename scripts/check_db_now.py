#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(
    host='complianceai-prod-18493.j77.aws-eu-central-1.cockroachlabs.cloud',
    port=26257, user='ahmed', 
    password='p3OjZDFd2pJE-0O9qj0aPQ',
    database='defaultdb', sslmode='require'
)
cur = conn.cursor()

# Count records
cur.execute("SELECT COUNT(*) FROM sanctions_list")
count = cur.fetchone()[0]
print(f"Current records in DB: {count:,}")

# Check if old data exists
cur.execute("SELECT name, source FROM sanctions_list LIMIT 5")
print("\nSample records:")
for row in cur.fetchall():
    print(f"  - {row[0]:50s} [{row[1]}]")

cur.close()
conn.close()
