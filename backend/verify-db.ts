import { supabase } from './src/supabase'

async function verifyDatabase() {
  console.log('🔍 Verifying database connection...')
  
  try {
    // Test screening_results table
    const { data: screening, error: screeningError } = await supabase
      .from('screening_results')
      .select('*')
      .limit(1)
    
    console.log(screeningError ? '❌ screening_results: Error' : '✅ screening_results: Working')
    if (screeningError) console.log('   Error:', screeningError.message)

    // Test sanctions_list table  
    const { data: sanctions, error: sanctionsError } = await supabase
      .from('sanctions_list')
      .select('*')
      .limit(1)
    
    console.log(sanctionsError ? '❌ sanctions_list: Error' : '✅ sanctions_list: Working')
    if (sanctionsError) console.log('   Error:', sanctionsError.message)

    if (!screeningError && !sanctionsError) {
      console.log('\n🎉 Database connection successful! Ready for integration.')
    }
    
  } catch (err) {
    console.log('❌ Connection failed:', err)
  }
}

verifyDatabase()
