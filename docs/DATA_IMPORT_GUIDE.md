# Sanctions Data Import Guide

## Overview
This guide explains how to import sanctions data from multiple sources into your Supabase database.

## Supported Data Sources

### 1. OFAC SDN List (US Treasury)
- **Format**: CSV, XML, TXT
- **URL**: https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/CONSOLIDATED.XML
- **Update Frequency**: Daily

### 2. UN Sanctions List
- **Format**: XML
- **URL**: https://scsanctions.un.org/resources/xml/en/consolidated.xml
- **Update Frequency**: Weekly

### 3. EU Sanctions List
- **Format**: XML, CSV
- **URL**: https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content
- **Update Frequency**: Daily

### 4. MLCU Egypt Terror List
- **Format**: PDF, CSV (manual conversion)
- **Source**: Egyptian Financial Supervisory Authority
- **Update Frequency**: As published

## Import Process

### Step 1: Download Source Data
```bash
# Example: Download OFAC SDN list
curl -o data/ofac_sdn.xml https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/CONSOLIDATED.XML

# Example: Download UN list
curl -o data/un_consolidated.xml https://scsanctions.un.org/resources/xml/en/consolidated.xml
```

### Step 2: Convert Data (if needed)

For PDF sources like MLCU Egypt, manually convert to CSV with columns:
- name (or الاسم in Arabic)
- type (individual/entity)
- aliases
- nationality
- date_listed

### Step 3: Run Import Script
```bash
cd scripts/data-import

# Import OFAC data
node sanctions-importer.js import-ofac ../../data/ofac_sdn.csv

# Import UN data
node sanctions-importer.js import-un ../../data/un_consolidated.xml

# Import MLCU Egypt data
node sanctions-importer.js import-mlcu ../../data/mlcu_egypt.csv
```

### Step 4: Verify Import
```bash
# Check record count in Supabase
curl -X POST https://shiny-spoon-96qrv99gxxvf74pq-3000.app.github.dev/api/test-db
```

## Data Mapping

All sources are normalized to this structure:

| Field | Type | Description |
|-------|------|-------------|
| entity_name | TEXT | Primary name |
| entity_type | TEXT | 'individual' or 'entity' |
| aliases | TEXT[] | Alternative names |
| addresses | TEXT[] | Known addresses |
| nationalities | TEXT[] | Country codes |
| date_of_birth | DATE | Birth date (individuals) |
| place_of_birth | TEXT | Birth location |
| identification_numbers | TEXT[] | Passport/ID numbers |
| list_source | TEXT | OFAC, UN, EU, MLCU |
| program | TEXT | Specific sanctions program |
| date_listed | DATE | When added to list |
| raw_data | JSONB | Original record |

## Automated Updates

Set up a cron job to update sanctions data daily:
```bash
# Add to crontab
0 2 * * * cd /path/to/scripts/data-import && ./update-all-lists.sh
```

Create `update-all-lists.sh`:
```bash
#!/bin/bash
# Download latest data
curl -o data/ofac_sdn.xml https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/CONSOLIDATED.XML

# Clear old data
node sanctions-importer.js clear

# Import fresh data
node sanctions-importer.js import-ofac data/ofac_sdn.xml

echo "Sanctions data updated: $(date)"
```

## Troubleshooting

### Issue: Encoding errors with Arabic text
**Solution**: Ensure files are UTF-8 encoded
```bash
iconv -f ISO-8859-1 -t UTF-8 input.csv > output.csv
```

### Issue: Duplicate records
**Solution**: Run deduplication query
```sql
DELETE FROM sanctions_list a USING sanctions_list b
WHERE a.id < b.id 
AND a.entity_name = b.entity_name 
AND a.list_source = b.list_source;
```

### Issue: Date format errors
**Solution**: Standardize dates to YYYY-MM-DD format before import

## Next Steps
1. Set up automated daily updates
2. Implement change tracking
3. Add email alerts for new matches
4. Create audit logs for data changes
