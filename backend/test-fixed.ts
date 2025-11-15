import { supabase } from './src/supabase'
async function testConnection() {
  try {
    console.log('Testing Supabase connection...')
    
    const { data, error } = await supabase
      .from('screening_results')
      .select('*')
      .limit(1)
    
    if (error) {
      console.log('❌ Error:', error.message)
    } else {
      console.log('✅ Supabase connection successful!')
      console.log('Sample data:', data)
    }
  } catch (err) {
    console.log('❌ Connection failed:', err)
  }
}
testConnection()
