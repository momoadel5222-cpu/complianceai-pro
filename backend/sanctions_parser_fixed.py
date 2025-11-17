#!/usr/bin/env python3
"""
Fixed Sanctions Data Parser - All Sources Working
Correctly parses OFAC CSV, UN XML, and UK XML formats
"""
import os
import csv
import xml.etree.ElementTree as ET

print("=" * 60)
print("🌍 Parsing Downloaded Sanctions Lists")
print("=" * 60)

def parse_ofac_csv(filepath):
    """
    Parse OFAC CSV format:
    Column 0: ID
    Column 1: Name (what we want)
    Column 2: Type (Individual/Entity)
    Column 3: Country
    Column 4: Designation
    Column 11: Additional remarks
    """
    print(f"\n📊 Parsing OFAC data...")
    records = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            for row in reader:
                if len(row) < 12:
                    continue
                
                entity_name = row[1].strip().strip('"')
                entity_type_raw = row[2].strip().strip('"')
                country = row[3].strip().strip('"')
                designation = row[4].strip().strip('"')
                remarks = row[11].strip().strip('"') if len(row) > 11 else ''
                
                if not entity_name or entity_name == '-0-' or entity_name == '':
                    continue
                
                entity_type = 'individual' if 'individual' in entity_type_raw.lower() else 'entity'
                program = f"{designation} ({country})" if designation and designation != '-0-' else country
                
                records.append({
                    'entity_name': entity_name,
                    'entity_type': entity_type,
                    'list_source': 'OFAC',
                    'program': program if program != '-0-' else '',
                    'jurisdiction': country if country != '-0-' else '',
                    'remarks': remarks if remarks != '-0-' else '',
                    'is_pep': False
                })
        
        print(f"  ✅ Parsed {len(records)} OFAC records")
        return records
    except Exception as e:
        print(f"  ❌ Error parsing OFAC: {e}")
        return []

def parse_un_xml(filepath):
    """
    Parse UN XML - NO NAMESPACE (just plain tags)
    """
    print(f"\n📊 Parsing UN data...")
    records = []
    
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # Find individuals - NO namespace prefix
        all_individuals = root.findall('.//INDIVIDUAL')
        all_entities = root.findall('.//ENTITY')
        
        print(f"  Found {len(all_individuals)} individuals and {len(all_entities)} entities in UN XML")
        
        # Parse individuals
        for entry in all_individuals:
            # Get name fields without namespace
            first = entry.find('.//FIRST_NAME')
            second = entry.find('.//SECOND_NAME')
            third = entry.find('.//THIRD_NAME')
            fourth = entry.find('.//FOURTH_NAME')
            
            name_parts = []
            for n in [first, second, third, fourth]:
                if n is not None and n.text and n.text.strip():
                    name_parts.append(n.text.strip())
            
            if name_parts:
                un_list = entry.find('.//UN_LIST_TYPE')
                program = un_list.text if un_list is not None and un_list.text else ''
                
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
        for entry in all_entities:
            first = entry.find('.//FIRST_NAME')
            
            if first is not None and first.text:
                un_list = entry.find('.//UN_LIST_TYPE')
                program = un_list.text if un_list is not None and un_list.text else ''
                
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
        print(f"  ❌ Error parsing UN: {e}")
        import traceback
        traceback.print_exc()
        return []

def parse_uk_xml(filepath):
    """
    Parse UK Sanctions XML
    """
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
                    regime = regime_elem.text if regime_elem is not None and regime_elem.text else ''
                    
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
        print(f"  ❌ Error parsing UK: {e}")
        return []

# Main execution
all_records = []

if os.path.exists('sanctions_data/ofac.csv'):
    all_records.extend(parse_ofac_csv('sanctions_data/ofac.csv'))
else:
    print("\n⚠️  ofac.csv not found")

if os.path.exists('sanctions_data/un.xml'):
    all_records.extend(parse_un_xml('sanctions_data/un.xml'))
else:
    print("\n⚠️  un.xml not found")

if os.path.exists('sanctions_data/uk.xml'):
    all_records.extend(parse_uk_xml('sanctions_data/uk.xml'))
else:
    print("\n⚠️  uk.xml not found")

# Export combined CSV
if all_records:
    output_file = 'sanctions_data/combined_sanctions_complete.csv'
    print(f"\n💾 Exporting {len(all_records)} total records...")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['entity_name', 'entity_type', 'list_source', 'program', 'jurisdiction', 'remarks', 'is_pep']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)
    
    print(f"✅ Export complete: {output_file}")
    print(f"\n📊 Final Summary:")
    print(f"  - OFAC: {sum(1 for r in all_records if r['list_source'] == 'OFAC')} records")
    print(f"  - UN: {sum(1 for r in all_records if r['list_source'] == 'UN')} records")
    print(f"  - UK: {sum(1 for r in all_records if r['list_source'] == 'UK')} records")
    print(f"  - Total: {len(all_records)} records")
    
    file_size = os.path.getsize(output_file) / 1024 / 1024
    print(f"  - File size: {file_size:.1f} MB")
    
    print(f"\n🎯 Ready to import into Supabase!")
else:
    print("\n❌ No records parsed from any source")

print("=" * 60)
