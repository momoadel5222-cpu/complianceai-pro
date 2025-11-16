from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
import os
import logging
from datetime import datetime
from typing import List, Dict, Any
from fuzzywuzzy import fuzz
from groq import Groq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "https://complianceai-pro.vercel.app", "https://shiny-spoon-96qrv99gxxvf74pq-5173.app.github.dev"]}})

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://qwacsyreyuhhlvzcwhnw.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7es')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Groq AI
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        logger.info("✅ Groq AI initialized")
    except Exception as e:
        logger.warning(f"⚠️ Groq AI not available: {e}")
else:
    logger.warning("⚠️ GROQ_API_KEY not set - AI features disabled")

def calculate_fuzzy_score(str1, str2):
    if not str1 or not str2: return 0.0
    str1, str2 = str1.lower().strip(), str2.lower().strip()
    if str1 == str2: return 1.0
    if str1 in str2 or str2 in str1: return 0.9
    ratio = fuzz.ratio(str1, str2) / 100.0
    partial = fuzz.partial_ratio(str1, str2) / 100.0
    token_sort = fuzz.token_sort_ratio(str1, str2) / 100.0
    token_set = fuzz.token_set_ratio(str1, str2) / 100.0
    return round((ratio * 0.2 + partial * 0.2 + token_sort * 0.3 + token_set * 0.3), 3)

def explain_match_with_ai(query_name: str, matched_entity: Dict[str, Any]) -> str:
    """Generate AI explanation using Groq"""
    if not groq_client:
        return "AI explanations unavailable"
    
    try:
        prompt = f"""As a sanctions compliance expert, explain why "{query_name}" matched "{matched_entity.get('entity_name')}" from {matched_entity.get('list_source')}.

Details:
- Type: {matched_entity.get('entity_type')}
- Program: {matched_entity.get('program', 'N/A')}
- Nationalities: {', '.join(matched_entity.get('nationalities', []) or ['N/A'])}

Provide: 1) Match reasoning, 2) Risk level (CRITICAL/HIGH/MEDIUM/LOW), 3) Recommendation. Max 4 sentences."""

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a sanctions compliance expert. Be concise and actionable."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq AI error: {e}")
        return f"AI explanation unavailable: {str(e)}"

def calculate_risk_score(entity: Dict[str, Any], match_score: float) -> Dict[str, Any]:
    """Calculate comprehensive risk score"""
    base_score = match_score * 50
    
    program = (entity.get('program') or '').lower()
    if any(k in program for k in ['terrorism', 'proliferation', 'narcotics', 'taliban', 'isis']):
        base_score += 35
        severity = "CRITICAL"
    elif any(k in program for k in ['weapons', 'wmd', 'military']):
        base_score += 25
        severity = "HIGH"
    else:
        base_score += 10
        severity = "MEDIUM"
    
    source = entity.get('list_source', '').upper()
    if source in ['OFAC', 'UN']:
        base_score += 15
    elif source in ['EU', 'UK']:
        base_score += 10
    
    final_score = min(100, base_score)
    
    if final_score >= 80:
        level = "CRITICAL"
    elif final_score >= 60:
        level = "HIGH"
    elif final_score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"
    
    return {
        'score': round(final_score, 1),
        'level': level,
        'program_severity': severity,
        'source': source
    }

def search_database_flexible(name: str, entity_type: str) -> List[Dict]:
    """Search database with multiple strategies for better recall"""
    all_results = []
    search_terms = []
    
    # Strategy 1: Full name
    search_terms.append(name)
    
    # Strategy 2: Individual words (for names with multiple parts)
    words = name.strip().split()
    if len(words) > 1:
        # Add significant words (> 3 chars)
        search_terms.extend([w for w in words if len(w) > 3])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_terms = []
    for term in search_terms:
        term_lower = term.lower()
        if term_lower not in seen:
            seen.add(term_lower)
            unique_terms.append(term)
    
    logger.info(f"Searching with terms: {unique_terms}")
    
    # Execute searches
    for term in unique_terms[:4]:  # Limit to 4 searches to avoid timeout
        try:
            query = supabase.table('sanctions_list').select('*')
            if entity_type != 'all':
                query = query.eq('entity_type', entity_type)
            query = query.ilike('entity_name', f'%{term}%')
            response = query.limit(500).execute()
            
            if response.data:
                all_results.extend(response.data)
                logger.info(f"  '{term}': found {len(response.data)} matches")
        except Exception as e:
            logger.error(f"Search error for '{term}': {e}")
    
    # Remove duplicates based on ID
    unique_results = {item['id']: item for item in all_results}.values()
    return list(unique_results)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok", 
        "message": "Backend is running",
        "ai_enabled": groq_client is not None
    }), 200

@app.route('/', methods=['GET'])
def root():
    return jsonify({"message": "ComplianceAI Backend API", "status": "running"}), 200

@app.route('/api/sanctions/screen', methods=['POST', 'OPTIONS'])
def sanctions_screen():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        entity_type = data.get('type', 'individual')
        use_ai = data.get('use_ai', True)
        nationality_filter = data.get('nationality', '').strip()
        
        if not name:
            return jsonify({"success": False, "error": "Name required"}), 400
        
        logger.info(f"Screening: {name} (type={entity_type}, ai={use_ai})")
        
        # Query database with flexible search
        try:
            all_matches = search_database_flexible(name, entity_type)
            logger.info(f"Found {len(all_matches)} potential matches")
        except Exception as e:
            logger.error(f"DB error: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500
        
        # Filter and score matches
        matches = []
        for entity in all_matches:
            if nationality_filter:
                nats = entity.get('nationalities', []) or []
                if not any(nationality_filter.lower() in (n or '').lower() for n in nats):
                    continue
            
            entity_name = entity.get('entity_name', '')
            name_score = calculate_fuzzy_score(name, entity_name)
            
            # Check aliases
            alias_scores = []
            for alias in (entity.get('aliases', []) or [])[:5]:
                if alias:
                    alias_scores.append(calculate_fuzzy_score(name, str(alias)))
            
            best_fuzzy = max([name_score] + alias_scores) if alias_scores else name_score
            
            # Lower threshold to 0.4 to catch more potential matches
            if best_fuzzy > 0.4:
                risk = calculate_risk_score(entity, best_fuzzy)
                matches.append({
                    **entity,
                    'match_score': round(name_score, 3),
                    'best_fuzzy_score': round(best_fuzzy, 3),
                    'combined_score': round(best_fuzzy, 3),
                    'risk_assessment': risk,
                    'ai_explanation': None
                })
        
        # Sort by score
        matches.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        matches = matches[:20]
        
        # Generate AI explanation for top 3 matches
        if use_ai and groq_client and matches:
            logger.info("Generating Groq AI explanations...")
            for i, match in enumerate(matches[:3]):
                try:
                    match['ai_explanation'] = explain_match_with_ai(name, match)
                except Exception as e:
                    logger.error(f"AI failed for match {i}: {e}")
        
        # Determine status
        status = 'no_match'
        if matches:
            top = matches[0]['combined_score']
            status = 'match' if top > 0.85 else 'potential_match' if top > 0.65 else 'low_confidence_match'
        
        return jsonify({
            "success": True,
            "data": {
                "screening_id": f"screen-{hash(name)}-{int(datetime.now().timestamp())}",
                "status": status,
                "matches": matches,
                "query": {
                    "name": name,
                    "type": entity_type,
                    "ai_enabled": use_ai and groq_client is not None
                },
                "timestamp": datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sanctions/history', methods=['GET'])
def get_history():
    """Get search history (placeholder)"""
    return jsonify({"success": True, "data": []}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
