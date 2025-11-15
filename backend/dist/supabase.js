import { createClient } from '@supabase/supabase-js';
const supabaseUrl = process.env.SUPABASE_URL || 'your_supabase_url';
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || 'your_service_role_key';
export const supabase = createClient(supabaseUrl, supabaseServiceKey);
