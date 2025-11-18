const API_BASE = "/api";

export const fetchUsers = async (token) => {
  const response = await fetch(`${API_BASE}/users`, {
    headers: { "Authorization": `Bearer ${token}` }
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return await response.json();
};
