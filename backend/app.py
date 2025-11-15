from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CORS configuration
CORS(app, 
     resources={
         r"/api/*": {
             "origins": "*",
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type"],
             "supports_credentials": False
         }
     }
)

# Supabase client
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://qwacsyreyuhhlvzcwhnw.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7es')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def calculate_similarity(str1, str2):
    """Simple similarity calculation"""
    str1 = str1.lower()
    str2 = str2.lower()
    
    if str1 == str2:
        return 1.0
    
    if str1 in str2 or str2 in str1:
        return 0.8
    
    # Basic word matching
    words1 = set(str1.split())
    words2 = set(str2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

@app.route('/api/health', methods=['GET'])
def health():
    logger.info("Health check endpoint called")
    return jsonify({
        "status": "ok",
        "message": "Backend is running"
    }), 200

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "ComplianceAI Backend API",
        "status": "running"
    }), 200

@app.route('/api/sanctions/screen', methods=['POST', 'OPTIONS'])
def sanctions_screen():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        logger.info(f"Sanctions screening request received: {data}")
        
        name = data.get('name', '').strip()
        entity_type = data.get('type', 'individual')
        
        if not name:
            return jsonify({
                "success": False,
                "error": "Name is required"
            }), 400
        
        # Query Supabase
        query = supabase.table('sanctions_list').select('*').eq('entity_type', entity_type)
        
        # Search by name
        name_parts = name.split()
        if len(name_parts) > 1:
            first_name = name_parts[0]
            last_name = name_parts[-1]
            response = query.or_(f"entity_name.ilike.%{name}%,first_name.ilike.%{first_name}%,last_name.ilike.%{last_name}%").limit(100).execute()
        else:
            response = query.ilike('entity_name', f'%{name}%').limit(100).execute()
        
        potential_matches = response.data if response.data else []
        
        logger.info(f"Found {len(potential_matches)} potential matches")
        
        # Calculate similarity scores
        matches = []
        for entity in potential_matches:
            entity_name = entity.get('entity_name', '')
            
            # Calculate name similarity
            name_score = calculate_similarity(name, entity_name)
            
            # Check aliases
            alias_scores = []
            aliases = entity.get('aliases', [])
            if aliases:
                for alias in aliases:
                    alias_scores.append(calculate_similarity(name, alias))
            
            best_score = max([name_score] + alias_scores)
            
            if best_score > 0.6:  # 60% threshold
                matches.append({
                    **entity,
                    'match_score': name_score,
                    'alias_scores': alias_scores,
                    'best_score': best_score
                })
        
        # Sort by best score
        matches.sort(key=lambda x: x['best_score'], reverse=True)
        matches = matches[:20]  # Top 20 matches
        
        # Determine status
        status = 'no_match'
        if matches:
            status = 'match' if matches[0]['best_score'] > 0.85 else 'potential_match'
        
        logger.info(f"Returning {len(matches)} matches with status: {status}")
        
        result = {
            "success": True,
            "data": {
                "screening_id": "temp-" + str(hash(name)),
                "status": status,
                "matches": matches
            }
        }
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error in sanctions screening: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
