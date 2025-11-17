#!/usr/bin/env python3
import os
import requests
import xml.etree.ElementTree as ET
import csv

os.makedirs('sanctions_data', exist_ok=True)

print("=" * 60)
print("�� Downloading Official Sanctions Lists")
print("=" * 60)

SOURCES = {
    'OFAC': 'https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV',
    'UN': 'https://scsanctions.un.org/resources/xml/en/consolidated.xml',
    'UK': 'https://sanctionslist.fcdo.gov.uk/docs/UK-Sanctions-List.xml'
}

def download_file(url, filename):
    print(f"\n📥 Downloading {filename}...")
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        with open(f'sanctions_data/{filename}', 'wb') as f:
            f.write(response.content)
        size_mb = len(response.content) / 1024 / 1024
        print(f"  ✅ Downloaded {filename} ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def parse_ofac_csv(filepath):
    print(f"\n📊 Parsing OFAC data...")
    records = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('name', '') or row.get('NAME', '')
                if not name:
                    continue
                
                entity_type = row.get('type', '') or row.get('TYPE', '')
                entity_type = 'individual' if 'individual' in entity_type.lower() else 'entity'
                
                program = row.get('programs', '') or row.get('PROGRAMS', '')
                remarks = row.get('remarks', '') or row.get('REMARKS', '')
                
                records.append({
                    'entity_name': name.strip(),
                    'entity_type': entity_type,
                    'list_source': 'OFAC',
                    'program': program,
                    'remarks': remarks,
                    'is_pep': 'false'
                })
        print(f"  ✅ Parsed {len(records)} OFAC records")
        return records
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []

def parse_un_xml(filepath):
    print(f"\n📊 Parsing UN data...")
    records = []
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        for entry in root.findall('.//{http://www.un.org/sanctions/1.0}INDIVIDUAL'):
            first = entry.find('.//{http://www.un.org/sanctions/1.0}FIRST_NAME')
            second = entry.find('.//{http://www.un.org/sanctions/1.0}SECOND_NAME')
            third = entry.find('.//{http://www.un.org/sanctions/1.0}THIRD_NAME')
            
            name_parts = []
            for n in [first, second, third]:
                if n is not None and n.text:
                    name_parts.append(n.text)
            
            if name_parts:
                records.append({
                    'entity_name': ' '.join(name_parts).strip(),
                    'entity_type': 'individual',
                    'list_source': 'UN',
                    'program': '',
                    'remarks': '',
                    'is_pep': 'false'
                })
        
        for entry in root.findall('.//{http://www.un.org/sanctions/1.0}ENTITY'):
            first = entry.find('.//{http://www.un.org/sanctions/1.0}FIRST_NAME')
            if first is not None and first.text:
                records.append({
                    'entity_name': first.text.strip(),
                    'entity_type': 'entity',
                    'list_source': 'UN',
                    'program': '',
                    'remarks': '',
                    'is_pep': 'false'
                })
        
        print(f"  ✅ Parsed {len(records)} UN records")
        return records
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []

def parse_uk_xml(filepath):
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
                        'remarks': '',
                        'is_pep': 'false'
                    })
        
        print(f"  ✅ Parsed {len(records)} UK records")
        return records
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []

all_records = []

if download_file(SOURCES['OFAC'], 'ofac.csv'):
    all_records.extend(parse_ofac_csv('sanctions_data/ofac.csv'))

if download_file(SOURCES['UN'], 'un.xml'):
    all_records.extend(parse_un_xml('sanctions_data/un.xml'))

if download_file(SOURCES['UK'], 'uk.xml'):
    all_records.extend(parse_uk_xml('sanctions_data/uk.xml'))

if all_records:
    output_file = 'sanctions_data/combined_sanctions.csv'
    print(f"\n💾 Exporting {len(all_records)} total records...")
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['entity_name', 'entity_type', 'list_source', 'program', 'remarks', 'is_pep'])
        writer.writeheader()
        writer.writerows(all_records)
    print(f"✅ Done: {output_file}")
    print(f"\n📊 Summary:")
    print(f"  - OFAC: {sum(1 for r in all_records if r['list_source'] == 'OFAC')} records")
    print(f"  - UN: {sum(1 for r in all_records if r['list_source'] == 'UN')} records")
    print(f"  - UK: {sum(1 for r in all_records if r['list_source'] == 'UK')} records")
    print(f"  - Total: {len(all_records)} records")
    print(f"\n🎯 Next: Import {output_file} into Supabase")
else:
    print("\n❌ No records")

print("=" * 60)
