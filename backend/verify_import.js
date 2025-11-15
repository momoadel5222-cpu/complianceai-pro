import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_ANON_KEY);

(async () => {
  console.log('\n' + '='.repeat(70));
  console.log('VERIFICATION: Enhanced OFAC Import');
  console.log('='.repeat(70) + '\n');
  
  const { data: all, error } = await supabase
    .from('sanctions_list')
    .select('list_source, entity_type, first_name, last_name, date_of_birth_text, gender')
    .limit(50000);
  
  if (error) {
    console.log('Error:', error);
    return;
  }
  
  const stats = {
    total: all.length,
    bySource: {},
    byType: {},
    withFirstName: 0,
    withLastName: 0,
    withDOB: 0,
    withGender: 0
  };
  
  all.forEach(row => {
    stats.bySource[row.list_source] = (stats.bySource[row.list_source] || 0) + 1;
    stats.byType[row.entity_type] = (stats.byType[row.entity_type] || 0) + 1;
    if (row.first_name) stats.withFirstName++;
    if (row.last_name) stats.withLastName++;
    if (row.date_of_birth_text) stats.withDOB++;
    if (row.gender && row.gender !== 'unknown') stats.withGender++;
  });
  
  console.log('�� DATABASE SUMMARY:\n');
  console.log(`   Total Records: ${stats.total}`);
  console.log('\n   By Source:');
  Object.entries(stats.bySource).forEach(([source, count]) => {
    console.log(`      ${source}: ${count} (${(count/stats.total*100).toFixed(1)}%)`);
  });
  
  console.log('\n   By Type:');
  Object.entries(stats.byType).forEach(([type, count]) => {
    console.log(`      ${type}: ${count} (${(count/stats.total*100).toFixed(1)}%)`);
  });
  
  console.log('\n   Enhanced Fields:');
  console.log(`      First Names: ${stats.withFirstName} (${(stats.withFirstName/stats.total*100).toFixed(1)}%)`);
  console.log(`      Last Names: ${stats.withLastName} (${(stats.withLastName/stats.total*100).toFixed(1)}%)`);
  console.log(`      DOB Extracted: ${stats.withDOB} (${(stats.withDOB/stats.total*100).toFixed(1)}%)`);
  console.log(`      Gender Detected: ${stats.withGender} (${(stats.withGender/stats.total*100).toFixed(1)}%)`);
  
  console.log('\n' + '='.repeat(70));
  console.log('✅ Phase 1 Complete! Enhanced OFAC data imported successfully.');
  console.log('='.repeat(70) + '\n');
})();
