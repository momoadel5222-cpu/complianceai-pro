#!/usr/bin/env python3
"""
Download and parse sanctions data from official sources
Outputs a clean CSV ready for Supabase import
"""

import os
import requests
import xml.etree.ElementTree as ET
import csv
from datetime import datetime

# Create output directory
os.makedirs('sanctions_data', exist_ok=True)

print("=" * 60)
print("🌍 Downloading Official Sanctions Lists")
print("=" * 60)

# URLs for sanctions data
SOURCES = {
    'OFAC': 'https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/CONSOLIDATED.XML',
    'UN': 'https://scsanctions.un.org/resources/xml/en/consolidated.xml',
    'UK': 'https://assets.publishing.service.gov.uk/media/674d4dd72d5a6a8dfc8dd92f/ConList.csv'
}

def download_file(url, filename):
    """Download file with progress"""
    print(f"\n📥 Downloading {filename}...")
    try:
        response = requests.get(url, timeout=120, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(f'sanctions_data/{filename}', 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"  Progress: {percent:.1f}%", end='\r')
        
        print(f"  ✅ Downloaded {filename} ({downloaded / 1024 / 1024:.1f} MB)")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def parse_ofac_xml(filepath):
    """Parse OFAC XML format"""
    print(f"\n📊 Parsing OFAC data...")
    records = []
    
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # Find all SDN entries
        for entry in root.findall('.//sdnEntry'):
            name_elem = entry.find('.//lastName')
            first_name_elem = entry.find('.//firstName')
            
            entity_name = ''
            if name_elem is not None and name_elem.text:
                entity_name = name_elem.text
                if first_name_elem is not None and first_name_elem.text:
                    entity_name = f"{first_name_elem.text} {entity_name}"
            
            if not entity_name:
                continue
            
            entity_type = entry.find('.//sdnType')
            entity_type = entity_type.text if entity_type is not None else 'Unknown'
            entity_type = 'individual' if entity_type.lower() == 'individual' else 'entity'
            
            # Get program
            program_list = entry.findall('.//program')
            program = ', '.join([p.text for p in program_list if p.text]) if program_list else ''
            
            # Get remarks
            remarks_elem = entry.find('.//remarks')
            remarks = remarks_elem.text if remarks_elem is not None else ''
            
            records.append({
                'entity_name': entity_name.strip(),
                'entity_type': entity_type,
                'list_source': 'OFAC',
                'program': program,
                'remarks': remarks,
                'is_pep': False
            })
        
        print(f"  ✅ Parsed {len(records)} OFAC records")
        return records
    except Exception as e:
        print(f"  ❌ Error parsing OFAC: {e}")
        return []

def parse_un_xml(filepath):
    """Parse UN XML format"""
    print(f"\n📊 Parsing UN data...")
    records = []
    
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # UN uses different namespace
        ns = {'un': 'http://www.un.org/sanctions/1.0'}
        
        for entry in root.findall('.//INDIVIDUAL', ns) + root.findall('.//ENTITY', ns):
            first_name = entry.find('.//FIRST_NAME', ns)
            second_name = entry.find('.//SECOND_NAME', ns)
            third_name = entry.find('.//THIRD_NAME', ns)
            fourth_name = entry.find('.//FOURTH_NAME', ns)
            un_list_type = entry.find('.//UN_LIST_TYPE', ns)
            comments = entry.find('.//COMMENTS1', ns)
            
            # Build full name
            name_parts = []
            for name_elem in [first_name, second_name, third_name, fourth_name]:
                if name_elem is not None and name_elem.text:
                    name_parts.append(name_elem.text)
            
            if not name_parts:
                continue
            
            entity_name = ' '.join(name_parts)
            entity_type = 'individual' if entry.tag.endswith('INDIVIDUAL') else 'entity'
            program = un_list_type.text if un_list_type is not None else ''
            remarks = comments.text if comments is not None else ''
            
            records.append({
                'entity_name': entity_name.strip(),
                'entity_type': entity_type,
                'list_source': 'UN',
                'program': program,
                'remarks': remarks,
                'is_pep': False
            })
        
        print(f"  ✅ Parsed {len(records)} UN records")
        return records
    except Exception as e:
        print(f"  ❌ Error parsing UN: {e}")
        return []

def parse_uk_csv(filepath):
    """Parse UK CSV format"""
    print(f"\n📊 Parsing UK data...")
    records = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('Name6', '') or row.get('Name', '')
                if not name:
                    continue
                
                entity_type = 'individual' if row.get('Group Type', '').lower() == 'individual' else 'entity'
                regime = row.get('Regime', '')
                
                records.append({
                    'entity_name': name.strip(),
                    'entity_type': entity_type,
                    'list_source': 'UK',
                    'program': regime,
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

# Download OFAC
if download_file(SOURCES['OFAC'], 'ofac.xml'):
    all_records.extend(parse_ofac_xml('sanctions_data/ofac.xml'))

# Download UN
if download_file(SOURCES['UN'], 'un.xml'):
    all_records.extend(parse_un_xml('sanctions_data/un.xml'))

# Download UK
if download_file(SOURCES['UK'], 'uk.csv'):
    all_records.extend(parse_uk_csv('sanctions_data/uk.csv'))

# Export combined CSV
if all_records:
    output_file = 'sanctions_data/combined_sanctions.csv'
    print(f"\n💾 Exporting {len(all_records)} total records to CSV...")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['entity_name', 'entity_type', 'list_source', 'program', 'remarks', 'is_pep']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)
    
    print(f"✅ Export complete: {output_file}")
    print(f"\n📊 Summary:")
    print(f"  - OFAC: {sum(1 for r in all_records if r['list_source'] == 'OFAC')} records")
    print(f"  - UN: {sum(1 for r in all_records if r['list_source'] == 'UN')} records")
    print(f"  - UK: {sum(1 for r in all_records if r['list_source'] == 'UK')} records")
    print(f"  - Total: {len(all_records)} records")
    print(f"\n🎯 Next step: Import {output_file} into Supabase")
else:
    print("\n❌ No records downloaded")

print("=" * 60)
