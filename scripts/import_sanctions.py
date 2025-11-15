#!/usr/bin/env python3
import csv
import json
import sys
import os
from supabase import create_client, Client

SUPABASE_URL = 'https://qwacsyreyuhhlvzcwhnw.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7es'

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def import_json(filepath, source_name='UN'):
    """Import sanctions data from JSON file"""
    print(f"\n{'='*60}")
    print(f"📂 Reading file: {filepath}")
    print(f"📋 Source: {source_name}")
    print(f"{'='*60}\n")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        entities = json.load(f)
    
    print(f"✅ Parsed {len(entities)} entities\n")
    
    # Insert in batches
    batch_size = 100
    total_inserted = 0
    errors = 0
    
    for i in range(0, len(entities), batch_size):
        batch = entities[i:i+batch_size]
        try:
            response = supabase.table('sanctions_list').insert(batch).execute()
            total_inserted += len(batch)
            print(f"✓ Batch {i//batch_size + 1}/{(len(entities)-1)//batch_size + 1}: Inserted {len(batch)} records")
        except Exception as e:
            errors += len(batch)
            print(f"✗ Error inserting batch {i//batch_size + 1}: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 Import Summary:")
    print(f"   Total Processed: {len(entities)}")
    print(f"   Successfully Inserted: {total_inserted}")
    print(f"   Errors: {errors}")
    print(f"{'='*60}\n")
    
    return total_inserted

def import_csv(filepath, source_name='OFAC'):
    """Import sanctions data from CSV file"""
    print(f"\n{'='*60}")
    print(f"📂 Reading file: {filepath}")
    print(f"📋 Source: {source_name}")
    print(f"{'='*60}\n")
    
    entities = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            aliases = []
            if row.get('aliases'):
                aliases = [a.strip() for a in row['aliases'].split(';') if a.strip()]
            
            nationalities = []
            if row.get('nationality'):
                nationalities = [n.strip() for n in row['nationality'].split(',') if n.strip()]
            
            entity = {
                'entity_name': row.get('name', '').strip(),
                'entity_type': row.get('type', 'individual').lower().strip(),
                'aliases': aliases,
                'nationalities': nationalities,
                'list_source': source_name,
                'program': row.get('program', 'General').strip(),
                'date_listed': row.get('date_listed', None) or None,
            }
            
            entities.append(entity)
    
    print(f"✅ Parsed {len(entities)} entities\n")
    
    batch_size = 100
    total_inserted = 0
    errors = 0
    
    for i in range(0, len(entities), batch_size):
        batch = entities[i:i+batch_size]
        try:
            response = supabase.table('sanctions_list').insert(batch).execute()
            total_inserted += len(batch)
            print(f"✓ Batch {i//batch_size + 1}/{(len(entities)-1)//batch_size + 1}: Inserted {len(batch)} records")
        except Exception as e:
            errors += len(batch)
            print(f"✗ Error inserting batch {i//batch_size + 1}: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 Import Summary:")
    print(f"   Total Processed: {len(entities)}")
    print(f"   Successfully Inserted: {total_inserted}")
    print(f"   Errors: {errors}")
    print(f"{'='*60}\n")
    
    return total_inserted

def clear_database(source_name=None):
    """Clear sanctions data"""
    if source_name:
        confirm = input(f"⚠️  Delete all records from '{source_name}'? Type 'YES' to confirm: ")
        if confirm == 'YES':
            try:
                supabase.table('sanctions_list').delete().eq('list_source', source_name).execute()
                print(f"✅ Cleared all {source_name} records")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print("❌ Cancelled")
    else:
        confirm = input("⚠️  DELETE ALL SANCTIONS DATA? Type 'DELETE ALL' to confirm: ")
        if confirm == 'DELETE ALL':
            try:
                supabase.table('sanctions_list').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
                print("✅ Database cleared")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print("❌ Cancelled")

def show_stats():
    """Show database statistics"""
    try:
        response = supabase.table('sanctions_list').select('*', count='exact').execute()
        total = response.count
        
        print(f"\n{'='*60}")
        print(f"📊 Database Statistics")
        print(f"{'='*60}")
        print(f"Total Records: {total}\n")
        
        response = supabase.table('sanctions_list').select('list_source').execute()
        sources = {}
        for item in response.data:
            source = item.get('list_source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        print("Records by Source:")
        for source, count in sorted(sources.items()):
            print(f"  • {source}: {count}")
        
        response = supabase.table('sanctions_list').select('entity_type').execute()
        types = {}
        for item in response.data:
            etype = item.get('entity_type', 'Unknown')
            types[etype] = types.get(etype, 0) + 1
        
        print("\nRecords by Type:")
        for etype, count in sorted(types.items()):
            print(f"  • {etype}: {count}")
        
        print(f"{'='*60}\n")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("��️  ComplianceAI Pro - Sanctions Data Importer")
    print("="*60)
    
    if len(sys.argv) < 2:
        print("""
📖 Usage:
  python3 import_sanctions.py <command> [args]

📝 Commands:
  import <file> [source_name]      Import data from CSV or JSON
  clear [source_name]              Clear data (optional: specific source)
  stats                            Show database statistics

💡 Examples:
  python3 import_sanctions.py import data/ofac.csv OFAC
  python3 import_sanctions.py import data/un.json UN
  python3 import_sanctions.py clear UN
  python3 import_sanctions.py stats
""")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'import':
        if len(sys.argv) < 3:
            print("❌ Error: Missing file path")
            sys.exit(1)
        
        filepath = sys.argv[2]
        source_name = sys.argv[3] if len(sys.argv) > 3 else 'OFAC'
        
        if not os.path.exists(filepath):
            print(f"❌ Error: File not found: {filepath}")
            sys.exit(1)
        
        # Detect file type and use appropriate importer
        if filepath.endswith('.json'):
            import_json(filepath, source_name)
        elif filepath.endswith('.csv'):
            import_csv(filepath, source_name)
        else:
            print("❌ Error: Unsupported file type. Use .csv or .json")
            sys.exit(1)
    
    elif command == 'clear':
        source_name = sys.argv[2] if len(sys.argv) > 2 else None
        clear_database(source_name)
    
    elif command == 'stats':
        show_stats()
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)
