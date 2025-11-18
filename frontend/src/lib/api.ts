export const API_BASE_URL = 'https://complianceai-backend-7n50.onrender.com';

interface ScreenRequest {
  name: string;
}

interface AISummary {
  summary: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  key_factors: string[];
}

export interface EnhancedSearchResult {
  query: {
    name: string;
  };
  total_matches: number;
  matches: EnhancedMatch[];
  ai_analysis: string | null;
  ai_explanation?: AISummary;
  risk_level: string;
  recommended_action: string;
  screening_timestamp?: string;
}

export const screenEntity = async (name: string): Promise<EnhancedSearchResult> => {
  const response = await fetch(API_BASE_URL + '/api/screen', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: name,
      type: 'individual'
    }),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Screening failed');
  }
  return response.json();
};

export const getStats = async () => {
  const response = await fetch(API_BASE_URL + '/api/stats');
  if (!response.ok) throw new Error('Stats fetch failed');
  return response.json();
};

export const getHealth = async () => {
  const response = await fetch(API_BASE_URL + '/api/health');
  return response.json();
};