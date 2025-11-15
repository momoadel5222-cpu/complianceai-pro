#!/usr/bin/env python3
"""
Fixed OFAC Parser for headerless CSV files
"""
import csv
import re
import json

def parse_ofac_fixed(sdn_file: str, alt_file: str, add_file: str, output_file: str):
    print("\n" + "="*70)
    print("Enhanced OFAC Parser - Fixed Version")
    print("="*70 + "\n")
    
    # Read aliases (no headers)
    print("Loading aliases...")
    aliases_map = {}
    with open(alt_file, 'r', encoding='latin-1') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 4:
                continue
            ent_num = row[0].strip()
            alt_name = row[3].strip()  # Column 4 is the alias name
            if ent_num and alt_name and alt_name != '-0-':
                if ent_num not in aliases_map:
                    aliases_map[ent_num] = []
                aliases_map[ent_num].append(alt_name)
    
    print(f"   ✓ Loaded aliases for {len(aliases_map)} entities")
    
    # Read addresses (no headers)
    print("Loading addresses...")
    nationality_map = {}
    with open(add_file, 'r', encoding='latin-1') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 5:
                continue
            ent_num = row[0].strip()
            country = row[4].strip()  # Column 5 is country
            
            if ent_num and country and country != '-0-':
                if ent_num not in nationality_map:
                    nationality_map[ent_num] = set()
                nationality_map[ent_num].add(country)
    
    print(f"   ✓ Loaded nationalities for {len(nationality_map)} entities")
    
    # Read main SDN file (no headers)
    print("Parsing main SDN file...\n")
    entities = []
    stats = {'total': 0, 'with_parsed_name': 0, 'with_dob': 0, 'individuals': 0}
    
    with open(sdn_file, 'r', encoding='latin-1') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 12:
                continue
            
            stats['total'] += 1
            
            ent_num = row[0].strip()
            full_name = row[1].strip()
            sdn_type = row[2].strip().lower()
            program = row[3].strip()
            remarks = row[11].strip() if len(row) > 11 else ''
            
            # Parse name: "LASTNAME, Firstname"
            first_name, middle_name, last_name = None, None, None
            if ',' in full_name:
                parts = full_name.split(',', 1)
                last_name = parts[0].strip()
                rest = parts[1].strip() if len(parts) > 1 else ''
                name_parts = rest.split()
                first_name = name_parts[0] if name_parts else None
                middle_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else None
                stats['with_parsed_name'] += 1
            
            # Extract DOB from remarks
            dob = None
            if remarks and remarks != '-0-':
                match = re.search(r'DOB\s+(\d{1,2}\s+\w+\s+\d{4})', remarks, re.IGNORECASE)
                if match:
                    stats['with_dob'] += 1
                    dob = match.group(1)
            
            if sdn_type == 'individual':
                stats['individuals'] += 1
            
            entity = {
                'entity_id': ent_num,
                'entity_name': full_name,
                'first_name': first_name,
                'middle_name': middle_name,
                'last_name': last_name,
                'entity_type': 'individual' if sdn_type == 'individual' else 'entity',
                'date_of_birth_text': dob,
                'nationalities': list(nationality_map.get(ent_num, set())),
                'aliases': aliases_map.get(ent_num, []),
                'list_source': 'OFAC',
                'program': program if program != '-0-' else None,
                'remarks': remarks if remarks != '-0-' else None
            }
            
            entities.append(entity)
            
            if stats['total'] % 2000 == 0:
                print(f"   Processed: {stats['total']} entities...")
    
    print("\n" + "="*70)
    print("Parsing Complete!")
    print("="*70)
    print(f"   Total entities: {stats['total']}")
    print(f"   Individuals: {stats['individuals']} ({stats['individuals']/stats['total']*100:.1f}%)")
    print(f"   Names parsed: {stats['with_parsed_name']} ({stats['with_parsed_name']/stats['total']*100:.1f}%)")
    print(f"   DOB found: {stats['with_dob']} ({stats['with_dob']/stats['total']*100:.1f}%)")
    print("="*70 + "\n")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved {len(entities)} entities to: {output_file}\n")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 5:
        print("Usage: python3 parse_ofac_fixed.py <sdn.csv> <alt.csv> <add.csv> <output.json>")
        sys.exit(1)
    parse_ofac_fixed(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
