from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
import os
import logging
from datetime import datetime
from openai import OpenAI
from fuzzywuzzy import fuzz
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://qwacsyreyuhhlvzcwhnw.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7es')
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configure DeepSeek client
deepseek_client = None
if DEEPSEEK_API_KEY:
    deepseek_client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com/v1"
    )
    logger.info("✅ DeepSeek API key configured")
else:
    logger.warning("⚠️ DeepSeek API key not found - AI features disabled")

def calculate_fuzzy_score(str1, str2):
    if not str1 or not str2: return 0.0
    str1, str2 = str1.lower().strip(), str2.lower().strip()
    if str1 == str2: return 1.0
    if str1 in str2 or str2 in str1: return 0.9
    return round((fuzz.ratio(str1, str2) * 0.2 + fuzz.partial_ratio(str1, str2) * 0.2 + 
                  fuzz.token_sort_ratio(str1, str2) * 0.3 + fuzz.token_set_ratio(str1, str2) * 0.3) / 100.0, 3)

def get_embedding_deepseek(text):
    if not deepseek_client: return None
    try:
        response = deepseek_client.embeddings.create(
            model="text-embedding",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"DeepSeek embedding error: {e}")
        return None

def cosine_similarity(vec1, vec2):
    if vec1 is None or vec2 is None: return 0.0
    vec1, vec2 = np.array(vec1), np.array(vec2)
    dot = np.dot(vec1, vec2)
    norm = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    return dot / norm if norm != 0 else 0.0

def explain_match_with_deepseek(query_name, matched_entity):
    if not deepseek_client: return "AI explanation unavailable"
    try:
        prompt = f"""Analyze this sanctions match for compliance screening:

QUERY: {query_name}
MATCHED ENTITY: {matched_entity.get('entity_name')}
ALIASES: {', '.join(matched_entity.get('aliases', [])[:3])}
NATIONALITIES: {', '.join(matched_entity.get('nationalities', []))}
SANCTIONS PROGRAM: {matched_entity.get('program', 'N/A')}
SOURCE LIST: {matched_entity.get('list_source', 'N/A')}

Provide a concise 2-3 sentence analysis explaining:
1. Why this match occurred (name similarity, aliases, etc.)
2. Key compliance risks and confidence level
3. Recommended next steps for due diligence"""

        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a compliance analyst specializing in sanctions screening and financial crime prevention."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"DeepSeek explanation error: {e}")
        return f"Unable to generate explanation: {str(e)}"

def calculate_risk_score(entity, match_score, semantic_score=None):
    risk_score = match_score * 40
    risk_factors = []
    
    if semantic_score and semantic_score > 0.7:
        risk_score += semantic_score * 20
        risk_factors.append("High semantic similarity")
    
    high_risk = ['terrorism', 'proliferation', 'narcotics', 'isis', 'al-qaeda', 'taliban']
    program = entity.get('program', '').lower()
    if any(k in program for k in high_risk):
        risk_score += 20
        risk_factors.append(f"High-risk program: {entity.get('program')}")
    elif program:
        risk_score += 10
        risk_factors.append(f"Listed program: {entity.get('program')}")
    
    if any(s in entity.get('list_source', '').lower() for s in ['ofac', 'un', 'eu', 'uk']):
        risk_score += 10
        risk_factors.append(f"Trusted source: {entity.get('list_source')}")
    
    date_listed = entity.get('date_listed')
    if date_listed:
        try:
            if isinstance(date_listed, str):
                listed = datetime.fromisoformat(date_listed.replace('Z', '+00:00'))
                days = (datetime.now(listed.tzinfo or None) - listed).days
                if days < 365:
                    risk_score += 10
                    risk_factors.append("Recently listed")
                elif days < 1825:
                    risk_score += 5
        except:
            pass
    
    risk_score = min(100, risk_score)
    level = "CRITICAL" if risk_score >= 80 else "HIGH" if risk_score >= 60 else "MEDIUM" if risk_score >= 40 else "LOW"
    return {'score': round(risk_score, 1), 'level': level, 'factors': risk_factors}

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "message": "Backend is running",
        "ai_features": "enabled" if DEEPSEEK_API_KEY else "disabled",
        "ai_provider": "DeepSeek",
        "version": "2.0-DeepSeek"
    }), 200

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "ComplianceAI Backend API",
        "status": "running",
        "version": "2.0-DeepSeek",
        "ai_provider": "DeepSeek"
    }), 200

@app.route('/api/sanctions/screen', methods=['POST', 'OPTIONS'])
def sanctions_screen():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        logger.info(f"Screening request: {data}")
        
        name = data.get('name', '').strip()
        entity_type = data.get('type', 'individual')
        use_ai = data.get('use_ai', True)
        nationality_filter = data.get('nationality', '').strip()
        
        if not name:
            return jsonify({"success": False, "error": "Name required"}), 400
        
        # Get query embedding with DeepSeek
        query_embedding = get_embedding_deepseek(name) if use_ai and DEEPSEEK_API_KEY else None
        if query_embedding:
            logger.info("✅ Generated query embedding with DeepSeek")
        
        # Query database
        try:
            query = supabase.table('sanctions_list').select('*')
            if entity_type != 'all':
                query = query.eq('entity_type', entity_type)
            query = query.or_(f'entity_name.ilike.%{name}%,aliases.cs.{{"{name}"}}')
            response = query.limit(300).execute()
            all_matches = response.data if response.data else []
            logger.info(f"Found {len(all_matches)} database matches")
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500
        
        # Process matches
        matches = []
        for entity in all_matches:
            # Apply nationality filter
            if nationality_filter:
                nats = entity.get('nationalities', []) or []
                if not any(nationality_filter.lower() in (n or '').lower() for n in nats):
                    continue
            
            entity_name = entity.get('entity_name', '')
            name_score = calculate_fuzzy_score(name, entity_name)
            alias_scores = [calculate_fuzzy_score(name, str(a)) for a in (entity.get('aliases', []) or []) if a]
            best_fuzzy = max([name_score] + alias_scores) if alias_scores else name_score
            
            # Semantic scoring with DeepSeek
            semantic_score = None
            if query_embedding and use_ai:
                entity_text = f"{entity_name} {' '.join((entity.get('aliases', []) or [])[:3])}"
                entity_emb = get_embedding_deepseek(entity_text)
                if entity_emb:
                    semantic_score = cosine_similarity(query_embedding, entity_emb)
            
            # Combined score
            combined = (best_fuzzy * 0.6 + semantic_score * 0.4) if semantic_score else best_fuzzy
            
            if combined > 0.5:
                risk = calculate_risk_score(entity, combined, semantic_score)
                matches.append({
                    **entity,
                    'match_score': round(name_score, 3),
                    'best_fuzzy_score': round(best_fuzzy, 3),
                    'semantic_score': round(semantic_score, 3) if semantic_score else None,
                    'combined_score': round(combined, 3),
                    'risk_assessment': risk,
                    'ai_explanation': None
                })
        
        # Sort by combined score
        matches.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        # Generate AI explanations for top matches
        if use_ai and DEEPSEEK_API_KEY and matches:
            for i, m in enumerate(matches[:3]):
                logger.info(f"Generating DeepSeek explanation for match {i+1}")
                m['ai_explanation'] = explain_match_with_deepseek(name, m)
        
        matches = matches[:20]
        
        # Determine status
        status = 'no_match'
        if matches:
            top = matches[0]['combined_score']
            status = 'match' if top > 0.85 else 'potential_match' if top > 0.65 else 'low_confidence_match'
        
        logger.info(f"Returning {len(matches)} matches, status: {status}")
        
        return jsonify({
            "success": True,
            "data": {
                "screening_id": f"screen-{hash(name)}-{int(datetime.now().timestamp())}",
                "status": status,
                "matches": matches,
                "query": {
                    "name": name,
                    "type": entity_type,
                    "ai_enabled": use_ai and DEEPSEEK_API_KEY is not None,
                    "ai_provider": "DeepSeek" if DEEPSEEK_API_KEY else None
                },
                "timestamp": datetime.now().isoformat()
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Screening error: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
