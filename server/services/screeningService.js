export const J1 = async (entityName, userEmail) => {
  try {
    const response = await fetch(`${process.env.SCREENING_API_URL}/api/screen`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${process.env.SCREENING_API_KEY}`,
        "X-User-Email": userEmail
      },
      body: JSON.stringify({ entity_name: entityName, user_email: userEmail })
    });

    if (!response.ok) throw new Error(`Screening failed: ${response.status}`);
    
    const data = await response.json();
    return { isAllowed: !!data.isAllowed, rlsFilter: data.rlsFilter || null };
  } catch (error) {
    console.error("Screening error:", error);
    return { isAllowed: false, rlsFilter: null };
  }
};
