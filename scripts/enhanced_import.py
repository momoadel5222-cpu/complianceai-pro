#!/usr/bin/env python3
import requests, csv, json, time
import xml.etree.ElementTree as ET
from datetime import datetime
from supabase import create_client

SUPABASE_URL = "https://qwacsyreyuhhlvzcwhnw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7es"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def download_file(url, filename):
    print(f"📥 {filename}...")
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(8192):
                if chunk: f.write(chunk)
        print(f"✅ {filename}")
        return filename
    except Exception as e:
        print(f"❌ {e}")
        return None

def batch_insert(entities):
    if not entities: return 0
    try:
        supabase.table('sanctions_list').insert(entities).execute()
        return len(entities)
    except Exception as e:
        print(f"⚠️ {e}")
        ok = 0
        for e in entities:
            try:
                supabase.table('sanctions_list').insert(e).execute()
                ok += 1
            except: pass
        return ok

def import_ofac():
    print("\n🇺🇸 OFAC")
    url = 'https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/CONSOLIDATED.CSV'
    f = download_file(url, '../data/ofac.csv')
    if not f: return 0
    entities, total = [], 0
    with open(f, 'r', encoding='utf-8', errors='ignore') as file:
        for row in csv.DictReader(file):
            name = row.get('name', row.get('Name', ''))
            if not name: continue
            entities.append({
                'entity_name': name,
                'entity_type': 'individual' if 'individual' in row.get('type','').lower() else 'entity',
                'list_source': 'OFAC',
                'program': row.get('programs', ''),
                'is_pep': False,
                'last_updated_date': datetime.now().date().isoformat()
            })
            if len(entities) >= 100:
                total += batch_insert(entities)
                print(f"  ✓ {total}")
                entities = []
                time.sleep(0.1)
    if entities: total += batch_insert(entities)
    print(f"✅ {total}")
    return total

def import_un():
    print("\n�� UN")
    url = 'https://scsanctions.un.org/resources/xml/en/consolidated.xml'
    f = download_file(url, '../data/un.xml')
    if not f: return 0
    tree = ET.parse(f)
    root = tree.getroot()
    entities, total = [], 0
    ns = '{http://www.un.org/sc/xml/1.0}'
    for ind in root.findall(f'.//{ns}INDIVIDUAL'):
        fn = ind.find(f'.//{ns}FIRST_NAME')
        ln = ind.find(f'.//{ns}SECOND_NAME')
        name = f"{fn.text if fn is not None and fn.text else ''} {ln.text if ln is not None and ln.text else ''}".strip()
        if name:
            entities.append({'entity_name':name,'entity_type':'individual','list_source':'UN','program':'UN Sanctions','is_pep':False})
            total += 1
            if len(entities) >= 100:
                batch_insert(entities)
                print(f"  ✓ {total}")
                entities = []
                time.sleep(0.1)
    for ent in root.findall(f'.//{ns}ENTITY'):
        ne = ent.find(f'.//{ns}FIRST_NAME')
        name = ne.text if ne is not None and ne.text else ''
        if name:
            entities.append({'entity_name':name,'entity_type':'entity','list_source':'UN','program':'UN Sanctions','is_pep':False})
            total += 1
            if len(entities) >= 100:
                batch_insert(entities)
                print(f"  ✓ {total}")
                entities = []
                time.sleep(0.1)
    if entities: batch_insert(entities)
    print(f"✅ {total}")
    return total

def import_peps():
    print("\n🎩 PEPs (10-15 min)")
    url = 'https://data.opensanctions.org/datasets/latest/peps/entities.ftm.json'
    try:
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
    except:
        print("❌ Failed")
        return 0
    entities, total = [], 0
    for line in r.iter_lines():
        if not line or total >= 50000: break
        try:
            d = json.loads(line)
            p = d.get('properties', {})
            n = p.get('name', [])
            if not n or not n[0]: continue
            entities.append({
                'entity_name': n[0],
                'entity_type': 'individual',
                'list_source': 'OpenSanctions-PEP',
                'program': 'PEP',
                'is_pep': True,
                'pep_level': 'direct',
                'position': ', '.join(p.get('position',[])[:2]),
                'jurisdiction': p.get('country',[''])[0],
                'nationalities': p.get('country',[])[:3]
            })
            total += 1
            if len(entities) >= 100:
                batch_insert(entities)
                print(f"  ✓ {total}")
                entities = []
                time.sleep(0.05)
        except: continue
    if entities: batch_insert(entities)
    print(f"✅ {total}")
    return total

def stats():
    print("\n📊 STATS")
    r = supabase.table('sanctions_list').select('id',count='exact').execute()
    t = r.count if hasattr(r,'count') else 0
    p = supabase.table('sanctions_list').select('id',count='exact').eq('is_pep',True).execute()
    peps = p.count if hasattr(p,'count') else 0
    print(f"Total: {t:,}\nPEPs: {peps:,}\nSanctions: {t-peps:,}")

def main():
    print("="*60)
    print("🚀 IMPORT")
    print("="*60)
    print("1. OFAC\n2. UN\n3. PEPs\n4. ALL\n5. Stats")
    c = input("\nChoice: ").strip()
    start = time.time()
    if c=='1': import_ofac()
    elif c=='2': import_un()
    elif c=='3': import_peps()
    elif c=='4':
        import_ofac()
        import_un()
        import_peps()
    elif c=='5':
        stats()
        return
    print(f"\n⏱️ {(time.time()-start)/60:.1f} min")
    stats()
    print("\n✅ DONE")

if __name__=='__main__':
    main()
