#!/usr/bin/env python3
"""
Enhanced OFAC Parser with DOB/POB/Gender extraction
"""
import csv
import re
import json
from typing import Dict, List, Optional, Tuple

def parse_date(date_str: str) -> Optional[str]:
    """Parse various date formats to YYYY-MM-DD"""
    if not date_str:
        return None
    
    months = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }
    
    # 12 Jul 1986 format
    match = re.search(r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})', date_str, re.IGNORECASE)
    if match:
        day, month, year = match.groups()
        month_num = months[month.title()]
        return f"{year}-{month_num}-{day.zfill(2)}"
    
    # Just year
    match = re.search(r'(\d{4})', date_str)
    if match:
        return f"{match.group(1)}-01-01"
    
    return None

def extract_dob(remarks: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract date of birth from remarks"""
    if not remarks:
        return None, None
    
    match = re.search(r'DOB\s+([^;]+)', remarks, re.IGNORECASE)
    if match:
        dob_text = match.group(1).strip()
        dob_parsed = parse_date(dob_text)
        return dob_parsed, dob_text
    
    return None, None

def extract_pob(remarks: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract place of birth from remarks"""
    if not remarks:
        return None, None
    
    match = re.search(r'POB\s+([^;]+)', remarks, re.IGNORECASE)
    if match:
        pob = match.group(1).strip()
        country_match = re.search(r',\s*([A-Z]{2})$', pob)
        country = country_match.group(1) if country_match else None
        return pob, country
    
    return None, None

def extract_gender(remarks: str, sdn_type: str) -> str:
    """Extract gender from remarks"""
    if sdn_type != 'individual':
        return 'unknown'
    
    if not remarks:
        return 'unknown'
    
    if re.search(r'\b(male|man|mr\.)\b', remarks, re.IGNORECASE):
        return 'male'
    elif re.search(r'\b(female|woman|mrs\.|ms\.)\b', remarks, re.IGNORECASE):
        return 'female'
    
    return 'unknown'

def parse_name(full_name: str) -> Dict[str, Optional[str]]:
    """Parse OFAC name format: 'LASTNAME, Firstname Middlename'"""
    if not full_name:
        return {'first_name': None, 'middle_name': None, 'last_name': None}
    
    if ',' in full_name:
        parts = full_name.split(',', 1)
        last_name = parts[0].strip()
        rest = parts[1].strip() if len(parts) > 1 else ''
        
        name_parts = rest.split()
        first_name = name_parts[0] if len(name_parts) > 0 else None
        middle_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else None
        
        return {
            'first_name': first_name,
            'middle_name': middle_name,
            'last_name': last_name
        }
    else:
        parts = full_name.split()
        if len(parts) == 1:
            return {'first_name': parts[0], 'middle_name': None, 'last_name': None}
        elif len(parts) == 2:
            return {'first_name': parts[0], 'middle_name': None, 'last_name': parts[1]}
        else:
            return {
                'first_name': parts[0],
                'middle_name': ' '.join(parts[1:-1]),
                'last_name': parts[-1]
            }

def parse_ofac_enhanced(sdn_file: str, alt_file: str, add_file: str, output_file: str):
    """Parse OFAC files with enhanced data extraction"""
    
    print(f"\n{'='*70}")
    print("Enhanced OFAC Parser - Phase 1")
    print(f"{'='*70}\n")
    
    # Read aliases
    print("Loading aliases...")
    aliases_map = {}
    with open(alt_file, 'r', encoding='latin-1') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ent_num = row.get('Ent_Num', '').strip()
            alt_name = row.get('Alt_Name', '').strip()
            if ent_num and alt_name:
                if ent_num not in aliases_map:
                    aliases_map[ent_num] = []
                aliases_map[ent_num].append(alt_name)
    
    print(f"   Loaded aliases for {len(aliases_map)} entities")
    
    # Read addresses
    print("Loading addresses...")
    address_map = {}
    nationality_map = {}
    with open(add_file, 'r', encoding='latin-1') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ent_num = row.get('Ent_Num', '').strip()
            address = row.get('Address', '').strip()
            country = row.get('Country', '').strip()
            
            if ent_num:
                if ent_num not in address_map:
                    address_map[ent_num] = []
                if address:
                    address_map[ent_num].append({
                        'street': address,
                        'country': country
                    })
                
                if country:
                    if ent_num not in nationality_map:
                        nationality_map[ent_num] = set()
                    nationality_map[ent_num].add(country)
    
    print(f"   Loaded addresses for {len(address_map)} entities")
    
    # Read main SDN file
    print("Parsing main SDN file...")
    entities = []
    stats = {
        'total': 0,
        'with_dob': 0,
        'with_pob': 0,
        'with_gender': 0,
        'with_parsed_name': 0
    }
    
    with open(sdn_file, 'r', encoding='latin-1') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            stats['total'] += 1
            
            ent_num = row.get('Ent_Num', '').strip()
            full_name = row.get('SDN_Name', '').strip()
            sdn_type = row.get('SDN_Type', '').strip().lower()
            program = row.get('Program', '').strip()
            title = row.get('Title', '').strip()
            remarks = row.get('Remarks', '').strip()
            
            # Parse name
            name_parts = parse_name(full_name)
            if name_parts['first_name'] or name_parts['last_name']:
                stats['with_parsed_name'] += 1
            
            # Extract biographical data
            dob, dob_text = extract_dob(remarks)
            pob, pob_country = extract_pob(remarks)
            gender = extract_gender(remarks, sdn_type)
            
            if dob:
                stats['with_dob'] += 1
            if pob:
                stats['with_pob'] += 1
            if gender != 'unknown':
                stats['with_gender'] += 1
            
            # Get aliases and addresses
            entity_aliases = aliases_map.get(ent_num, [])
            nationalities = list(nationality_map.get(ent_num, set()))
            addresses = address_map.get(ent_num, [])
            countries = list(set([addr['country'] for addr in addresses if addr.get('country')]))
            
            # Build entity record
            entity = {
                'entity_id': ent_num,
                'entity_name': full_name,
                'first_name': name_parts['first_name'],
                'middle_name': name_parts['middle_name'],
                'last_name': name_parts['last_name'],
                'entity_type': 'individual' if sdn_type == 'individual' else 'entity',
                'gender': gender,
                'date_of_birth': dob,
                'date_of_birth_text': dob_text,
                'place_of_birth': pob,
                'place_of_birth_country': pob_country,
                'nationalities': nationalities,
                'aliases': entity_aliases,
                'addresses': addresses,
                'countries': countries,
                'list_source': 'OFAC',
                'program': program,
                'remarks': remarks,
                'title': title
            }
            
            entities.append(entity)
            
            if stats['total'] % 1000 == 0:
                print(f"   Processing: {stats['total']} entities...")
    
    print(f"\n{'='*70}")
    print("Parsing Complete!")
    print(f"{'='*70}")
    print(f"   Total entities: {stats['total']}")
    print(f"   Names parsed: {stats['with_parsed_name']} ({stats['with_parsed_name']/stats['total']*100:.1f}%)")
    print(f"   DOB extracted: {stats['with_dob']} ({stats['with_dob']/stats['total']*100:.1f}%)")
    print(f"   POB extracted: {stats['with_pob']} ({stats['with_pob']/stats['total']*100:.1f}%)")
    print(f"   Gender detected: {stats['with_gender']} ({stats['with_gender']/stats['total']*100:.1f}%)")
    print(f"{'='*70}\n")
    
    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(entities)} enhanced entities to: {output_file}\n")
    
    return entities

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) != 5:
        print("Usage: python3 parse_ofac_enhanced.py <SDN.CSV> <ALT.CSV> <ADD.CSV> <output.json>")
        sys.exit(1)
    
    parse_ofac_enhanced(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
