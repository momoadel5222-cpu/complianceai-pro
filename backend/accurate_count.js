import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_ANON_KEY);

(async () => {
  console.log('\n' + '='.repeat(70));
  console.log('ACCURATE DATABASE COUNT');
  console.log('='.repeat(70) + '\n');
  
  // Get total count
  const { count: totalCount } = await supabase
    .from('sanctions_list')
    .select('*', { count: 'exact', head: true });
  
  console.log(`Total Records: ${totalCount}\n`);
  
  // Count OFAC
  const { count: ofacCount } = await supabase
    .from('sanctions_list')
    .select('*', { count: 'exact', head: true })
    .eq('list_source', 'OFAC');
  
  console.log(`OFAC Records: ${ofacCount}`);
  
  // Count UN
  const { count: unCount } = await supabase
    .from('sanctions_list')
    .select('*', { count: 'exact', head: true })
    .eq('list_source', 'UN');
  
  console.log(`UN Records: ${unCount}`);
  
  console.log('\n' + '='.repeat(70) + '\n');
})();
