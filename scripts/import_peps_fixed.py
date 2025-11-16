#!/usr/bin/env python3
"""
Fixed PEP Import - No artificial limits
"""

import requests
import json
from supabase import create_client
import time

SUPABASE_URL = "https://qwacsyreyuhhlvzcwhnw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7es"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def batch_insert(entities):
    """Insert entities in batches"""
    if not entities:
        return 0
    
    try:
        supabase.table('sanctions_list').insert(entities).execute()
        return len(entities)
    except Exception as e:
        print(f"  ⚠️ Batch error: {e}")
        # Try one by one
        success = 0
        for entity in entities:
            try:
                supabase.table('sanctions_list').insert(entity).execute()
                success += 1
            except:
                pass
        return success

def import_opensanctions_full():
    """Import FULL OpenSanctions PEP dataset - NO LIMITS"""
    print("\n🎩 IMPORTING FULL OPENSANCTIONS PEP DATA")
    print("⚠️  This will import ALL available PEPs (200K+)")
    print("⏱️  Expected time: 20-30 minutes\n")
    
    url = 'https://data.opensanctions.org/datasets/latest/peps/entities.ftm.json'
    
    print(f"📥 Downloading OpenSanctions PEP database...")
    
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return 0
    
    entities = []
    total_count = 0
    skipped = 0
    egypt_count = 0
    kuwait_count = 0
    uae_count = 0
    
    print("📝 Processing PEP records (NO LIMIT)...\n")
    
    for line in response.iter_lines():
        if not line:
            continue
        
        try:
            data = json.loads(line)
            properties = data.get('properties', {})
            
            # Get name
            names = properties.get('name', [])
            if not names or not names[0]:
                skipped += 1
                continue
            
            # Get countries
            countries = properties.get('country', [])
            nationalities = countries[:3] if countries else []
            
            # Count MENA region
            if countries:
                country_str = str(countries).upper()
                if 'EG' in country_str or 'EGYPT' in country_str:
                    egypt_count += 1
                if 'KW' in country_str or 'KUWAIT' in country_str:
                    kuwait_count += 1
                if 'AE' in country_str or 'UAE' in country_str or 'EMIRATES' in country_str:
                    uae_count += 1
            
            entity = {
                'entity_name': names[0],
                'entity_type': 'individual',
                'list_source': 'OpenSanctions-PEP',
                'program': 'Politically Exposed Person',
                'is_pep': True,
                'pep_level': 'direct',
                'position': ', '.join(properties.get('position', [])[:3]),
                'jurisdiction': countries[0] if countries else '',
                'nationalities': nationalities,
                'aliases': properties.get('alias', [])[:10]
            }
            
            # Determine PEP level
            topics = properties.get('topics', [])
            if 'role.rca' in topics:
                entity['pep_level'] = 'associate'
            
            entities.append(entity)
            total_count += 1
            
            # Batch insert every 100
            if len(entities) >= 100:
                count = batch_insert(entities)
                print(f"  ✓ {total_count:,} PEPs | Egypt: {egypt_count} | Kuwait: {kuwait_count} | UAE: {uae_count}")
                entities = []
                time.sleep(0.05)
                
        except Exception as e:
            skipped += 1
            continue
    
    # Insert remaining
    if entities:
        batch_insert(entities)
    
    print(f"\n✅ IMPORT COMPLETE!")
    print(f"📊 Total PEPs imported: {total_count:,}")
    print(f"🇪🇬 Egypt PEPs: {egypt_count}")
    print(f"🇰🇼 Kuwait PEPs: {kuwait_count}")
    print(f"🇦🇪 UAE PEPs: {uae_count}")
    print(f"⚠️  Skipped invalid: {skipped}")
    
    return total_count

if __name__ == '__main__':
    # First, delete existing OpenSanctions-PEP entries
    print("🗑️  Removing old PEP data...")
    try:
        supabase.table('sanctions_list').delete().eq('list_source', 'OpenSanctions-PEP').execute()
        print("✅ Old data cleared\n")
    except Exception as e:
        print(f"⚠️  Error clearing: {e}\n")
    
    # Import fresh data
    import_opensanctions_full()
