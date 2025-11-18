// Use .env.local for API URL, fallback to production backend
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://complianceai-backend-7n50.onrender.com';

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

export const screenEntity = async (data: ScreenRequest): Promise<EnhancedSearchResult> => {
  const response = await fetch(`${API_BASE_URL}/api/screen`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: data.name,
      type: 'individual'
    }),
  });
  
  if (!response.ok) throw new Error('Screening failed');
  return response.json();
};

export const getStats = async () => {
  const response = await fetch(`${API_BASE_URL}/api/stats`);
  if (!response.ok) throw new Error('Stats fetch failed');
  return response.json();
};

export const getHealth = async () => {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  return response.json();
};
