#!/usr/bin/env python3
import os, time, pandas as pd, logging
from sqlalchemy import create_engine, text
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{timestamp} | INFO    | {msg}")

# COCKROACHDB URL
DB_URL = "postgresql+psycopg2://ahmed:p3OjZDFd2pJE-0O9qj0aPQ@complianceai-prod-18493.j77.aws-eu-central-1.cockroachlabs.cloud:26257/defaultdb?sslmode=require"

def create_cockroach_engine():
    return create_engine(
        DB_URL,
        connect_args={'options': '-csearch_path=public'},  # ✅ CockroachDB fix
        pool_pre_ping=False,
        pool_recycle=300
    )

log("🔗 Testing connection...")
engine = create_cockroach_engine()
DB_URL = "postgresql+psycopg2://ahmed:p3OjZDFd2pJE-0O9qj0aPQ@complianceai-prod-18493.j77.aws-eu-central-1.cockroachlabs.cloud:26257/defaultdb?sslmode=require"

def create_cockroach_engine():
    return create_engine(
        DB_URL,
        connect_args={'options': '-csearch_path=public'},
        pool_pre_ping=False,
        pool_recycle=300
    )

log("🔗 Testing connection...")
engine = create_cockroach_engine()

try:
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM sanctions_list")).scalar()
        log(f"✅ CONNECTION PERFECT! Current records: {count:,}")
except Exception as e:
    log(f"❌ Connection failed: {e}")
    exit(1)

# SAVE CLEANED DATA (in case not saved)
log("💾 Saving cleaned_sanctions.csv...")
df = pd.DataFrame()  # Placeholder - will be loaded from memory or re-create
log("📂 Loading cleaned data...")
df = pd.read_csv('cleaned_sanctions.csv') if os.path.exists('cleaned_sanctions.csv') else pd.DataFrame()
log(f"📊 Loaded {len(df):,} records")

BATCH_SIZE = 25000
total_batches = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE
log(f"🚀 Starting {total_batches} batches...")

start_time = time.time()
for i in range(0, len(df), BATCH_SIZE):
    batch_df = df.iloc[i:i+BATCH_SIZE]
    batch_num = (i // BATCH_SIZE) + 1
    batch_df.to_sql('sanctions_list', engine, if_exists='append', index=False, method='multi')
    elapsed = time.time() - start_time
    speed = (i + len(batch_df)) / elapsed / 1000
    log(f"✅ Batch {batch_num}/{total_batches} ({len(batch_df):,} records, {speed:.0f} rec/sec)")

log(f"🎉 COMPLETE! {len(df):,} records")
