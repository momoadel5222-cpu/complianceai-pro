#!/usr/bin/env python3
"""
Parse OFAC SDN CSV files and convert to our standard format
"""
import csv
import sys

def parse_ofac_files(sdn_file, alt_file, add_file, output_file):
    """Parse OFAC CSV files and create unified import file"""
    
    print("📂 Reading OFAC files...")
    
    # Read alternate names (aliases)
    aliases = {}
    with open(alt_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ent_num = row.get('Ent_Num', '').strip()
            alt_name = row.get('Alt_Name', '').strip()
            if ent_num and alt_name:
                if ent_num not in aliases:
                    aliases[ent_num] = []
                aliases[ent_num].append(alt_name)
    
    print(f"✓ Loaded {len(aliases)} entities with aliases")
    
    # Read addresses
    addresses = {}
    with open(add_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ent_num = row.get('Ent_Num', '').strip()
            country = row.get('Country', '').strip()
            if ent_num and country:
                if ent_num not in addresses:
                    addresses[ent_num] = []
                addresses[ent_num].append(country)
    
    print(f"✓ Loaded {len(addresses)} entities with addresses")
    
    # Read main SDN file and combine
    entities = []
    with open(sdn_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            ent_num = row.get('Ent_Num', '').strip()
            name = row.get('SDN_Name', '').strip()
            sdn_type = row.get('SDN_Type', '').strip().lower()
            program = row.get('Program', '').strip()
            
            # Determine entity type
            entity_type = 'individual' if sdn_type == 'individual' else 'entity'
            
            # Get aliases for this entity
            entity_aliases = aliases.get(ent_num, [])
            
            # Get nationalities from addresses
            nationalities = list(set(addresses.get(ent_num, [])))
            
            entity = {
                'name': name,
                'type': entity_type,
                'aliases': ';'.join(entity_aliases) if entity_aliases else '',
                'nationality': ','.join(nationalities) if nationalities else '',
                'program': program,
                'date_listed': ''  # OFAC doesn't provide this in CSV
            }
            
            entities.append(entity)
    
    print(f"✓ Parsed {len(entities)} entities from SDN list")
    
    # Write to output CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'type', 'aliases', 'nationality', 'program', 'date_listed'])
        writer.writeheader()
        writer.writerows(entities)
    
    print(f"✅ Created unified file: {output_file}")
    print(f"   Total entities: {len(entities)}")
    
    return len(entities)

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("""
Usage: python3 parse_ofac.py <SDN.CSV> <ALT.CSV> <ADD.CSV> <output.csv>

Example:
  python3 parse_ofac.py data/SDN.CSV data/ALT.CSV data/ADD.CSV data/ofac_unified.csv
        """)
        sys.exit(1)
    
    sdn_file = sys.argv[1]
    alt_file = sys.argv[2]
    add_file = sys.argv[3]
    output_file = sys.argv[4]
    
    parse_ofac_files(sdn_file, alt_file, add_file, output_file)
