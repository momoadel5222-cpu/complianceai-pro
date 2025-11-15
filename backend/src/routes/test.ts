import express, { Request, Response } from 'express';
import { supabase } from '../db.js';

const router = express.Router();

router.get('/test-db', async (req: Request, res: Response) => {
  try {
    // Get total count
    const { count: totalCount, error: countError } = await supabase
      .from('sanctions_list')
      .select('*', { count: 'exact', head: true });
    
    if (countError) throw countError;
    
    // Get count by source using aggregation
    const { count: ofacCount } = await supabase
      .from('sanctions_list')
      .select('*', { count: 'exact', head: true })
      .eq('list_source', 'OFAC');
    
    const { count: unCount } = await supabase
      .from('sanctions_list')
      .select('*', { count: 'exact', head: true })
      .eq('list_source', 'UN');
    
    res.json({
      status: 'Database connected',
      total_records: totalCount,
      by_source: {
        OFAC: ofacCount || 0,
        UN: unCount || 0
      }
    });
  } catch (error: any) {
    console.error('Database test error:', error);
    res.status(500).json({ 
      status: 'Error', 
      error: error.message 
    });
  }
});

export default router;
