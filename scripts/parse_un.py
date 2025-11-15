#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import json
import sys
import re

def clean_date(date_str):
    """Clean date format - remove timezone info"""
    if not date_str:
        return None
    # Remove timezone part: "2015-04-07-04:00" -> "2015-04-07"
    return re.sub(r'(-\d{2}:\d{2})$', '', date_str)

def parse_un_xml(xml_file: str, output_file: str):
    print("\n" + "="*70)
    print("UN Consolidated List Parser")
    print("="*70 + "\n")
    
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    entities = []
    stats = {'total': 0, 'individuals': 0, 'entities': 0, 'with_dob': 0}
    
    print("Parsing individuals...")
    for individual in root.findall('.//INDIVIDUAL'):
        stats['total'] += 1
        stats['individuals'] += 1
        
        un_ref = individual.find('REFERENCE_NUMBER')
        un_ref = un_ref.text if un_ref is not None else None
        
        first_name = individual.find('FIRST_NAME')
        first_name = first_name.text if first_name is not None else ''
        
        second_name = individual.find('SECOND_NAME')
        second_name = second_name.text if second_name is not None else ''
        
        third_name = individual.find('THIRD_NAME')
        third_name = third_name.text if third_name is not None else ''
        
        fourth_name = individual.find('FOURTH_NAME')
        fourth_name = fourth_name.text if fourth_name is not None else ''
        
        name_parts = [first_name, second_name, third_name, fourth_name]
        full_name = ' '.join([p for p in name_parts if p]).strip()
        
        parsed_first = first_name or None
        parsed_last = fourth_name or None
        parsed_middle = ' '.join([second_name, third_name]).strip() or None
        
        gender_elem = individual.find('GENDER')
        gender = 'unknown'
        if gender_elem is not None and gender_elem.text:
            gender = gender_elem.text.strip().lower()
        
        dob = None
        dob_text = None
        for dob_elem in individual.findall('.//INDIVIDUAL_DATE_OF_BIRTH'):
            year = dob_elem.find('YEAR')
            month = dob_elem.find('MONTH')
            day = dob_elem.find('DAY')
            
            if year is not None and year.text:
                stats['with_dob'] += 1
                y = year.text
                m = month.text if month is not None and month.text else '01'
                d = day.text if day is not None and day.text else '01'
                dob = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                dob_text = f"{d} {m} {y}"
                break
        
        pob = None
        pob_country = None
        for pob_elem in individual.findall('.//INDIVIDUAL_PLACE_OF_BIRTH'):
            city = pob_elem.find('CITY')
            country = pob_elem.find('COUNTRY')
            pob = city.text if city is not None and city.text else None
            pob_country = country.text if country is not None and country.text else None
            if pob:
                break
        
        nationalities = []
        for nat in individual.findall('.//NATIONALITY'):
            value = nat.find('VALUE')
            if value is not None and value.text:
                nationalities.append(value.text)
        
        aliases = []
        for alias in individual.findall('.//INDIVIDUAL_ALIAS'):
            alias_name = alias.find('ALIAS_NAME')
            if alias_name is not None and alias_name.text:
                aliases.append(alias_name.text)
        
        addresses = []
        countries = set()
        for address in individual.findall('.//INDIVIDUAL_ADDRESS'):
            street = address.find('STREET')
            city = address.find('CITY')
            country = address.find('COUNTRY')
            
            addr_obj = {}
            if street is not None and street.text:
                addr_obj['street'] = street.text
            if city is not None and city.text:
                addr_obj['city'] = city.text
            if country is not None and country.text:
                addr_obj['country'] = country.text
                countries.add(country.text)
            
            if addr_obj:
                addresses.append(addr_obj)
        
        listed_on = individual.find('LISTED_ON')
        date_listed = None
        if listed_on is not None and listed_on.text:
            date_listed = clean_date(listed_on.text.split('T')[0])
        
        comments = individual.find('COMMENTS1')
        remarks = comments.text if comments is not None and comments.text else None
        
        entity = {
            'entity_id': f"UN-{un_ref}" if un_ref else None,
            'entity_name': full_name,
            'first_name': parsed_first,
            'middle_name': parsed_middle,
            'last_name': parsed_last,
            'entity_type': 'individual',
            'gender': gender,
            'date_of_birth': dob,
            'date_of_birth_text': dob_text,
            'place_of_birth': pob,
            'place_of_birth_country': pob_country,
            'nationalities': nationalities,
            'aliases': aliases,
            'addresses': addresses,
            'countries': list(countries),
            'list_source': 'UN',
            'program': 'UN Security Council',
            'date_listed': date_listed,
            'remarks': remarks,
            'data_confidence': 1.0
        }
        
        entities.append(entity)
        
        if stats['total'] % 100 == 0:
            print(f"   Processed: {stats['total']} entities...")
    
    print("Parsing entities...")
    for entity_elem in root.findall('.//ENTITY'):
        stats['total'] += 1
        stats['entities'] += 1
        
        un_ref = entity_elem.find('REFERENCE_NUMBER')
        un_ref = un_ref.text if un_ref is not None else None
        
        first_name = entity_elem.find('FIRST_NAME')
        full_name = first_name.text if first_name is not None else ''
        
        aliases = []
        for alias in entity_elem.findall('.//ENTITY_ALIAS'):
            alias_name = alias.find('ALIAS_NAME')
            if alias_name is not None and alias_name.text:
                aliases.append(alias_name.text)
        
        addresses = []
        countries = set()
        for address in entity_elem.findall('.//ENTITY_ADDRESS'):
            street = address.find('STREET')
            city = address.find('CITY')
            country = address.find('COUNTRY')
            
            addr_obj = {}
            if street is not None and street.text:
                addr_obj['street'] = street.text
            if city is not None and city.text:
                addr_obj['city'] = city.text
            if country is not None and country.text:
                addr_obj['country'] = country.text
                countries.add(country.text)
            
            if addr_obj:
                addresses.append(addr_obj)
        
        listed_on = entity_elem.find('LISTED_ON')
        date_listed = None
        if listed_on is not None and listed_on.text:
            date_listed = clean_date(listed_on.text.split('T')[0])
        
        comments = entity_elem.find('COMMENTS1')
        remarks = comments.text if comments is not None and comments.text else None
        
        entity = {
            'entity_id': f"UN-{un_ref}" if un_ref else None,
            'entity_name': full_name,
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
            'countries': list(countries),
            'list_source': 'UN',
            'program': 'UN Security Council',
            'date_listed': date_listed,
            'remarks': remarks,
            'data_confidence': 1.0
        }
        
        entities.append(entity)
        
        if stats['total'] % 100 == 0:
            print(f"   Processed: {stats['total']} entities...")
    
    print("\n" + "="*70)
    print("Parsing Complete!")
    print("="*70)
    print(f"   Total entities: {stats['total']}")
    print(f"   Individuals: {stats['individuals']} ({stats['individuals']/stats['total']*100:.1f}%)")
    print(f"   Entities: {stats['entities']} ({stats['entities']/stats['total']*100:.1f}%)")
    print(f"   With DOB: {stats['with_dob']} ({stats['with_dob']/stats['total']*100:.1f}%)")
    print("="*70 + "\n")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved {len(entities)} entities to: {output_file}\n")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 parse_un.py <input.xml> <output.json>")
        sys.exit(1)
    parse_un_xml(sys.argv[1], sys.argv[2])
