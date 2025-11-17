import sys
import os
import warnings
import logging
from datetime import datetime
import uuid
from typing import List, Dict, Any
import io  # 🔥 CRITICAL FIX FOR OFAC

# Fix Pandas warnings
import pandas as pd
import numpy as np
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)
pd.options.mode.chained_assignment = None

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
import json
from tqdm import tqdm
import xml.etree.ElementTree as ET

# Import DB config
from backend.config import get_db_connection, release_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler('sanctions_import.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SanctionsImporter:
    """🌍 Fixed Sanctions Data Importer"""
    
    BATCH_SIZE = 1000
    COMMIT_INTERVAL = 50000
    
    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self.total_imported = 0
        
        self.sources = {
            'opensanctions_peps': {
                'name': 'OpenSanctions PEPs',
                'url': 'https://data.opensanctions.org/datasets/latest/peps/entities.ftm.json',
                'is_pep': True,
                'type': 'opensanctions'
            },
            'opensanctions_sanctions': {
                'name': 'OpenSanctions Global Sanctions',
                'url': 'https://data.opensanctions.org/datasets/latest/sanctions/entities.ftm.json',
                'is_pep': False,
                'type': 'opensanctions'
            },
            'opensanctions_uae': {
                'name': 'UAE Local Terrorist List',
                'url': 'https://data.opensanctions.org/datasets/latest/ae_local_terrorists/entities.ftm.json',
                'is_pep': False,
                'type': 'opensanctions'
            },
            'opensanctions_uk': {
                'name': 'UK HMT/OFSI Sanctions',
                'url': 'https://data.opensanctions.org/datasets/latest/gb_hmt_sanctions/entities.ftm.json',
                'is_pep': False,
                'type': 'opensanctions'
            },
            'ofac': {
                'name': 'OFAC SDN List',
                'url': 'https://www.treasury.gov/ofac/downloads/sdn.csv',
                'is_pep': False,
                'type': 'ofac'
            },
            'un': {
                'name': 'UN Consolidated List',
                'url': 'https://scsanctions.un.org/resources/xml/en/consolidated.xml',
                'is_pep': False,
                'type': 'un'
            }
        }
    
    def get_first(self, val: Any) -> Any:
        if isinstance(val, list) and val:
            return val
        return val
    
    def download_opensanctions(self, url: str, source_name: str, is_pep: bool):
        """📥 Download OpenSanctions JSON"""
        logger.info(f"📥 {source_name}")
        logger.info(f"🔗 {url}")
        
        try:
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            processed = 0
            for line in response.iter_lines():
                if line:
                    try:
                        entity = json.loads(line)
                        props = entity.get('properties', {})
                        
                        name = self.get_first(props.get('name'))
                        if not name:
                            continue
                        
                        program = 'PEP' if is_pep else self.get_first(props.get('program')) or 'Sanctions'
                        
                        record = {
                            'id': str(uuid.uuid4()),
                            'entity_name': str(name),
                            'entity_type': entity.get('schema', 'Person').lower(),
                            'first_name': self.get_first(props.get('firstName')),
                            'last_name': self.get_first(props.get('lastName')),
                            'list_source': source_name,
                            'program': program,
                            'is_pep': is_pep,
                            'pep_level': self.get_first(props.get('pepStatus')),
                            'position': self.get_first(props.get('position')),
                            'jurisdiction': self.get_first(props.get('country')),
                            'nationalities': json.dumps(props.get('nationality', [])),
                            'aliases': json.dumps(props.get('alias', [])),
                            'date_of_birth': self.get_first(props.get('birthDate')),
                            'remarks': self.get_first(props.get('notes')),
                            'last_updated_date': datetime.now(),
                            'created_at': datetime.now()
                        }
                        
                        self.records.append(record)
                        processed += 1
                        
                        if processed % 25000 == 0:
                            logger.info(f"   ✓ {processed:,} records")
                    
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            logger.info(f"✅ {source_name}: {processed:,} records")
            
        except requests.RequestException as e:
            logger.error(f"❌ Network error {source_name}: {e}")
    
    def download_ofac(self, url: str, source_name: str):
        """📥 Download OFAC CSV (FIXED)"""
        logger.info(f"📥 {source_name}")
        logger.info(f"🔗 {url}")
        
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            
            # 🔥 FIXED: Use io.StringIO instead of deprecated pandas.compat
            df = pd.read_csv(
                io.StringIO(response.text),  # CORRECTED HERE
                encoding='latin1',
                on_bad_lines='skip',
                low_memory=False
            )
            
            for _, row in df.iterrows():
                record = {
                    'id': str(uuid.uuid4()),
                    'entity_name': str(row.iloc[1]) if len(row) > 1 else 'Unknown',
                    'entity_type': str(row.iloc[2]).lower() if len(row) > 2 else 'individual',
                    'first_name': None,
                    'last_name': None,
                    'list_source': source_name,
                    'program': str(row.iloc[3]) if len(row) > 3 else 'SDN',
                    'is_pep': False,
                    'pep_level': None,
                    'position': str(row.iloc[4]) if len(row) > 4 else None,
                    'jurisdiction': None,
                    'nationalities': None,
                    'aliases': None,
                    'date_of_birth': None,
                    'remarks': str(row.iloc[-1]) if len(row) > 5 else None,
                    'last_updated_date': datetime.now(),
                    'created_at': datetime.now()
                }
                self.records.append(record)
            
            logger.info(f"✅ {source_name}: {len(df):,} records")
            
        except Exception as e:
            logger.error(f"❌ OFAC error: {e}")
    
    def download_un(self, url: str, source_name: str):
        """📥 Download UN XML"""
        logger.info(f"📥 {source_name}")
        logger.info(f"🔗 {url}")
        
        try:
            response = requests.get(url, timeout=180)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            individuals = root.findall(".//INDIVIDUAL")
            
            for individual in individuals:
                first_name = individual.find(".//FIRST_NAME")
                last_name = individual.find(".//SECOND_NAME")
                
                name_parts = []
                if first_name is not None and first_name.text:
                    name_parts.append(first_name.text)
                if last_name is not None and last_name.text:
                    name_parts.append(last_name.text)
                
                if not name_parts:
                    continue
                
                record = {
                    'id': str(uuid.uuid4()),
                    'entity_name': " ".join(name_parts),
                    'entity_type': 'individual',
                    'first_name': first_name.text if first_name is not None else None,
                    'last_name': last_name.text if last_name is not None else None,
                    'list_source': source_name,
                    'program': 'UN Sanctions',
                    'is_pep': False,
                    'pep_level': None,
                    'position': None,
                    'jurisdiction': None,
                    'nationalities': None,
                    'aliases': None,
                    'date_of_birth': None,
                    'remarks': None,
                    'last_updated_date': datetime.now(),
                    'created_at': datetime.now()
                }
                self.records.append(record)
            
            logger.info(f"✅ {source_name}: {len(individuals):,} records")
            
        except Exception as e:
            logger.error(f"❌ UN error: {e}")
    
    def download_all_sources(self):
        """Download all sources"""
        logger.info("=" * 80)
        logger.info("🌍 DOWNLOADING ALL SOURCES")
        logger.info("=" * 80)
        
        for source_key, config in self.sources.items():
            if config['type'] == 'opensanctions':
                self.download_opensanctions(config['url'], config['name'], config['is_pep'])
            elif config['type'] == 'ofac':
                self.download_ofac(config['url'], config['name'])
            elif config['type'] == 'un':
                self.download_un(config['url'], config['name'])
        
        logger.info(f"📊 TOTAL: {len(self.records):,} records collected")
    
    def clean_data(self):
        """🧹 Clean & deduplicate"""
        logger.info("\n🧹 CLEANING DATA...")
        
        df = pd.DataFrame(self.records)
        
        # Deduplicate
        initial = len(df)
        df = df.drop_duplicates(subset=['entity_name', 'list_source'], keep='first')
        logger.info(f"Deduplicated: {initial:,} → {len(df):,} (-{initial-len(df):,})")
        
        # Fix dates
        for col in ['date_of_birth', 'last_updated_date', 'created_at']:
            df[col] = pd.to_datetime(df[col], errors='coerce').where(
                pd.notnull(df[col]), None
            )
        
        # Clean nulls
        df = df.replace({np.nan: None, pd.NaT: None})
        
        self.records = df.to_dict('records')
        logger.info(f"✅ Cleaned: {len(self.records):,} records ready")
    
    def import_to_cockroach(self):
        """🚀 Fixed CockroachDB import"""
        logger.info("\n🚀 IMPORTING TO COCKROACHDB...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Clear table
            cursor.execute("TRUNCATE TABLE sanctions_list")
            conn.commit()
            logger.info("🗑️  Table cleared")
            
            insert_sql = """
                INSERT INTO sanctions_list (
                    id, entity_name, entity_type, first_name, last_name,
                    list_source, program, is_pep, pep_level, position,
                    jurisdiction, nationalities, aliases, date_of_birth,
                    remarks, last_updated_date, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            total = len(self.records)
            imported = 0
            
            with tqdm(total=total, desc="Importing", unit="rows") as pbar:
                for i in range(0, total, self.BATCH_SIZE):
                    batch = self.records[i:i + self.BATCH_SIZE]
                    
                    try:
                        batch_data = [
                            tuple(r.get(k, None) for k in [
                                'id', 'entity_name', 'entity_type', 'first_name', 'last_name',
                                'list_source', 'program', 'is_pep', 'pep_level', 'position',
                                'jurisdiction', 'nationalities', 'aliases', 'date_of_birth',
                                'remarks', 'last_updated_date', 'created_at'
                            ])
                            for r in batch
                        ]
                        
                        cursor.executemany(insert_sql, batch_data)
                        
                        imported += len(batch)
                        pbar.update(len(batch))
                        
                        # COMMIT EVERY 50k ROWS
                        if imported % self.COMMIT_INTERVAL == 0:
                            conn.commit()
                            logger.info(f"💾 Checkpoint: {imported:,}/{total:,} ({imported/total*100:.1f}%)")
                    
                    except Exception as e:
                        conn.rollback()
                        logger.error(f"❌ Batch {i//self.BATCH_SIZE + 1} failed: {e}")
                        continue
            
            # Final commit
            conn.commit()
            self.total_imported = imported
            logger.info(f"\n✅ Imported {imported:,} records!")
            
            # Stats
            self._show_stats(cursor)
            
        except Exception as e:
            logger.error(f"❌ Import failed: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            release_db_connection(conn)
    
    def _show_stats(self, cursor):
        """📊 Show final statistics"""
        cursor.execute("SELECT COUNT(*) FROM sanctions_list")
        final_count = cursor.fetchone()
        
        logger.info(f"📊 DB Count: {final_count:,} | Success Rate: {(final_count/self.total_imported*100):.1f}%")
        
        # By source
        cursor.execute("SELECT list_source, COUNT(*) FROM sanctions_list GROUP BY list_source ORDER BY count DESC")
        logger.info("📋 By source:")
        for row in cursor.fetchall():
            logger.info(f"   • {row:<30} {row[1]:>6,}")
    
    def run_full_pipeline(self):
        """🎯 Run complete pipeline"""
        start = datetime.now()
        
        logger.info("🚀 STARTING SANCTIONS IMPORT")
        logger.info(f"⏱️  Started: {start.strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.download_all_sources()
        self.clean_data()
        self.import_to_cockroach()
        
        end = datetime.now()
        duration = (end - start).total_seconds() / 60
        
        logger.info("\n✨ COMPLETE!")
        logger.info(f"⏱️  Duration: {duration:.1f} minutes")
        logger.info("🎉 Database ready!")


if __name__ == "__main__":
    try:
        importer = SanctionsImporter()
        importer.run_full_pipeline()
    except KeyboardInterrupt:
        logger.info("⚠️  Cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Fatal: {e}")
        sys.exit(1)
ENDOFFILE

