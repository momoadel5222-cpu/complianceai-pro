import { createClient } from '@supabase/supabase-js';
import fs from 'fs';
import dotenv from 'dotenv';

dotenv.config({ path: '../backend/.env' });

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
);

// Parse OFAC files - they use -0- as null indicator
function parseCSVLine(line) {
  const parts = [];
  let current = '';
  let inQuotes = false;
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      parts.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  parts.push(current.trim());
  return parts.map(p => p === '-0-' ? null : p);
}

async function importOFACData() {
  console.log('📂 Reading OFAC files...');
  
  // Read SDN file
  const sdnData = fs.readFileSync('../data/sdn.csv', 'utf-8').split('\n').filter(l => l.trim());
  
  // Read aliases
  const altData = fs.readFileSync('../data/alt.csv', 'utf-8').split('\n').filter(l => l.trim());
  const aliases = {};
  altData.forEach(line => {
    const parts = parseCSVLine(line);
    const entNum = parts[0];
    const altName = parts[3];
    if (entNum && altName) {
      if (!aliases[entNum]) aliases[entNum] = [];
      aliases[entNum].push(altName);
    }
  });
  
  // Read addresses
  const addData = fs.readFileSync('../data/add.csv', 'utf-8').split('\n').filter(l => l.trim());
  const addresses = {};
  addData.forEach(line => {
    const parts = parseCSVLine(line);
    const entNum = parts[0];
    const country = parts[4];
    if (entNum && country) {
      if (!addresses[entNum]) addresses[entNum] = [];
      addresses[entNum].push(country);
    }
  });
  
  console.log(`✓ Loaded ${Object.keys(aliases).length} entities with aliases`);
  console.log(`✓ Loaded ${Object.keys(addresses).length} entities with addresses`);
  
  // Parse SDN entries
  const entities = [];
  sdnData.forEach(line => {
    const parts = parseCSVLine(line);
    const entNum = parts[0];
    const name = parts[1];
    const sdnType = parts[2];
    const program = parts[3];
    
    if (!name) return;
    
    const entity = {
      entity_name: name,
      entity_type: sdnType?.toLowerCase() === 'individual' ? 'individual' : 'entity',
      aliases: aliases[entNum] || [],
      nationalities: addresses[entNum] ? [...new Set(addresses[entNum])] : [],
      list_source: 'OFAC',
      program: program || 'SDN',
      date_listed: null
    };
    
    entities.push(entity);
  });
  
  console.log(`✓ Parsed ${entities.length} entities from SDN list`);
  
  // Clear existing data
  console.log('🗑️  Clearing old data...');
  await supabase.from('sanctions_list').delete().neq('id', '00000000-0000-0000-0000-000000000000');
  
  // Insert in batches
  const batchSize = 100;
  for (let i = 0; i < entities.length; i += batchSize) {
    const batch = entities.slice(i, i + batchSize);
    const { error } = await supabase.from('sanctions_list').insert(batch);
    
    if (error) {
      console.error('Error inserting batch:', error);
      throw error;
    }
    
    console.log(`Inserted batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(entities.length / batchSize)}`);
  }
  
  console.log(`✅ Successfully imported ${entities.length} OFAC entities!`);
}

importOFACData().catch(console.error);
