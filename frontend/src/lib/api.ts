export const API_BASE_URL = 'https://complianceai-backend-7n50.onrender.com';

interface ScreenRequest {
  name: string;
  type?: string;
  country?: string;
  date_of_birth?: string;
}

interface AISummary {
  summary: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  key_factors: string[];
}

export interface EnhancedMatch {
  entity_name: string;
  entity_type: string;
  list_source: string;
  program: string;
  nationalities: string[];
  date_of_birth: string;
  match_score: number;
  aliases?: string[];
  akas?: string[];
  positions?: string[];
  countries?: string[];
  dates?: string[];
  details?: Record<string, any>;
}

export interface EnhancedSearchResult {
  query: {
    name: string;
    country: string;
    date_of_birth: string;
  };
  total_matches: number;
  matches: EnhancedMatch[];
  ai_analysis: string | null;
  ai_explanation?: AISummary;
  risk_level: string;
  recommended_action: string;
  entity_name?: string;
  screening_timestamp?: string;
}

export const screenEntity = async (entityName: string, type: string, data: ScreenRequest): Promise<EnhancedSearchResult> => {
  const url = API_BASE_URL + '/api/screen';
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: data.name,
      type: 'individual'  // This is crucial - must match backend expectations
    }),
  });
  if (!response.ok) throw new Error('Screening failed');
  return response.json();
};

export const getStats = async () => {
  const url = API_BASE_URL + '/api/stats';
  const response = await fetch(url);
  if (!response.ok) throw new Error('Stats fetch failed');
  return response.json();
};

export const getHealth = async () => {
  const url = API_BASE_URL + '/api/health';
  const response = await fetch(url);
  return response.json();
};
