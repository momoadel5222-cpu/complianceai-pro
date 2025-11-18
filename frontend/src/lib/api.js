const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:10000';

export const screenEntity = async (name) => {
  const response = await fetch(`${API_BASE_URL}/api/screen`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ entity_name: name })
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
