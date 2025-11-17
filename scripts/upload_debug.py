#!/usr/bin/env python3
import sys
import os
import time
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

def log(msg):
    print(f"{msg}", flush=True)

log("="*70)
log("🚀 UPLOADING SANCTIONS DATA")
log("="*70)

CONN = {
    'host': 'complianceai-prod-18493.j77.aws-eu-central-1.cockroachlabs.cloud',
    'port': 26257,
    'user': 'ahmed',
    'password': 'p3OjZDFd2pJE-0O9qj0aPQ',
    'database': 'defaultdb',
    'sslmode': 'require',
    'connect_timeout': 10
}

CSV_FILE = 'cleaned_sanctions.csv'
CHUNK_SIZE = 50000
BATCH_SIZE = 5000

try:
    # Check CSV file
    if not os.path.exists(CSV_FILE):
        log(f"❌ ERROR: {CSV_FILE} not found!")
        exit(1)
    
    log(f"\n📂 CSV file: {CSV_FILE}")
    size_mb = os.path.getsize(CSV_FILE) / 1024 / 1024
    log(f"   Size: {size_mb:.1f} MB")
    
    # Count rows
    log("\n🔢 Counting rows...")
    total = sum(1 for _ in open(CSV_FILE, encoding='utf-8')) - 1
    log(f"   Total records: {total:,}")
    
    # Prepare insert SQL
    insert_sql = """
        INSERT INTO sanctions_list 
        (entity_name, entity_type, first_name, last_name, list_source, 
         jurisdiction, aliases, date_of_birth, is_pep, pep_level)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    uploaded = 0
    start = time.time()
    
    log("\n⬆️  Starting upload...\n")
    
    for chunk_num, chunk_df in enumerate(pd.read_csv(CSV_FILE, chunksize=CHUNK_SIZE, low_memory=False), 1):
        conn = psycopg2.connect(**CONN)
        conn.autocommit = False
        cur = conn.cursor()
        
        batch_data = []
        for _, row in chunk_df.iterrows():
            name = str(row.get('name', '')) if pd.notna(row.get('name')) else ''
            entity_type = str(row.get('entity_type', '')) if pd.notna(row.get('entity_type')) else ''
            source = str(row.get('source', '')) if pd.notna(row.get('source')) else ''
            country = str(row.get('country', '')) if pd.notna(row.get('country')) else ''
            aliases_str = str(row.get('aliases', '')) if pd.notna(row.get('aliases')) else ''
            dob = str(row.get('dates_of_birth', '')) if pd.notna(row.get('dates_of_birth')) else ''
            
            aliases = [a.strip() for a in aliases_str.split('|') if a.strip()] if aliases_str else []
            is_pep = 'pep' in source.lower()
            
            name_parts = name.strip().split()
            first = name_parts[0] if name_parts else ''
            last = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            
            batch_data.append((
                name[:500] or 'Unknown',
                entity_type[:100],
                first[:100],
                last[:100],
                source[:200] or 'Unknown',
                country[:500],
                aliases,
                dob[:500] if dob != 'nan' else None,
                is_pep,
                'medium' if is_pep else None
            ))
        
        execute_batch(cur, insert_sql, batch_data, page_size=1000)
        conn.commit()
        uploaded += len(batch_data)
        
        elapsed = time.time() - start
        rate = uploaded / elapsed
        eta = (total - uploaded) / rate / 60
        pct = uploaded / total * 100
        
        log(f"📦 Chunk {chunk_num:3d} | {uploaded:7,}/{total:,} ({pct:5.1f}%) | {rate:5.0f}/s | ETA {eta:5.1f}m")
        
        cur.close()
        conn.close()
    
    elapsed = time.time() - start
    log("\n" + "="*70)
    log(f"🎉 SUCCESS!")
    log(f"   Uploaded: {uploaded:,} records")
    log(f"   Duration: {elapsed/60:.1f} minutes")
    log(f"   Rate: {uploaded/elapsed:.0f} records/second")
    log("="*70)
    
except KeyboardInterrupt:
    log("\n⚠️  Upload interrupted by user")
    exit(1)
    
except Exception as e:
    log(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
