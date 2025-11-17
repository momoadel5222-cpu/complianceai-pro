#!/usr/bin/env python3
import os, time, pandas as pd, logging
from sqlalchemy import create_engine, text
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{timestamp} | INFO    | {msg}")
    logging.info(msg)

# COCKROACHDB CONNECTION WITH FIX
DB_URL = os.getenv('COCKROACH_URL', "postgresql+psycopg2://ahmed:p3OjZDFd2pJE-0O9qj0aPQ@complianceai-prod-18493.j77.aws-eu-central-1.cockroachlabs.cloud:26257/defaultdb?sslmode=require")

def create_cockroach_engine():
    return create_engine(
        DB_URL,
        connect_args={'server_version': '12'},  # ✅ FIXES CockroachDB version error
        pool_pre_ping=False,
        pool_recycle=300,
        echo=False
    )

log("🔗 Testing CockroachDB connection...")
engine = create_cockroach_engine()

try:
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM sanctions_list")).scalar()
        log(f"✅ CONNECTION PERFECT! Current records: {count:,}")
except Exception as e:
    log(f"❌ Connection failed: {e}")
    exit(1)

# LOAD CLEANED DATA
log("📂 Loading cleaned sanctions data...")
df = pd.read_csv('cleaned_sanctions.csv')
log(f"📊 Loaded {len(df):,} records for upload")

# BATCH UPLOAD (25k chunks)
BATCH_SIZE = 25000
total_batches = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE
log(f"🚀 Starting {total_batches} batches of {BATCH_SIZE:,} records each...")

start_time = time.time()
for i in range(0, len(df), BATCH_SIZE):
    batch_df = df.iloc[i:i+BATCH_SIZE]
    batch_num = (i // BATCH_SIZE) + 1
    
    try:
        batch_df.to_sql(
            'sanctions_list', 
            engine, 
            if_exists='append', 
            index=False, 
            method='multi',
            chunksize=5000
        )
        elapsed = time.time() - start_time
        speed = (i + len(batch_df)) / elapsed / 1000  # records/sec
        log(f"✅ Batch {batch_num}/{total_batches} ({len(batch_df):,} records, {speed:.0f} rec/sec)")
    except Exception as e:
        log(f"❌ Batch {batch_num} failed: {e}")
        break

total_time = time.time() - start_time
log(f"🎉 UPLOAD COMPLETE! {len(df):,} records in {total_time/60:.1f} minutes")
