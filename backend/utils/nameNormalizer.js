// backend/utils/nameNormalizer.js

/**
 * Normalizes a name string for better matching.
 * - Converts to lowercase
 * - Removes punctuation
 * - Removes common titles and particles
 * - Removes extra whitespace
 * @param {string} name The name to normalize.
 * @returns {string} The normalized name.
 */
function normalizeName(name) {
  if (!name || typeof name !== 'string') {
    return '';
  }

  return name
    .toLowerCase()
    .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, '') // Remove punctuation
    .replace(/\b(al|bin|de|del|der|di|la|le|van|von|the|mr|mrs|ms|dr|jr|sr|iii|ii|iv)\b/g, '') // Remove common particles/titles
    .replace(/\s+/g, ' ') // Replace multiple spaces with a single space
    .trim(); // Remove leading/trailing whitespace
}

module.exports = { normalizeName };