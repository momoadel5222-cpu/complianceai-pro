#!/usr/bin/env python3
import os, time, pandas as pd, psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime

def log(msg):
    print(f"{datetime.now().strftime('%H:%M:%S')} | {msg}")

BATCH_SIZE = 5000
CONN = {
    'host': 'complianceai-prod-18493.j77.aws-eu-central-1.cockroachlabs.cloud',
    'port': 26257,
    'user': 'ahmed',
    'password': 'p3OjZDFd2pJE-0O9qj0aPQ',
    'database': 'defaultdb',
    'sslmode': 'require'
}

log("="*70)
log("🚀 UPLOADING TO COCKROACHDB")
log("="*70)

# Test connection
log("🔌 Testing connection...")
try:
    conn = psycopg2.connect(**CONN)
    cur = conn.cursor()
    cur.execute("SELECT 1")
    log("✅ Connected!\n")
    cur.close()
    conn.close()
except Exception as e:
    log(f"❌ Connection failed: {e}")
    exit(1)

# Create table if not exists
log("🏗️  Creating table if needed...")
conn = psycopg2.connect(**CONN)
cur = conn.cursor()

create_table_sql = """
CREATE TABLE IF NOT EXISTS sanctions_list (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id TEXT,
    name TEXT NOT NULL,
    entity_type TEXT,
    source TEXT,
    country TEXT,
    aliases TEXT,
    dates_of_birth TEXT,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sanctions_name ON sanctions_list(name);
CREATE INDEX IF NOT EXISTS idx_sanctions_entity_id ON sanctions_list(entity_id);
CREATE INDEX IF NOT EXISTS idx_sanctions_source ON sanctions_list(source);
"""

cur.execute(create_table_sql)
conn.commit()
log("✅ Table ready\n")

# Check existing data
cur.execute("SELECT COUNT(*) FROM sanctions_list")
current = cur.fetchone()[0]
log(f"📊 Current database: {current:,} records")

if current > 0:
    resp = input("\n⚠️  Clear existing data? (y/n): ")
    if resp.lower() == 'y':
        log("🗑️  Clearing...")
        cur.execute("TRUNCATE TABLE sanctions_list")
        conn.commit()
        log("✅ Cleared\n")
    else:
        log("✅ Keeping existing data\n")

cur.close()
conn.close()

# Load CSV
log("📂 Loading cleaned_sanctions.csv...")
if not os.path.exists('cleaned_sanctions.csv'):
    log("❌ File not found!")
    exit(1)

df = pd.read_csv('cleaned_sanctions.csv', low_memory=False)
log(f"✅ Loaded {len(df):,} records\n")

# Upload
log(f"⬆️  Uploading in batches of {BATCH_SIZE:,}...")
log("="*70)

insert_sql = """
    INSERT INTO sanctions_list 
    (entity_id, name, entity_type, source, country, aliases, dates_of_birth, raw_data)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
"""

conn = psycopg2.connect(**CONN)
conn.autocommit = False
cur = conn.cursor()

total = len(df)
uploaded = 0
start = time.time()

try:
    for i in range(0, len(df), BATCH_SIZE):
        batch = df.iloc[i:i+BATCH_SIZE]
        
        # Prepare batch data
        batch_data = []
        for _, row in batch.iterrows():
            batch_data.append((
                str(row.get('entity_id', ''))[:255] if pd.notna(row.get('entity_id')) else '',
                str(row.get('name', ''))[:500] if pd.notna(row.get('name')) else '',
                str(row.get('entity_type', ''))[:100] if pd.notna(row.get('entity_type')) else '',
                str(row.get('source', ''))[:100] if pd.notna(row.get('source')) else '',
                str(row.get('country', ''))[:500] if pd.notna(row.get('country')) else '',
                str(row.get('aliases', ''))[:2000] if pd.notna(row.get('aliases')) else '',
                str(row.get('dates_of_birth', ''))[:500] if pd.notna(row.get('dates_of_birth')) else '',
                str(row.get('raw_data', '{}')) if pd.notna(row.get('raw_data')) else '{}'
            ))
        
        # Execute batch
        execute_batch(cur, insert_sql, batch_data, page_size=1000)
        conn.commit()
        
        uploaded += len(batch)
        elapsed = time.time() - start
        rate = uploaded / elapsed if elapsed > 0 else 0
        eta = (total - uploaded) / rate / 60 if rate > 0 else 0
        progress = (uploaded / total) * 100
        
        log(f"✅ {uploaded:,}/{total:,} ({progress:5.1f}%) | "
            f"{rate:4.0f} rec/s | ETA {eta:4.1f}m")
    
    cur.close()
    conn.close()
    
    elapsed = time.time() - start
    log("="*70)
    log(f"🎉 COMPLETE in {elapsed/60:.1f} minutes!")
    log(f"   Uploaded: {uploaded:,} records")
    log(f"   Rate: {uploaded/elapsed:.0f} records/second")
    
    # Verify
    conn = psycopg2.connect(**CONN)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sanctions_list")
    final = cur.fetchone()[0]
    log(f"\n✅ Database: {final:,} records\n")
    
    cur.execute("""
        SELECT source, COUNT(*) 
        FROM sanctions_list 
        GROUP BY source 
        ORDER BY COUNT(*) DESC
    """)
    log("📋 Breakdown by source:")
    for row in cur.fetchall():
        log(f"   {row[0]:40s}: {row[1]:,}")
    
    cur.close()
    conn.close()
    log("="*70)
    
except Exception as e:
    log(f"❌ Upload failed: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()
    conn.close()
    exit(1)
