from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
import os
import logging
from datetime import datetime
from fuzzywuzzy import fuzz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://qwacsyreyuhhlvzcwhnw.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7es')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or os.environ.get('OPENAI_API_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Only import Gemini if key is available
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info("✅ AI API key configured")
    except ImportError:
        logger.warning("google-generativeai not installed")
        GEMINI_API_KEY = None
else:
    logger.warning("⚠️ AI API key not found - AI features disabled")

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

def explain_match_with_ai(query_name, matched_entity):
    if not GEMINI_API_KEY: return None
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        prompt = f"Why does '{query_name}' match '{matched_entity.get('entity_name')}' on {matched_entity.get('list_source')} list? Risk level? (2 sentences max)"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"AI error: {e}")
        return None

def calculate_risk_score(entity, match_score):
    risk_score = match_score * 40
    risk_factors = []
    program = (entity.get('program') or '').lower()
    if any(k in program for k in ['terrorism', 'proliferation', 'narcotics', 'isis', 'taliban']): 
        risk_score += 30
        risk_factors.append(f"High-risk program: {entity.get('program')}")
    elif program: 
        risk_score += 15
        risk_factors.append(f"Sanctioned program: {entity.get('program')}")
    
    source = (entity.get('list_source') or '').lower()
    if any(s in source for s in ['ofac', 'un', 'eu']): 
        risk_score += 20
        risk_factors.append(f"Trusted source: {entity.get('list_source')}")
    
    risk_score = min(100, risk_score)
    level = "CRITICAL" if risk_score >= 80 else "HIGH" if risk_score >= 60 else "MEDIUM" if risk_score >= 40 else "LOW"
    return {'score': round(risk_score, 1), 'level': level, 'factors': risk_factors}

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok", 
        "message": "Backend is running", 
        "ai_features": "enabled" if GEMINI_API_KEY else "disabled", 
        "version": "2.1-Fast"
    }), 200

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "ComplianceAI Backend API", 
        "status": "running", 
        "version": "2.1-Fast"
    }), 200

@app.route('/api/sanctions/screen', methods=['POST', 'OPTIONS'])
def sanctions_screen():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        entity_type = data.get('type', 'individual')
        use_ai = data.get('use_ai', False)  # 🚀 DEFAULT FALSE FOR SPEED
        nationality_filter = data.get('nationality', '').strip()
        
        if not name:
            return jsonify({"success": False, "error": "Name required"}), 400
        
        logger.info(f"Screening: {name} (type={entity_type}, ai={use_ai})")
        
        # Fast database query
        try:
            query = supabase.table('sanctions_list').select('*')
            if entity_type != 'all':
                query = query.eq('entity_type', entity_type)
            query = query.or_(f'entity_name.ilike.%{name}%,aliases.cs.{{"{name}"}}')
            response = query.limit(100).execute()  # 🚀 Reduced from 300
            all_matches = response.data if response.data else []
            logger.info(f"Found {len(all_matches)} matches")
        except Exception as e:
            logger.error(f"DB error: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500
        
        # Fast fuzzy matching
        matches = []
        for entity in all_matches:
            if nationality_filter:
                nats = entity.get('nationalities', []) or []
                if not any(nationality_filter.lower() in (n or '').lower() for n in nats):
                    continue
            
            entity_name = entity.get('entity_name', '')
            name_score = calculate_fuzzy_score(name, entity_name)
            
            # Check aliases (limit to first 5 for speed)
            alias_scores = []
            for alias in (entity.get('aliases', []) or [])[:5]:
                if alias:
                    alias_scores.append(calculate_fuzzy_score(name, str(alias)))
            
            best_fuzzy = max([name_score] + alias_scores) if alias_scores else name_score
            
            if best_fuzzy > 0.5:
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
        
        # 🚀 Only generate AI explanation for TOP match if AI enabled
        if use_ai and GEMINI_API_KEY and matches:
            logger.info("Generating AI explanation for top match...")
            matches[0]['ai_explanation'] = explain_match_with_ai(name, matches[0])
        
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
                    "ai_enabled": use_ai and GEMINI_API_KEY is not None
                },
                "timestamp": datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
