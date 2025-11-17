#!/usr/bin/env python3
import os
import requests
import xml.etree.ElementTree as ET
import csv

os.makedirs('sanctions_data', exist_ok=True)

print("=" * 60)
print("🌍 Downloading & Parsing Sanctions Lists")
print("=" * 60)

def parse_ofac_csv(filepath):
    """Parse OFAC CSV - columns: ID, Name, Type, Country, Designation, ..., Remarks"""
    print(f"\n📊 Parsing OFAC data...")
    records = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 12:
                    continue
                
                # Extract fields by position
                entity_id = row[0].strip()
                entity_name = row[1].strip().strip('"')
                entity_type_raw = row[2].strip().strip('"')
                country = row[3].strip().strip('"')
                designation = row[4].strip().strip('"')
                remarks = row[11].strip().strip('"')
                
                if not entity_name or entity_name == '-0-':
                    continue
                
                # Determine entity type
                entity_type = 'individual' if 'individual' in entity_type_raw.lower() else 'entity'
                
                # Combine designation and country as program
                program = f"{designation} ({country})" if designation and designation != '-0-' else country
                
                records.append({
                    'entity_name': entity_name,
                    'entity_type': entity_type,
                    'list_source': 'OFAC',
                    'program': program,
                    'jurisdiction': country if country != '-0-' else '',
                    'remarks': remarks if remarks != '-0-' else '',
                    'is_pep': False
                })
        
        print(f"  ✅ Parsed {len(records)} OFAC records")
        return records
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

def parse_un_xml(filepath):
    """Parse UN XML"""
    print(f"\n📊 Parsing UN data...")
    records = []
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # Parse individuals
        for entry in root.findall('.//{http://www.un.org/sanctions/1.0}INDIVIDUAL'):
            first = entry.find('.//{http://www.un.org/sanctions/1.0}FIRST_NAME')
            second = entry.find('.//{http://www.un.org/sanctions/1.0}SECOND_NAME')
            third = entry.find('.//{http://www.un.org/sanctions/1.0}THIRD_NAME')
            fourth = entry.find('.//{http://www.un.org/sanctions/1.0}FOURTH_NAME')
            
            name_parts = []
            for n in [first, second, third, fourth]:
                if n is not None and n.text:
                    name_parts.append(n.text.strip())
            
            if name_parts:
                un_list = entry.find('.//{http://www.un.org/sanctions/1.0}UN_LIST_TYPE')
                program = un_list.text if un_list is not None else ''
                
                records.append({
                    'entity_name': ' '.join(name_parts),
                    'entity_type': 'individual',
                    'list_source': 'UN',
                    'program': program,
                    'jurisdiction': '',
                    'remarks': '',
                    'is_pep': False
                })
        
        # Parse entities
        for entry in root.findall('.//{http://www.un.org/sanctions/1.0}ENTITY'):
            first = entry.find('.//{http://www.un.org/sanctions/1.0}FIRST_NAME')
            if first is not None and first.text:
                un_list = entry.find('.//{http://www.un.org/sanctions/1.0}UN_LIST_TYPE')
                program = un_list.text if un_list is not None else ''
                
                records.append({
                    'entity_name': first.text.strip(),
                    'entity_type': 'entity',
                    'list_source': 'UN',
                    'program': program,
                    'jurisdiction': '',
                    'remarks': '',
                    'is_pep': False
                })
        
        print(f"  ✅ Parsed {len(records)} UN records")
        return records
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []

def parse_uk_xml(filepath):
    """Parse UK XML"""
    print(f"\n📊 Parsing UK data...")
    records = []
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        for designation in root.findall('.//Designation'):
            names = designation.findall('.//Name')
            for name_elem in names:
                name6 = name_elem.find('.//Name6')
                if name6 is not None and name6.text:
                    entity_type_elem = designation.find('.//EntitySubjectType')
                    entity_type = 'individual' if entity_type_elem is not None and 'Individual' in entity_type_elem.text else 'entity'
                    
                    regime_elem = designation.find('.//RegimeName')
                    regime = regime_elem.text if regime_elem is not None else ''
                    
                    records.append({
                        'entity_name': name6.text.strip(),
                        'entity_type': entity_type,
                        'list_source': 'UK',
                        'program': regime,
                        'jurisdiction': '',
                        'remarks': '',
                        'is_pep': False
                    })
        
        print(f"  ✅ Parsed {len(records)} UK records")
        return records
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []

# Parse existing downloaded files
all_records = []

if os.path.exists('sanctions_data/ofac.csv'):
    all_records.extend(parse_ofac_csv('sanctions_data/ofac.csv'))

if os.path.exists('sanctions_data/un.xml'):
    all_records.extend(parse_un_xml('sanctions_data/un.xml'))

if os.path.exists('sanctions_data/uk.xml'):
    all_records.extend(parse_uk_xml('sanctions_data/uk.xml'))

# Export combined CSV
if all_records:
    output_file = 'sanctions_data/combined_sanctions_final.csv'
    print(f"\n💾 Exporting {len(all_records)} total records...")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['entity_name', 'entity_type', 'list_source', 'program', 'jurisdiction', 'remarks', 'is_pep']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)
    
    print(f"✅ Export complete: {output_file}")
    print(f"\n📊 Summary:")
    print(f"  - OFAC: {sum(1 for r in all_records if r['list_source'] == 'OFAC')} records")
    print(f"  - UN: {sum(1 for r in all_records if r['list_source'] == 'UN')} records")
    print(f"  - UK: {sum(1 for r in all_records if r['list_source'] == 'UK')} records")
    print(f"  - Total: {len(all_records)} records")
    
    # Show file size
    import os
    file_size = os.path.getsize(output_file) / 1024 / 1024
    print(f"  - File size: {file_size:.1f} MB")
    
    print(f"\n🎯 Next: Import {output_file} into Supabase!")
else:
    print("\n❌ No records parsed")

print("=" * 60)
