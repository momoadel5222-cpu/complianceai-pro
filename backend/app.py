from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "*"}})

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://qwacsyreyuhhlvzcwhnw.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7es')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def calculate_similarity(str1, str2):
    str1 = str1.lower().strip()
    str2 = str2.lower().strip()
    
    if str1 == str2:
        return 1.0
    if str1 in str2 or str2 in str1:
        return 0.8
    
    words1 = set(str1.split())
    words2 = set(str2.split())
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union) if union else 0.0

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Backend is running"}), 200

@app.route('/', methods=['GET'])
def root():
    return jsonify({"message": "ComplianceAI Backend API", "status": "running"}), 200

@app.route('/api/sanctions/screen', methods=['POST', 'OPTIONS'])
def sanctions_screen():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        logger.info(f"Request: {data}")
        
        name = data.get('name', '').strip()
        entity_type = data.get('type', 'individual')
        
        if not name:
            return jsonify({"success": False, "error": "Name required"}), 400
        
        # Simple query without entity_type filter first
        try:
            response = supabase.table('sanctions_list')\
                .select('*')\
                .ilike('entity_name', f'%{name}%')\
                .limit(200)\
                .execute()
            
            all_matches = response.data if response.data else []
            logger.info(f"Found {len(all_matches)} total matches")
            
        except Exception as e:
            logger.error(f"DB error: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500
        
        # Filter and score
        matches = []
        for entity in all_matches:
            # Manual entity_type filter
            if entity.get('entity_type') != entity_type:
                continue
            
            entity_name = entity.get('entity_name', '')
            name_score = calculate_similarity(name, entity_name)
            
            alias_scores = []
            aliases = entity.get('aliases', []) or []
            for alias in aliases:
                if alias:
                    alias_scores.append(calculate_similarity(name, str(alias)))
            
            best_score = max([name_score] + alias_scores) if alias_scores else name_score
            
            if best_score > 0.6:
                matches.append({
                    **entity,
                    'match_score': name_score,
                    'alias_scores': alias_scores,
                    'best_score': best_score
                })
        
        matches.sort(key=lambda x: x.get('best_score', 0), reverse=True)
        matches = matches[:20]
        
        status = 'no_match'
        if matches:
            status = 'match' if matches[0]['best_score'] > 0.85 else 'potential_match'
        
        logger.info(f"Returning {len(matches)} matches, status: {status}")
        
        return jsonify({
            "success": True,
            "data": {
                "screening_id": f"temp-{hash(name)}",
                "status": status,
                "matches": matches
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
