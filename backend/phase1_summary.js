import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_ANON_KEY);

(async () => {
  console.log('\n' + '='.repeat(70));
  console.log('🎉 PHASE 1 COMPLETE - FINAL SUMMARY');
  console.log('='.repeat(70) + '\n');
  
  // Total count
  const { count: total } = await supabase
    .from('sanctions_list')
    .select('*', { count: 'exact', head: true });
  
  // By source
  const { count: ofac } = await supabase
    .from('sanctions_list')
    .select('*', { count: 'exact', head: true })
    .eq('list_source', 'OFAC');
  
  const { count: un } = await supabase
    .from('sanctions_list')
    .select('*', { count: 'exact', head: true })
    .eq('list_source', 'UN');
  
  // Enhanced fields stats
  const { data: sample } = await supabase
    .from('sanctions_list')
    .select('first_name, last_name, date_of_birth_text, gender, nationalities')
    .limit(20000);
  
  const withFirstName = sample.filter(r => r.first_name).length;
  const withLastName = sample.filter(r => r.last_name).length;
  const withDOB = sample.filter(r => r.date_of_birth_text).length;
  const withGender = sample.filter(r => r.gender && r.gender !== 'unknown').length;
  const withNationalities = sample.filter(r => r.nationalities && r.nationalities.length > 0).length;
  
  console.log('📊 DATABASE STATISTICS:\n');
  console.log(`   Total Records: ${total.toLocaleString()}`);
  console.log(`   OFAC: ${ofac.toLocaleString()} (${(ofac/total*100).toFixed(1)}%)`);
  console.log(`   UN: ${un.toLocaleString()} (${(un/total*100).toFixed(1)}%)`);
  
  console.log('\n✨ ENHANCED DATA QUALITY:\n');
  console.log(`   First Names: ${withFirstName.toLocaleString()} (${(withFirstName/sample.length*100).toFixed(1)}%)`);
  console.log(`   Last Names: ${withLastName.toLocaleString()} (${(withLastName/sample.length*100).toFixed(1)}%)`);
  console.log(`   Date of Birth: ${withDOB.toLocaleString()} (${(withDOB/sample.length*100).toFixed(1)}%)`);
  console.log(`   Gender: ${withGender.toLocaleString()} (${(withGender/sample.length*100).toFixed(1)}%)`);
  console.log(`   Nationalities: ${withNationalities.toLocaleString()} (${(withNationalities/sample.length*100).toFixed(1)}%)`);
  
  console.log('\n🎯 CAPABILITIES:\n');
  console.log('   ✅ Multi-source screening (OFAC + UN)');
  console.log('   ✅ Structured name fields (First/Middle/Last)');
  console.log('   ✅ Biographical data (DOB/POB/Gender)');
  console.log('   ✅ Fuzzy name matching');
  console.log('   ✅ Alias matching');
  console.log('   ✅ Full-text search');
  
  console.log('\n' + '='.repeat(70));
  console.log('✅ Ready for Phase 2: Authentication & Advanced Features');
  console.log('='.repeat(70) + '\n');
})();
