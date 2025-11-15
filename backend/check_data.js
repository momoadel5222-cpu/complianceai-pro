import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_ANON_KEY);

(async () => {
  const { data, error } = await supabase
    .from('sanctions_list')
    .select('list_source, entity_type')
    .limit(50000);
  
  if (error) {
    console.log('Error:', error);
    return;
  }
  
  const summary = {};
  data.forEach(row => {
    const key = `${row.list_source} - ${row.entity_type}`;
    summary[key] = (summary[key] || 0) + 1;
  });
  
  console.log('\n📊 DATABASE CONTENTS:\n');
  Object.entries(summary)
    .sort((a, b) => b[1] - a[1])
    .forEach(([key, count]) => {
      console.log(`   ${key}: ${count} records`);
    });
  console.log(`\n   Total: ${data.length} records\n`);
})();
