const sanctionsList = require('../data/sanctions.json');
const Fuse = require('fuse.js');
const { getGroqResponse } = require('./groqService');
const { normalizeName } = require('../utils/nameNormalizer');
const { logScreeningEvent } = require('./auditService');
const { isFalsePositive } = require('./falsePositiveService');

// --- PRE-PROCESS THE SANCTIONS LIST ONCE ---
// This is much more efficient. We normalize the names when the server starts.
const normalizedSanctionsList = sanctionsList.map(item => ({
  ...item,
  // Create a new field with the normalized name for searching
  normalizedName: normalizeName(item.name),
}));

// --- CONFIGURE FUSE.JS ---
const fuseOptions = {
  keys: ['normalizedName'], // Search in our new normalized field
  threshold: 0.3, // A slightly stricter threshold to reduce noise
  includeScore: true,
  findAllMatches: false, // We only care about the best matches
};

// Initialize Fuse with the pre-processed list
const fuse = new Fuse(normalizedSanctionsList, fuseOptions);

// --- THE MAIN SCREENING FUNCTION ---
async function screenName(inputName, userId = 'anonymous', ipAddress = '0.0.0.0') {
  // 1. Check against the false positive list first
  if (await isFalsePositive(inputName)) {
    const result = { matches: [], analysis: `Input name "${inputName}" is on the false positive list.` };
    // Log the event for auditing
    await logScreeningEvent(inputName, userId, ipAddress, result);
    return result;
  }

  // 2. Normalize the input name for searching
  const normalizedInputName = normalizeName(inputName);

  // 3. Perform a single search to get the top candidates
  const searchResults = fuse.search(normalizedInputName, { limit: 10 });

  let result;
  if (searchResults.length === 0 || searchResults[0].score > 0.3) {
    // No good matches found via fuzzy search
    result = { matches: [], analysis: "No potential matches found via fuzzy search." };
  } else {
    // A potential match was found, use AI for final verification
    const bestCandidate = searchResults[0]; // The result with the lowest score
    
    const prompt = `
      You are a compliance expert. Compare the following two names.
      Your job is to determine if they refer to the same individual.
      Respond with a JSON object containing two keys: "decision" and "reason".
      The "decision" key must have the value "MATCH" or "NO MATCH".
      The "reason" key should be a very brief explanation.

      Input Name: "${inputName}"
      Sanctioned Name: "${bestCandidate.item.name}"

      JSON Response:
    `;

    try {
      const analysis = await getGroqResponse(prompt);
      let aiDecision;
      try {
        // Groq might add ```json ... ``` wrappers, so we need to be robust
        const jsonMatch = analysis.match(/\{.*\}/s);
        if (jsonMatch) {
          aiDecision = JSON.parse(jsonMatch[0]);
        } else {
          throw new Error("No JSON object found in response.");
        }
      } catch (parseError) {
        console.error("Failed to parse Groq JSON response:", analysis);
        result = { matches: [], analysis: "AI response was malformed. Could not determine match." };
      }
      
      // If parsing was successful, determine the final result based on AI decision
      if (aiDecision && aiDecision.decision === 'MATCH') {
        result = {
          matches: [{
            sanctionedName: bestCandidate.item.name,
            score: bestCandidate.score,
            reason: aiDecision.reason,
          }],
          analysis: `AI confirmed a match. Reason: ${aiDecision.reason}`
        };
      } else {
        result = {
          matches: [],
          analysis: `AI reviewed the best candidate ("${bestCandidate.item.name}") and determined it was not a match. Reason: ${aiDecision.reason}`
        };
      }
    } catch (error) {
      console.error("Error during Groq API call:", error);
      result = { matches: [], analysis: "An error occurred while contacting the AI service." };
    }
  }

  // 4. Log the final event for auditing, regardless of the outcome
  await logScreeningEvent(inputName, userId, ipAddress, result);

  return result;
}

module.exports = { screenName };