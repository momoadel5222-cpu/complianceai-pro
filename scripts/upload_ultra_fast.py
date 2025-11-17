#!/usr/bin/env python3
import pandas as pd, psycopg2, time
from psycopg2.extras import execute_values

print("🚀 ULTRA-FAST UPLOAD (10K/s) STARTING!")

DB_PARAMS = {
    'host': 'complianceai-prod-18493.j77.aws-eu-central-1.cockroachlabs.cloud',
    'port': 26257, 'user': 'ahmed', 'password': 'p3OjZDFd2pJE-0O9qj0aPQ',
    'database': 'defaultdb', 'sslmode': 'require'
}

conn = psycopg2.connect(**DB_PARAMS)
cur = conn.cursor()

start = time.time()
total = 0

for chunk in pd.read_csv('cleaned_sanctions.csv', chunksize=100000):  # 100K chunks!
    # ULTRA-SIMPLE MAPPING (NO PARSING!)
    data = [
        (str(row['name']), 'individual', str(row.get('source', 'Unknown'))) 
        for _, row in chunk.iterrows()
    ]
    
    # execute_values = 10X FASTER!
    execute_values(cur, """
        INSERT INTO sanctions_list (entity_name, entity_type, list_source) 
        VALUES %s
    """, data, template=None, page_size=10000)
    
    conn.commit()
    total += len(chunk)
    elapsed = time.time() - start
    rate = total / elapsed
    eta_min = (2332097 - total) / rate / 60
    
    print(f"⚡ {total:,} | {rate:6.0f}/s | ETA {eta_min:4.1f}m")
    
print(f"✅ ULTRA-FAST COMPLETE! {total:,} records!")
cur.close(); conn.close()
