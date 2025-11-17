#!/usr/bin/env python3
import sys, os, time, pandas as pd, psycopg2
from psycopg2.extras import execute_batch

sys.stdout.reconfigure(line_buffering=True)

def log(msg):
    print(f"{msg}", flush=True)

log("="*70)
log("🚀 TURBO UPLOAD - OPTIMIZED FOR SPEED")
log("="*70)

CONN = {
    'host': 'complianceai-prod-18493.j77.aws-eu-central-1.cockroachlabs.cloud',
    'port': 26257, 'user': 'ahmed', 'password': 'p3OjZDFd2pJE-0O9qj0aPQ',
    'database': 'defaultdb', 'sslmode': 'require', 'connect_timeout': 10
}

CSV_FILE = 'cleaned_sanctions.csv'
CHUNK_SIZE = 100000  # Larger chunks
BATCH_SIZE = 10000   # Larger batches

try:
    # Drop indexes temporarily for faster insert
    log("\n🔧 Step 1: Dropping indexes for faster insert...")
    conn = psycopg2.connect(**CONN)
    cur = conn.cursor()
    cur.execute("DROP INDEX IF EXISTS idx_entity_name_lower")
    cur.execute("DROP INDEX IF EXISTS idx_list_source")
    cur.execute("DROP INDEX IF EXISTS idx_is_pep")
    cur.execute("DROP INDEX IF EXISTS idx_jurisdiction")
    conn.commit()
    cur.close()
    conn.close()
    log("   ✅ Indexes dropped")
    
    # Count rows
    log("\n📂 Step 2: Counting rows...")
    total = sum(1 for _ in open(CSV_FILE, encoding='utf-8')) - 1
    log(f"   Total: {total:,} records")
    
    insert_sql = """
        INSERT INTO sanctions_list 
        (entity_name, entity_type, first_name, last_name, list_source, 
         jurisdiction, aliases, date_of_birth, is_pep, pep_level)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    uploaded = 0
    start = time.time()
    
    log("\n⬆️  Step 3: Uploading data...\n")
    
    conn = psycopg2.connect(**CONN)
    conn.autocommit = False  # Manual commit control
    cur = conn.cursor()
    
    batch_data = []
    last_log = time.time()
    
    for chunk_num, chunk_df in enumerate(pd.read_csv(CSV_FILE, chunksize=CHUNK_SIZE, low_memory=False), 1):
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
                name[:500] or 'Unknown', entity_type[:100], first[:100], last[:100],
                source[:200] or 'Unknown', country[:500], aliases,
                dob[:500] if dob != 'nan' else None, is_pep,
                'medium' if is_pep else None
            ))
            
            # Insert in large batches
            if len(batch_data) >= BATCH_SIZE:
                execute_batch(cur, insert_sql, batch_data, page_size=5000)
                uploaded += len(batch_data)
                batch_data = []
                
                # Commit every 50K records
                if uploaded % 50000 == 0:
                    conn.commit()
                
                # Log every 5 seconds
                if time.time() - last_log >= 5:
                    elapsed = time.time() - start
                    rate = uploaded / elapsed
                    eta = (total - uploaded) / rate / 60
                    pct = uploaded / total * 100
                    log(f"📦 {uploaded:7,}/{total:,} ({pct:5.1f}%) | {rate:5.0f}/s | ETA {eta:5.1f}m")
                    last_log = time.time()
    
    # Insert remaining
    if batch_data:
        execute_batch(cur, insert_sql, batch_data, page_size=5000)
        uploaded += len(batch_data)
    
    conn.commit()
    cur.close()
    conn.close()
    
    elapsed = time.time() - start
    log(f"\n✅ Upload complete: {uploaded:,} records in {elapsed/60:.1f}m ({uploaded/elapsed:.0f}/s)")
    
    # Recreate indexes
    log("\n🔧 Step 4: Recreating indexes (this may take 5-10 minutes)...")
    conn = psycopg2.connect(**CONN)
    cur = conn.cursor()
    
    log("   Creating idx_entity_name_lower...")
    cur.execute("CREATE INDEX idx_entity_name_lower ON sanctions_list(LOWER(entity_name))")
    log("   Creating idx_list_source...")
    cur.execute("CREATE INDEX idx_list_source ON sanctions_list(list_source)")
    log("   Creating idx_is_pep...")
    cur.execute("CREATE INDEX idx_is_pep ON sanctions_list(is_pep)")
    log("   Creating idx_jurisdiction...")
    cur.execute("CREATE INDEX idx_jurisdiction ON sanctions_list(jurisdiction)")
    conn.commit()
    cur.close()
    conn.close()
    
    log("   ✅ All indexes created")
    
    total_time = time.time() - start
    log("\n" + "="*70)
    log(f"🎉 COMPLETE! {uploaded:,} records in {total_time/60:.1f} minutes")
    log("="*70)
    
except KeyboardInterrupt:
    log("\n⚠️  Interrupted")
    conn.rollback()
    exit(1)
except Exception as e:
    log(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
