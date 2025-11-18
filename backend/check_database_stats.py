#!/usr/bin/env python3
"""
Check database statistics
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

print("=" * 60)
print("📊 Database Statistics")
print("=" * 60)

try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    
    # Total records
    cursor.execute("SELECT COUNT(*) as total FROM sanctions_list;")
    total = cursor.fetchone()['total']
    print(f"\n📁 Total Records: {total:,}")
    
    # PEPs count
    cursor.execute("SELECT COUNT(*) as peps FROM sanctions_list WHERE is_pep = true;")
    peps = cursor.fetchone()['peps']
    print(f"👔 PEPs: {peps:,}")
    
    # Sanctions count
    cursor.execute("SELECT COUNT(*) as sanctions FROM sanctions_list WHERE is_pep = false OR is_pep IS NULL;")
    sanctions = cursor.fetchone()['sanctions']
    print(f"⚠️  Sanctions: {sanctions:,}")
    
    # By source
    print(f"\n📋 By Source:")
    cursor.execute("""
        SELECT list_source, COUNT(*) as count 
        FROM sanctions_list 
        GROUP BY list_source 
        ORDER BY count DESC;
    """)
    for row in cursor.fetchall():
        print(f"   {row['list_source']}: {row['count']:,}")
    
    # By entity type
    print(f"\n👥 By Entity Type:")
    cursor.execute("""
        SELECT entity_type, COUNT(*) as count 
        FROM sanctions_list 
        GROUP BY entity_type 
        ORDER BY count DESC;
    """)
    for row in cursor.fetchall():
        print(f"   {row['entity_type']}: {row['count']:,}")
    
    # Sample PEPs
    print(f"\n🌟 Sample PEPs:")
    cursor.execute("""
        SELECT entity_name, program, nationalities 
        FROM sanctions_list 
        WHERE is_pep = true 
        LIMIT 10;
    """)
    for i, row in enumerate(cursor.fetchall(), 1):
        nats = ', '.join(row['nationalities']) if row['nationalities'] else 'N/A'
        print(f"   {i}. {row['entity_name']}")
        print(f"      Program: {row['program']}")
        print(f"      Nationalities: {nats}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Statistics Complete!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
