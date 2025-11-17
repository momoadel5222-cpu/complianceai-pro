#!/usr/bin/env python3
import logging, json, requests, pandas as pd
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
logger = logging.getLogger()

logger.info("="*70)
logger.info("🚀 DOWNLOADING SANCTIONS DATA")
logger.info("="*70)

all_records = []

# OpenSanctions PEPs
logger.info("\n📥 OpenSanctions PEPs")
response = requests.get('https://data.opensanctions.org/datasets/latest/peps/entities.ftm.json', stream=True)
count = 0
for line in response.iter_lines():
    if line:
        entity = json.loads(line)
        all_records.append({
            'entity_id': entity.get('id', ''),
            'name': entity.get('caption', ''),
            'entity_type': entity.get('schema', ''),
            'source': 'OpenSanctions PEPs',
            'country': ','.join(entity.get('properties', {}).get('country', [])),
            'aliases': ','.join(entity.get('properties', {}).get('alias', [])),
            'dates_of_birth': ','.join(entity.get('properties', {}).get('birthDate', [])),
            'raw_data': json.dumps(entity)
        })
        count += 1
        if count % 50000 == 0:
            logger.info(f"   {count:,} records...")
logger.info(f"✅ {count:,} records")

# OpenSanctions Sanctions
logger.info("\n📥 OpenSanctions Sanctions")
response = requests.get('https://data.opensanctions.org/datasets/latest/sanctions/entities.ftm.json', stream=True)
count = 0
for line in response.iter_lines():
    if line:
        entity = json.loads(line)
        all_records.append({
            'entity_id': entity.get('id', ''),
            'name': entity.get('caption', ''),
            'entity_type': entity.get('schema', ''),
            'source': 'OpenSanctions Sanctions',
            'country': ','.join(entity.get('properties', {}).get('country', [])),
            'aliases': ','.join(entity.get('properties', {}).get('alias', [])),
            'dates_of_birth': ','.join(entity.get('properties', {}).get('birthDate', [])),
            'raw_data': json.dumps(entity)
        })
        count += 1
        if count % 25000 == 0:
            logger.info(f"   {count:,} records...")
logger.info(f"✅ {count:,} records")

# OFAC
logger.info("\n📥 OFAC SDN")
df_ofac = pd.read_csv('https://www.treasury.gov/ofac/downloads/sdn.csv', encoding='latin-1')
for _, row in df_ofac.iterrows():
    all_records.append({
        'entity_id': str(row.get('ent_num', '')),
        'name': str(row.get('SDN_Name', '')),
        'entity_type': str(row.get('SDN_Type', '')),
        'source': 'OFAC SDN',
        'country': '',
        'aliases': '',
        'dates_of_birth': '',
        'raw_data': row.to_json()
    })
logger.info(f"✅ {len(df_ofac):,} records")

logger.info(f"\n📊 TOTAL: {len(all_records):,} records")

# Clean and save
logger.info("🧹 Cleaning...")
df = pd.DataFrame(all_records)
df = df.drop_duplicates(subset=['entity_id', 'name'])
df = df.dropna(subset=['name'])
df['name'] = df['name'].str.strip()
df = df[df['name'] != '']

logger.info(f"💾 Saving {len(df):,} records...")
df.to_csv('cleaned_sanctions.csv', index=False)
logger.info(f"✅ SAVED: cleaned_sanctions.csv")

logger.info("\n📋 By source:")
for src, cnt in df['source'].value_counts().items():
    logger.info(f"   {src:30s}: {cnt:,}")

logger.info("="*70)
logger.info("✅ SUCCESS! Run: python scripts/upload_working.py")
