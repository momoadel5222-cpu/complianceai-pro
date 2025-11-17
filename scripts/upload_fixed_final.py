#!/usr/bin/env python3
"""
Fixed Upload Script - Matches REAL CSV → Backend Schema
"""
import os, time, pandas as pd, psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
import sys

DB_URL = "postgresql://ahmed:p3OjZDFd2pJE-0O9qj0aPQ@complianceai-prod-18493.j77.aws-eu-central-1.cockroachlabs.cloud:26257/defaultdb?sslmode=require"

def upload_csv_to_db(csv_file, chunk_size=50000):
    print(f"🚀 UPLOADING {csv_file} → CockroachDB")
    
    # Connect & clear table
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE sanctions_list")
    conn.commit()
    
    total = 0
    start_time = time.time()
    
    # Read CSV in chunks
    for chunk in pd.read_csv(csv_file, chunksize=chunk_size, low_memory=False):
        # MAP YOUR CSV COLUMNS → SAFE BACKEND COLUMNS
        chunk['entity_name'] = chunk.get('name', chunk.get('entity_name', 'Unknown')).astype(str)
        chunk['entity_type'] = chunk.get('type', 'individual').astype(str)
        chunk['list_source'] = chunk.get('source', 'OpenSanctions').astype(str)
        chunk['program'] = chunk.get('program', 'General').astype(str)
        chunk['is_pep'] = chunk['is_pep'].fillna(False).astype(bool)
        chunk['pep_level'] = chunk.get('pep_level', None)
        chunk['jurisdiction'] = chunk.get('country', 'Unknown').astype(str)
        chunk['nationalities'] = chunk.get('nationality', []).astype(str)
        chunk['aliases'] = chunk.get('aliases', []).astype(str)
        chunk['date_of_birth'] = pd.to_datetime(chunk.get('date_of_birth'), errors='coerce')
        chunk['remarks'] = chunk.get('remarks', '').astype(str)
        chunk['last_updated_date'] = datetime.now()
        chunk['created_at'] = datetime.now()
        
        # Prepare data (ONLY SAFE COLUMNS)
        data = [
            (row.entity_name, row.entity_type, row.list_source, row.program,
             row.is_pep, row.pep_level, row.jurisdiction, str(row.nationalities),
             str(row.aliases), row.date_of_birth, row.remarks,
             row.last_updated_date, row.created_at)
            for _, row in chunk.iterrows()
        ]
        
        # Bulk insert
        execute_batch(cur, """
            INSERT INTO sanctions_list (
                entity_name, entity_type, list_source, program, is_pep, pep_level,
                jurisdiction, nationalities, aliases, date_of_birth, remarks,
                last_updated_date, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, data)
        conn.commit()
        
        total += len(chunk)
        elapsed = time.time() - start_time
        speed = total / elapsed if elapsed > 0 else 0
        eta = (2300000 - total) / speed if speed > 0 else 0
        
        print(f"📊 {total:,} records | {speed:,.0f}/sec | ETA: {eta/60:.0f}m")
    
    cur.execute("SELECT COUNT(*) FROM sanctions_list")
    final_count = cur.fetchone()[0]
    print(f"✅ COMPLETE! {final_count:,} records uploaded!")
    conn.close()

if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "data/sanctions_full.csv"
    upload_csv_to_db(csv_file)
