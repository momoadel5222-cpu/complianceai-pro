#!/usr/bin/env python3
"""
Download and parse PEP (Politically Exposed Persons) data
"""
import os
import csv

os.makedirs('data', exist_ok=True)

print("=" * 60)
print("🌍 Creating PEP Data")
print("=" * 60)

# Egypt Government Officials (PEPs)
egypt_peps = [
    {
        'entity_name': 'Mostafa Madbouly',
        'entity_type': 'individual',
        'list_source': 'PEP',
        'program': 'Egypt Prime Minister',
        'jurisdiction': 'Egypt',
        'nationalities': 'Egyptian',
        'aliases': 'Mostafa Kamal Madbouly|Moustafa Madbouly|Dr. Mostafa Madbouly',
        'position': 'Prime Minister of Egypt',
        'is_pep': 'true',
        'pep_level': 'National Leader',
        'remarks': 'Current Prime Minister of Egypt since 2018'
    },
    {
        'entity_name': 'Abdel Fattah el-Sisi',
        'entity_type': 'individual',
        'list_source': 'PEP',
        'program': 'Egypt President',
        'jurisdiction': 'Egypt',
        'nationalities': 'Egyptian',
        'aliases': 'Abdel Fattah Saeed Hussein Khalil el-Sisi|Abdel-Fattah el-Sissi|Al-Sisi',
        'position': 'President of Egypt',
        'is_pep': 'true',
        'pep_level': 'Head of State',
        'remarks': 'Current President of Egypt since 2014'
    },
    {
        'entity_name': 'Sameh Shoukry',
        'entity_type': 'individual',
        'list_source': 'PEP',
        'program': 'Egypt Foreign Affairs',
        'jurisdiction': 'Egypt',
        'nationalities': 'Egyptian',
        'aliases': 'Sameh Hassan Shoukry',
        'position': 'Minister of Foreign Affairs',
        'is_pep': 'true',
        'pep_level': 'National Leader',
        'remarks': 'Egyptian Minister of Foreign Affairs'
    }
]

output_file = 'data/pep_data.csv'
fieldnames = ['entity_name', 'entity_type', 'list_source', 'program', 
              'jurisdiction', 'nationalities', 'aliases', 'position', 
              'is_pep', 'pep_level', 'remarks']

print(f"\n💾 Saving {len(egypt_peps)} PEP records to {output_file}...")

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(egypt_peps)

print(f"✅ Saved to {output_file}")
print("\n📊 Sample records:")
for i, pep in enumerate(egypt_peps, 1):
    print(f"{i}. {pep['entity_name']} - {pep['position']}")

print("\n" + "=" * 60)
print(f"✅ Total PEP records: {len(egypt_peps)}")
print("=" * 60)
