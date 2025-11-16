#!/usr/bin/env python3
"""
Import UK HMT/OFSI and UAE Terrorist Lists
Quick import - approximately 3-4 minutes
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
        success = 0
        for entity in entities:
            try:
                supabase.table('sanctions_list').insert(entity).execute()
                success += 1
            except:
                pass
        return success

def import_uk_ofsi():
    """Import UK HMT/OFSI Consolidated List"""
    print("\n🇬🇧 IMPORTING UK HMT/OFSI CONSOLIDATED LIST")
    print("=" * 60)
    
    url = 'https://data.opensanctions.org/datasets/latest/gb_hmt_sanctions/entities.ftm.json'
    
    print(f"📥 Downloading UK sanctions data...")
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return 0
    
    entities = []
    total_count = 0
    skipped = 0
    
    print("📝 Processing UK entities...\n")
    
    for line in response.iter_lines():
        if not line:
            continue
        
        try:
            data = json.loads(line)
            properties = data.get('properties', {})
            schema = data.get('schema', '')
            
            # Get name
            names = properties.get('name', [])
            if not names or not names[0]:
                skipped += 1
                continue
            
            # Determine entity type
            entity_type = 'individual' if schema == 'Person' else 'entity'
            
            entity = {
                'entity_name': names[0],
                'entity_type': entity_type,
                'list_source': 'UK-OFSI',
                'program': 'UK Financial Sanctions',
                'is_pep': False,
                'nationalities': properties.get('country', [])[:3],
                'aliases': properties.get('alias', [])[:10],
                'remarks': ', '.join(properties.get('notes', [])[:3]) if properties.get('notes') else None
            }
            
            # Add birth date for individuals
            if entity_type == 'individual':
                birth_dates = properties.get('birthDate', [])
                if birth_dates:
                    entity['date_of_birth'] = birth_dates[0]
            
            entities.append(entity)
            total_count += 1
            
            # Batch insert every 50
            if len(entities) >= 50:
                count = batch_insert(entities)
                print(f"  ✓ Imported {total_count} UK entities...")
                entities = []
                time.sleep(0.05)
                
        except Exception as e:
            skipped += 1
            continue
    
    # Insert remaining
    if entities:
        batch_insert(entities)
    
    print(f"\n✅ UK OFSI Import Complete: {total_count} entities")
    print(f"⚠️  Skipped invalid: {skipped}\n")
    return total_count

def import_uae_terrorist_list():
    """Import UAE Local Terrorist List"""
    print("\n🇦🇪 IMPORTING UAE LOCAL TERRORIST LIST")
    print("=" * 60)
    
    url = 'https://data.opensanctions.org/datasets/latest/ae_local_terrorists/entities.ftm.json'
    
    print(f"📥 Downloading UAE terrorist list...")
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return 0
    
    entities = []
    total_count = 0
    skipped = 0
    
    print("📝 Processing UAE entities...\n")
    
    for line in response.iter_lines():
        if not line:
            continue
        
        try:
            data = json.loads(line)
            properties = data.get('properties', {})
            schema = data.get('schema', '')
            
            # Get name
            names = properties.get('name', [])
            if not names or not names[0]:
                skipped += 1
                continue
            
            # Determine entity type
            entity_type = 'individual' if schema == 'Person' else 'entity'
            
            entity = {
                'entity_name': names[0],
                'entity_type': entity_type,
                'list_source': 'UAE-Terrorist',
                'program': 'UAE Counter-Terrorism',
                'is_pep': False,
                'nationalities': properties.get('country', [])[:3],
                'aliases': properties.get('alias', [])[:10],
                'remarks': ', '.join(properties.get('notes', [])[:3]) if properties.get('notes') else None
            }
            
            # Add birth date for individuals
            if entity_type == 'individual':
                birth_dates = properties.get('birthDate', [])
                if birth_dates:
                    entity['date_of_birth'] = birth_dates[0]
            
            entities.append(entity)
            total_count += 1
            
            # Batch insert every 50
            if len(entities) >= 50:
                count = batch_insert(entities)
                print(f"  ✓ Imported {total_count} UAE entities...")
                entities = []
                time.sleep(0.05)
                
        except Exception as e:
            skipped += 1
            continue
    
    # Insert remaining
    if entities:
        batch_insert(entities)
    
    print(f"\n✅ UAE Terrorist List Import Complete: {total_count} entities")
    print(f"⚠️  Skipped invalid: {skipped}\n")
    return total_count

def show_final_stats():
    """Show complete database statistics"""
    print("\n" + "=" * 60)
    print("📊 COMPLETE DATABASE STATISTICS")
    print("=" * 60)
    
    try:
        # Total count
        result = supabase.table('sanctions_list').select('id', count='exact').execute()
        total = result.count if hasattr(result, 'count') else 0
        print(f"\n📌 Total Entities: {total:,}")
        
        # By source
        print("\n📋 By Data Source:")
        sources = ['OFAC', 'UN', 'OpenSanctions-PEP', 'UK-OFSI', 'UAE-Terrorist']
        
        for source in sources:
            result = supabase.table('sanctions_list').select('id', count='exact').eq('list_source', source).execute()
            count = result.count if hasattr(result, 'count') else 0
            if count > 0:
                icon = {'OFAC': '🇺🇸', 'UN': '🌍', 'OpenSanctions-PEP': '🎩', 'UK-OFSI': '🇬🇧', 'UAE-Terrorist': '🇦🇪'}.get(source, '📄')
                print(f"   {icon} {source}: {count:,}")
        
        # PEP count
        pep_result = supabase.table('sanctions_list').select('id', count='exact').eq('is_pep', True).execute()
        pep_count = pep_result.count if hasattr(pep_result, 'count') else 0
        print(f"\n🎩 Total PEPs: {pep_count:,}")
        print(f"🚫 Total Sanctions (non-PEP): {total - pep_count:,}")
        
    except Exception as e:
        print(f"⚠️  Error getting statistics: {e}")
    
    print("=" * 60)

def main():
    """Main import function"""
    print("\n" + "=" * 60)
    print("🚀 IMPORTING UK & UAE SANCTIONS LISTS")
    print("=" * 60)
    print("\nThis will add:")
    print("  🇬🇧 UK HMT/OFSI Consolidated List (~1,500 entities)")
    print("  🇦🇪 UAE Local Terrorist List (~80-100 entities)")
    print("\n⏱️  Estimated time: 3-4 minutes\n")
    
    input("Press Enter to start import...")
    
    start_time = time.time()
    
    # Import both lists
    uk_count = import_uk_ofsi()
    uae_count = import_uae_terrorist_list()
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("✅ IMPORT COMPLETE!")
    print("=" * 60)
    print(f"🇬🇧 UK OFSI: {uk_count:,} entities")
    print(f"🇦🇪 UAE Terrorist List: {uae_count:,} entities")
    print(f"📊 Total Added: {uk_count + uae_count:,} entities")
    print(f"⏱️  Time taken: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    
    # Show complete stats
    show_final_stats()
    
    print("\n🎉 Your screening tool now has 5 major sanctions sources!")
    print("=" * 60)

if __name__ == '__main__':
    main()
