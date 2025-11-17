#!/usr/bin/env python3
import os, time, pandas as pd, psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime

def log(msg):
    print(f"{datetime.now().strftime('%H:%M:%S')} | {msg}")

BATCH_SIZE = 5000
CHUNK_SIZE = 50000  # Process 50k rows at a time
CONN = {
    'host': 'complianceai-prod-18493.j77.aws-eu-central-1.cockroachlabs.cloud',
    'port': 26257,
    'user': 'ahmed',
    'password': 'p3OjZDFd2pJE-0O9qj0aPQ',
    'database': 'defaultdb',
    'sslmode': 'require'
}

log("="*70)
log("🚀 UPLOADING TO COCKROACHDB (CHUNKED)")
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

# Create table
log("🏗️  Creating table if needed...")
conn = psycopg2.connect(**CONN)
cur = conn.cursor()

cur.execute("""
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
""")
conn.commit()
log("✅ Table ready\n")

# Check existing
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

cur.close()
conn.close()

# Count total rows
log("📂 Counting rows...")
if not os.path.exists('cleaned_sanctions.csv'):
    log("❌ File not found!")
    exit(1)

total_rows = sum(1 for _ in open('cleaned_sanctions.csv')) - 1  # -1 for header
log(f"✅ Total: {total_rows:,} records\n")

# Upload in chunks
log(f"⬆️  Uploading in chunks of {CHUNK_SIZE:,} (batches of {BATCH_SIZE:,})...")
log("="*70)

insert_sql = """
    INSERT INTO sanctions_list 
    (entity_id, name, entity_type, source, country, aliases, dates_of_birth, raw_data)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
"""

uploaded = 0
start = time.time()

try:
    # Process CSV in chunks
    for chunk_num, chunk_df in enumerate(pd.read_csv('cleaned_sanctions.csv', 
                                                       chunksize=CHUNK_SIZE,
                                                       low_memory=False), 1):
        
        conn = psycopg2.connect(**CONN)
        conn.autocommit = False
        cur = conn.cursor()
        
        # Process chunk in batches
        chunk_uploaded = 0
        for i in range(0, len(chunk_df), BATCH_SIZE):
            batch = chunk_df.iloc[i:i+BATCH_SIZE]
            
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
            
            execute_batch(cur, insert_sql, batch_data, page_size=1000)
            conn.commit()
            
            chunk_uploaded += len(batch)
            uploaded += len(batch)
            
            elapsed = time.time() - start
            rate = uploaded / elapsed if elapsed > 0 else 0
            eta = (total_rows - uploaded) / rate / 60 if rate > 0 else 0
            progress = (uploaded / total_rows) * 100
            
            log(f"✅ Chunk {chunk_num} | {uploaded:,}/{total_rows:,} ({progress:5.1f}%) | "
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
    exit(1)
