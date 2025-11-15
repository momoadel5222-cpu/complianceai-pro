import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_ANON_KEY);

(async () => {
  console.log('\n🔍 DIAGNOSIS:\n');
  
  // Check total count without limit
  const { count, error } = await supabase
    .from('sanctions_list')
    .select('*', { count: 'exact', head: true });
  
  if (error) {
    console.log('Error:', error);
    return;
  }
  
  console.log(`Total records in database: ${count}\n`);
  
  // Check by source
  const { data: sources } = await supabase
    .from('sanctions_list')
    .select('list_source')
    .limit(50000);
  
  const sourceCounts = {};
  sources.forEach(row => {
    sourceCounts[row.list_source] = (sourceCounts[row.list_source] || 0) + 1;
  });
  
  console.log('Records by source:');
  Object.entries(sourceCounts).forEach(([source, count]) => {
    console.log(`   ${source}: ${count}`);
  });
  
  console.log('\n');
})();
