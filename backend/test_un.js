import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_ANON_KEY);

(async () => {
  console.log('\n🔍 Testing UN Records:\n');
  
  // Get sample UN entities
  const { data: unEntities } = await supabase
    .from('sanctions_list')
    .select('entity_name, entity_type, list_source')
    .eq('list_source', 'UN')
    .limit(10);
  
  console.log('Sample UN Records:');
  unEntities.forEach((e, i) => {
    console.log(`  ${i+1}. ${e.entity_name} (${e.entity_type})`);
  });
  
  console.log('\n');
})();
