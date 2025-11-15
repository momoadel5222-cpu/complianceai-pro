#!/usr/bin/env python3
"""
Full UN Consolidated List Parser
"""
import xml.etree.ElementTree as ET
import json
import re

def parse_date(date_str):
    """Parse UN date format"""
    if not date_str:
        return None, None
    
    # Extract YYYY-MM-DD
    match = re.match(r'(\d{4}-\d{2}-\d{2})', str(date_str))
    if match:
        return match.group(1), date_str
    
    return None, date_str

def parse_un_xml(xml_file, output_file):
    print("\n" + "="*70)
    print("UN CONSOLIDATED LIST - FULL PARSER")
    print("="*70 + "\n")
    
    print("📂 Parsing XML file...")
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    entities = []
    stats = {
        'total': 0,
        'individuals': 0,
        'entities': 0,
        'with_aliases': 0,
        'with_dob': 0
    }
    
    # Parse all INDIVIDUALS
    for individual in root.findall('.//INDIVIDUAL'):
        stats['total'] += 1
        stats['individuals'] += 1
        
        # Basic info
        un_list_type = individual.find('UN_LIST_TYPE')
        reference_number = individual.find('REFERENCE_NUMBER')
        
        # Name parsing
        first_name = individual.find('.//FIRST_NAME')
        second_name = individual.find('.//SECOND_NAME')
        third_name = individual.find('.//THIRD_NAME')
        fourth_name = individual.find('.//FOURTH_NAME')
        
        first = first_name.text if first_name is not None else None
        middle_parts = []
        if second_name is not None and second_name.text:
            middle_parts.append(second_name.text)
        if third_name is not None and third_name.text:
            middle_parts.append(third_name.text)
        last = fourth_name.text if fourth_name is not None else None
        
        middle = ' '.join(middle_parts) if middle_parts else None
        
        # Build full name
        name_parts = [p for p in [first, middle, last] if p]
        full_name = ' '.join(name_parts) if name_parts else 'UNKNOWN'
        
        # Date of birth
        dob_elem = individual.find('.//DATE_OF_BIRTH')
        dob_text = dob_elem.text if dob_elem is not None else None
        dob, dob_original = parse_date(dob_text)
        if dob:
            stats['with_dob'] += 1
        
        # Place of birth
        pob_elem = individual.find('.//CITY_OF_BIRTH')
        pob = pob_elem.text if pob_elem is not None else None
        pob_country_elem = individual.find('.//COUNTRY_OF_BIRTH')
        pob_country = pob_country_elem.text if pob_country_elem is not None else None
        
        # Gender
        gender = 'unknown'
        title = individual.find('.//TITLE')
        if title is not None and title.text:
            if title.text.lower() in ['mr', 'mr.']:
                gender = 'male'
            elif title.text.lower() in ['ms', 'ms.', 'mrs', 'mrs.']:
                gender = 'female'
        
        # Nationalities
        nationalities = []
        for nat in individual.findall('.//NATIONALITY'):
            if nat.text:
                nationalities.append(nat.text)
        
        # Aliases
        aliases = []
        for alias in individual.findall('.//INDIVIDUAL_ALIAS'):
            alias_name_elem = alias.find('.//ALIAS_NAME')
            if alias_name_elem is not None and alias_name_elem.text:
                aliases.append(alias_name_elem.text)
        
        if aliases:
            stats['with_aliases'] += 1
        
        # Addresses
        addresses = []
        for addr in individual.findall('.//INDIVIDUAL_ADDRESS'):
            street = addr.find('.//STREET')
            city = addr.find('.//CITY')
            country = addr.find('.//COUNTRY')
            
            addr_obj = {}
            if street is not None and street.text:
                addr_obj['street'] = street.text
            if city is not None and city.text:
                addr_obj['city'] = city.text
            if country is not None and country.text:
                addr_obj['country'] = country.text
            
            if addr_obj:
                addresses.append(addr_obj)
        
        # Comments
        comments_elem = individual.find('.//COMMENTS1')
        comments = comments_elem.text if comments_elem is not None else None
        
        entity = {
            'entity_id': reference_number.text if reference_number is not None else None,
            'entity_name': full_name,
            'first_name': first,
            'middle_name': middle,
            'last_name': last,
            'entity_type': 'individual',
            'gender': gender,
            'date_of_birth': dob,
            'date_of_birth_text': dob_original,
            'place_of_birth': pob,
            'place_of_birth_country': pob_country,
            'nationalities': nationalities,
            'aliases': aliases,
            'addresses': addresses,
            'countries': list(set([a.get('country') for a in addresses if a.get('country')])),
            'list_source': 'UN',
            'program': un_list_type.text if un_list_type is not None else 'UN Consolidated',
            'remarks': comments
        }
        
        entities.append(entity)
        
        if stats['total'] % 1000 == 0:
            print(f"   Processing: {stats['total']} entities...")
    
    # Parse all ENTITIES
    for entity_elem in root.findall('.//ENTITY'):
        stats['total'] += 1
        stats['entities'] += 1
        
        un_list_type = entity_elem.find('UN_LIST_TYPE')
        reference_number = entity_elem.find('REFERENCE_NUMBER')
        
        # Entity name
        first_name = entity_elem.find('.//FIRST_NAME')
        name = first_name.text if first_name is not None else 'UNKNOWN'
        
        # Aliases
        aliases = []
        for alias in entity_elem.findall('.//ENTITY_ALIAS'):
            alias_name_elem = alias.find('.//ALIAS_NAME')
            if alias_name_elem is not None and alias_name_elem.text:
                aliases.append(alias_name_elem.text)
        
        if aliases:
            stats['with_aliases'] += 1
        
        # Addresses
        addresses = []
        for addr in entity_elem.findall('.//ENTITY_ADDRESS'):
            street = addr.find('.//STREET')
            city = addr.find('.//CITY')
            country = addr.find('.//COUNTRY')
            
            addr_obj = {}
            if street is not None and street.text:
                addr_obj['street'] = street.text
            if city is not None and city.text:
                addr_obj['city'] = city.text
            if country is not None and country.text:
                addr_obj['country'] = country.text
            
            if addr_obj:
                addresses.append(addr_obj)
        
        # Comments
        comments_elem = entity_elem.find('.//COMMENTS1')
        comments = comments_elem.text if comments_elem is not None else None
        
        entity = {
            'entity_id': reference_number.text if reference_number is not None else None,
            'entity_name': name,
            'first_name': None,
            'middle_name': None,
            'last_name': None,
            'entity_type': 'entity',
            'gender': 'unknown',
            'date_of_birth': None,
            'date_of_birth_text': None,
            'place_of_birth': None,
            'place_of_birth_country': None,
            'nationalities': [],
            'aliases': aliases,
            'addresses': addresses,
            'countries': list(set([a.get('country') for a in addresses if a.get('country')])),
            'list_source': 'UN',
            'program': un_list_type.text if un_list_type is not None else 'UN Consolidated',
            'remarks': comments
        }
        
        entities.append(entity)
        
        if stats['total'] % 1000 == 0:
            print(f"   Processing: {stats['total']} entities...")
    
    print(f"\n{'='*70}")
    print("PARSING COMPLETE!")
    print(f"{'='*70}")
    print(f"   Total entities: {stats['total']}")
    print(f"   Individuals: {stats['individuals']} ({stats['individuals']/stats['total']*100:.1f}%)")
    print(f"   Entities: {stats['entities']} ({stats['entities']/stats['total']*100:.1f}%)")
    print(f"   With aliases: {stats['with_aliases']} ({stats['with_aliases']/stats['total']*100:.1f}%)")
    print(f"   With DOB: {stats['with_dob']} ({stats['with_dob']/stats['total']*100:.1f}%)")
    print(f"{'='*70}\n")
    
    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved {len(entities)} entities to: {output_file}\n")
    return entities

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("Usage: python3 parse_un_full.py <un_consolidated.xml> <output.json>")
        sys.exit(1)
    
    parse_un_xml(sys.argv[1], sys.argv[2])
