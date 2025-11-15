import express, { Request, Response } from 'express';
import { supabase } from '../db.js';
import { advancedNameMatch } from '../utils/fuzzyMatching.js';

const router = express.Router();

router.post('/screen', async (req: Request, res: Response) => {
  try {
    const { name, type = 'individual', dateOfBirth = null } = req.body;
    
    if (!name) {
      return res.status(400).json({ 
        success: false, 
        error: 'Name is required' 
      });
    }
    
    console.log(`Screening: ${name} (${type})${dateOfBirth ? ` DOB: ${dateOfBirth}` : ''}`);
    
    // Parse search name
    const nameParts = name.trim().split(/\s+/);
    const firstName = nameParts[0];
    const lastName = nameParts[nameParts.length - 1];
    
    // Query WITHOUT LIMIT - fetch all potential matches
    let query = supabase
      .from('sanctions_list')
      .select('*')
      .eq('entity_type', type);
    
    // Search using structured name fields
    if (nameParts.length === 1) {
      query = query.or(`first_name.ilike.%${name}%,last_name.ilike.%${name}%,entity_name.ilike.%${name}%`);
    } else {
      query = query.or(`first_name.ilike.%${firstName}%,last_name.ilike.%${lastName}%,entity_name.ilike.%${name}%`);
    }
    
    const { data: potentialMatches, error } = await query;
    
    if (error) {
      console.error('Database error:', error);
      throw error;
    }
    
    console.log(`Found ${potentialMatches?.length || 0} potential matches from all sources`);
    
    // Fuzzy matching with enhanced scoring
    const matches = (potentialMatches || [])
      .map(entity => {
        const nameScore = advancedNameMatch(name, entity.entity_name);
        const aliasScores = (entity.aliases || []).map((alias: string) => 
          advancedNameMatch(name, alias)
        );
        
        // Check structured name match
        let firstLastScore = 0;
        if (entity.first_name && entity.last_name) {
          const fullName = `${entity.first_name} ${entity.last_name}`;
          firstLastScore = advancedNameMatch(name, fullName);
        }
        
        let bestScore = Math.max(nameScore, firstLastScore, ...aliasScores);
        
        // DOB bonus: +10% if DOB matches
        if (dateOfBirth && entity.date_of_birth_text) {
          if (entity.date_of_birth_text.includes(dateOfBirth)) {
            bestScore = Math.min(bestScore + 0.10, 1.0);
          }
        }
        
        return {
          ...entity,
          match_score: nameScore,
          alias_scores: aliasScores,
          best_score: bestScore
        };
      })
      .filter(entity => entity.best_score > 0.60)
      .sort((a, b) => b.best_score - a.best_score)
      .slice(0, 20); // Limit to top 20 AFTER scoring
    
    let status = 'no_match';
    if (matches.length > 0) {
      status = matches[0].best_score > 0.85 ? 'match' : 'potential_match';
    }
    
    console.log(`Final: ${matches.length} matches, Status: ${status}`);
    if (matches.length > 0) {
      console.log(`Top match: ${matches[0].entity_name} (${matches[0].list_source}) - Score: ${matches[0].best_score.toFixed(2)}`);
    }
    
    // Save results
    const { data: screeningResult, error: saveError } = await supabase
      .from('screening_results')
      .insert({
        search_term: name,
        search_type: type,
        match_count: matches.length,
        highest_match_score: matches.length > 0 ? matches[0].best_score : 0,
        status,
        matches,
        user_id: null
      })
      .select()
      .single();
    
    if (saveError) {
      console.error('Save error:', saveError);
      throw saveError;
    }
    
    res.json({
      success: true,
      data: {
        screening_id: screeningResult.id,
        status,
        matches
      }
    });
  } catch (error: any) {
    console.error('Screening error:', error);
    res.status(500).json({ 
      success: false, 
      error: error.message || 'Screening failed' 
    });
  }
});

export default router;
