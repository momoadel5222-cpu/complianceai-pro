import { createClient } from '@supabase/supabase-js';
import fs from 'fs';
import csv from 'csv-parser';
import * as XLSX from 'xlsx';
import dotenv from 'dotenv';

dotenv.config({ path: '../../backend/.env' });

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
);

// Unified data structure
class SanctionEntity {
  constructor(data) {
    this.entity_name = data.entity_name || '';
    this.entity_type = data.entity_type || 'individual';
    this.aliases = data.aliases || [];
    this.addresses = data.addresses || [];
    this.nationalities = data.nationalities || [];
    this.date_of_birth = data.date_of_birth || null;
    this.place_of_birth = data.place_of_birth || null;
    this.identification_numbers = data.identification_numbers || [];
    this.list_source = data.list_source || '';
    this.program = data.program || '';
    this.date_listed = data.date_listed || null;
    this.raw_data = data.raw_data || {};
  }
}

// Parser for OFAC SDN List
class OFACParser {
  static parse(csvData) {
    const entities = [];
    
    csvData.forEach(row => {
      const entity = new SanctionEntity({
        entity_name: row.name || row.NAME || row['SDN Name'],
        entity_type: (row.type || row.TYPE)?.toLowerCase() === 'entity' ? 'entity' : 'individual',
        aliases: this.parseAliases(row.aliases || row.ALIASES || row['Alt Names']),
        addresses: this.parseAddresses(row.address || row.ADDRESS),
        nationalities: this.parseNationalities(row.nationality || row.NATIONALITY || row.citizenship),
        date_of_birth: this.parseDate(row.dob || row['Date of Birth']),
        identification_numbers: this.parseIDs(row.id_number || row['ID Number']),
        list_source: 'OFAC',
        program: row.program || row.PROGRAM || 'SDN',
        date_listed: this.parseDate(row.date_listed || row['Date Listed']),
        raw_data: row
      });
      
      entities.push(entity);
    });
    
    return entities;
  }
  
  static parseAliases(aliasStr) {
    if (!aliasStr) return [];
    return aliasStr.split(/[;,]/).map(a => a.trim()).filter(Boolean);
  }
  
  static parseAddresses(addressStr) {
    if (!addressStr) return [];
    return [addressStr.trim()];
  }
  
  static parseNationalities(natStr) {
    if (!natStr) return [];
    return natStr.split(/[;,]/).map(n => n.trim()).filter(Boolean);
  }
  
  static parseIDs(idStr) {
    if (!idStr) return [];
    return [idStr.trim()];
  }
  
  static parseDate(dateStr) {
    if (!dateStr) return null;
    try {
      const date = new Date(dateStr);
      return date.toISOString().split('T')[0];
    } catch {
      return null;
    }
  }
}

// Parser for UN Sanctions List
class UNParser {
  static parse(xmlData) {
    // UN uses XML format - simplified parser
    const entities = [];
    
    // Parse XML (you'll need a proper XML parser like xml2js)
    // This is a placeholder structure
    xmlData.forEach(individual => {
      const entity = new SanctionEntity({
        entity_name: individual.FIRST_NAME + ' ' + individual.SECOND_NAME,
        entity_type: 'individual',
        aliases: individual.INDIVIDUAL_ALIAS || [],
        nationalities: individual.NATIONALITY || [],
        date_of_birth: individual.DATE_OF_BIRTH,
        list_source: 'UN',
        program: 'UN Sanctions',
        raw_data: individual
      });
      
      entities.push(entity);
    });
    
    return entities;
  }
}

// Parser for Egypt MLCU List
class MLCUParser {
  static parse(csvData) {
    const entities = [];
    
    csvData.forEach(row => {
      const entity = new SanctionEntity({
        entity_name: row['الاسم'] || row['Name'] || row.name,
        entity_type: this.determineType(row),
        aliases: this.parseArabicAliases(row['أسماء أخرى'] || row.aliases),
        nationalities: ['EG'], // Egypt
        list_source: 'MLCU',
        program: 'Egypt Terror List',
        date_listed: this.parseDate(row['تاريخ الإدراج'] || row.date),
        raw_data: row
      });
      
      entities.push(entity);
    });
    
    return entities;
  }
  
  static determineType(row) {
    const typeField = row['النوع'] || row.type || '';
    if (typeField.includes('كيان') || typeField.toLowerCase().includes('entity')) {
      return 'entity';
    }
    return 'individual';
  }
  
  static parseArabicAliases(aliasStr) {
    if (!aliasStr) return [];
    return aliasStr.split(/[،,;]/).map(a => a.trim()).filter(Boolean);
  }
  
  static parseDate(dateStr) {
    if (!dateStr) return null;
    try {
      const date = new Date(dateStr);
      return date.toISOString().split('T')[0];
    } catch {
      return null;
    }
  }
}

// Main Importer
class SanctionsImporter {
  static async importFromCSV(filePath, parserClass) {
    const results = [];
    
    return new Promise((resolve, reject) => {
      fs.createReadStream(filePath)
        .pipe(csv())
        .on('data', (data) => results.push(data))
        .on('end', async () => {
          try {
            const entities = parserClass.parse(results);
            await this.bulkInsert(entities);
            resolve(entities.length);
          } catch (error) {
            reject(error);
          }
        })
        .on('error', reject);
    });
  }
  
  static async importFromExcel(filePath, parserClass) {
    const workbook = XLSX.readFile(filePath);
    const sheetName = workbook.SheetNames[0];
    const data = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName]);
    
    const entities = parserClass.parse(data);
    await this.bulkInsert(entities);
    return entities.length;
  }
  
  static async bulkInsert(entities) {
    const batchSize = 100;
    
    for (let i = 0; i < entities.length; i += batchSize) {
      const batch = entities.slice(i, i + batchSize);
      
      const { error } = await supabase
        .from('sanctions_list')
        .insert(batch);
      
      if (error) {
        console.error('Batch insert error:', error);
        throw error;
      }
      
      console.log(`Inserted batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(entities.length / batchSize)}`);
    }
  }
  
  static async clearDatabase() {
    const { error } = await supabase
      .from('sanctions_list')
      .delete()
      .neq('id', '00000000-0000-0000-0000-000000000000');
    
    if (error) throw error;
    console.log('Database cleared');
  }
}

// CLI Interface
const args = process.argv.slice(2);
const command = args[0];
const filePath = args[1];
const source = args[2];

async function main() {
  switch (command) {
    case 'import-ofac':
      console.log('Importing OFAC data...');
      const ofacCount = await SanctionsImporter.importFromCSV(filePath, OFACParser);
      console.log(`✅ Imported ${ofacCount} OFAC entities`);
      break;
      
    case 'import-un':
      console.log('Importing UN data...');
      // You'll need to implement XML parsing
      console.log('⚠️  UN parser needs XML implementation');
      break;
      
    case 'import-mlcu':
      console.log('Importing MLCU data...');
      const mlcuCount = await SanctionsImporter.importFromCSV(filePath, MLCUParser);
      console.log(`✅ Imported ${mlcuCount} MLCU entities`);
      break;
      
    case 'clear':
      await SanctionsImporter.clearDatabase();
      break;
      
    default:
      console.log(`
Usage:
  node sanctions-importer.js import-ofac <file.csv>
  node sanctions-importer.js import-un <file.xml>
  node sanctions-importer.js import-mlcu <file.csv>
  node sanctions-importer.js clear
      `);
  }
}

main().catch(console.error);
