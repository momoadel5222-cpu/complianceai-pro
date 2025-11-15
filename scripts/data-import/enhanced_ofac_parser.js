import { createClient } from '@supabase/supabase-js';
import fs from 'fs';
import dotenv from 'dotenv';

dotenv.config({ path: '../../backend/.env' });

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
);

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

function parseNameParts(fullName) {
  if (!fullName) return { first: null, middle: null, last: null };
  const parts = fullName.split(',').map(p => p.trim());
  if (parts.length === 2) {
    const lastName = parts[0];
    const firstMiddle = parts[1].split(/\s+/);
    const firstName = firstMiddle[0];
    const middleName = firstMiddle.slice(1).join(' ') || null;
    return { first: firstName, middle: middleName, last: lastName };
  }
  return { first: null, middle: null, last: null };
}

function extractDateOfBirth(remarks) {
  if (!remarks) return null;
  const monthMap = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
  };
  const dobPattern = /DOB\s+(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})/i;
  const match = remarks.match(dobPattern);
  if (match) {
    const day = match[1].padStart(2, '0');
    const month = monthMap[match[2].toLowerCase()];
    const year = match[3];
    return `${year}-${month}-${day}`;
  }
  return null;
}

function extractPlaceOfBirth(remarks) {
  if (!remarks) return null;
  const pobPattern = /POB\s+([^;]+)/i;
  const match = remarks.match(pobPattern);
  return match ? match[1].trim() : null;
}

function extractGender(remarks) {
  if (!remarks) return 'Unknown';
  const remarksLower = remarks.toLowerCase();
  if (remarksLower.includes('gender male')) return 'Male';
  if (remarksLower.includes('gender female')) return 'Female';
  return 'Unknown';
}

async function enhanceData() {
  console.log('Starting enhanced data parsing...');
  const sdnData = fs.readFileSync('../../data/sdn.csv', 'utf-8').split('\n').filter(l => l.trim());
  const altData = fs.readFileSync('../../data/alt.csv', 'utf-8').split('\n').filter(l => l.trim());
  const addData = fs.readFileSync('../../data/add.csv', 'utf-8').split('\n').filter(l => l.trim());
  
  const aliases = {};
  altData.forEach(line => {
    const parts = parseCSVLine(line);
    if (parts[0] && parts[3]) {
      if (!aliases[parts[0]]) aliases[parts[0]] = [];
      aliases[parts[0]].push(parts[3]);
    }
  });
  
  const addresses = {};
  addData.forEach(line => {
    const parts = parseCSVLine(line);
    if (parts[0] && parts[4]) {
      if (!addresses[parts[0]]) addresses[parts[0]] = [];
      addresses[parts[0]].push(parts[4]);
    }
  });
  
  console.log('Loaded', Object.keys(aliases).length, 'entities with aliases');
  console.log('Loaded', Object.keys(addresses).length, 'entities with addresses');
  
  const entities = [];
  let enhanced = 0;
  
  sdnData.forEach((line, index) => {
    const parts = parseCSVLine(line);
    const entNum = parts[0];
    const name = parts[1];
    const sdnType = parts[2];
    const program = parts[3];
    const remarks = parts[11];
    if (!name) return;
    const nameParts = parseNameParts(name);
    const dateOfBirth = extractDateOfBirth(remarks);
    const placeOfBirth = extractPlaceOfBirth(remarks);
    const gender = extractGender(remarks);
    if (dateOfBirth || placeOfBirth || gender !== 'Unknown') enhanced++;
    entities.push({
      entity_name: name,
      first_name: nameParts.first,
      middle_name: nameParts.middle,
      last_name: nameParts.last,
      entity_type: sdnType?.toLowerCase() === 'individual' ? 'individual' : 'entity',
      aliases: aliases[entNum] || [],
      nationalities: addresses[entNum] ? [...new Set(addresses[entNum])] : [],
      date_of_birth: dateOfBirth,
      place_of_birth: placeOfBirth,
      gender: gender,
      id_numbers: [],
      list_source: 'OFAC',
      program: program || 'SDN',
      date_listed: null,
      remarks: remarks
    });
    if ((index + 1) % 1000 === 0) {
      console.log('Parsed', index + 1, '/', sdnData.length, 'entities...');
    }
  });
  
  console.log('Parsed', entities.length, 'entities');
  console.log('Enhanced', enhanced, 'entities');
  console.log('Clearing old data...');
  await supabase.from('sanctions_list').delete().neq('id', '00000000-0000-0000-0000-000000000000');
  console.log('Importing enhanced data...');
  const batchSize = 100;
  for (let i = 0; i < entities.length; i += batchSize) {
    const batch = entities.slice(i, i + batchSize);
    const { error } = await supabase.from('sanctions_list').insert(batch);
    if (error) {
      console.error('Error:', error);
      throw error;
    }
    console.log('Batch', Math.floor(i / batchSize) + 1, '/', Math.ceil(entities.length / batchSize));
  }
  console.log('Successfully imported', entities.length, 'enhanced entities');
  console.log('With DOB:', entities.filter(e => e.date_of_birth).length);
  console.log('With POB:', entities.filter(e => e.place_of_birth).length);
  console.log('With Gender:', entities.filter(e => e.gender !== 'Unknown').length);
  console.log('Parsed names:', entities.filter(e => e.first_name && e.last_name).length);
}

enhanceData().catch(console.error);
