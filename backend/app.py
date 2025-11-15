from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from supabase import create_client, Client
import os
import logging
import jellyfish
import csv
import io
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://qwacsyreyuhhlvzcwhnw.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3YWNzeXJleXVoaGx2emN3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMxNDIyNzgsImV4cCI6MjA3ODcxODI3OH0.dv17Wt-3YvG-JoExolq9jXsqVMWEyDHRu074LokO7es')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def calculate_levenshtein_similarity(str1: str, str2: str) -> float:
    str1, str2 = str1.lower().strip(), str2.lower().strip()
    if not str1 or not str2:
        return 0.0
    distance = jellyfish.levenshtein_distance(str1, str2)
    max_len = max(len(str1), len(str2))
    return 1 - (distance / max_len) if max_len > 0 else 0.0

def phonetic_match(str1: str, str2: str) -> float:
    str1, str2 = str1.lower().strip(), str2.lower().strip()
    if str1 == str2:
        return 1.0
    try:
        soundex_score = 1.0 if jellyfish.soundex(str1) == jellyfish.soundex(str2) else 0.0
    except:
        soundex_score = 0.0
    try:
        metaphone_score = 1.0 if jellyfish.metaphone(str1) == jellyfish.metaphone(str2) else 0.0
    except:
        metaphone_score = 0.0
    jaro_score = jellyfish.jaro_winkler_similarity(str1, str2)
    return (soundex_score * 0.3) + (metaphone_score * 0.3) + (jaro_score * 0.4)

def calculate_weighted_score(name: str, entity: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
    entity_name = entity.get('entity_name', '')
    exact_score = 1.0 if name.lower() == entity_name.lower() else 0.0
    levenshtein_score = calculate_levenshtein_similarity(name, entity_name)
    phonetic_score = phonetic_match(name, entity_name)
    name_score = max(exact_score, levenshtein_score * 0.9, phonetic_score * 0.85)
    alias_scores = []
    aliases = entity.get('aliases', []) or []
    for alias in aliases:
        if alias:
            alias_str = str(alias)
            alias_exact = 1.0 if name.lower() == alias_str.lower() else 0.0
            alias_lev = calculate_levenshtein_similarity(name, alias_str)
            alias_phon = phonetic_match(name, alias_str)
            alias_scores.append(max(alias_exact, alias_lev * 0.9, alias_phon * 0.85))
    best_alias_score = max(alias_scores) if alias_scores else 0.0
    best_overall_score = max(name_score, best_alias_score)
    bonus = 0.0
    if filters.get('nationality'):
        entity_nationalities = entity.get('nationalities', []) or []
        if filters['nationality'].upper() in [n.upper() for n in entity_nationalities]:
            bonus += 0.05
    if filters.get('date_of_birth'):
        entity_dob = entity.get('date_of_birth_text', '')
        if entity_dob and filters['date_of_birth'] in entity_dob:
            bonus += 0.05
    source_weights = {'UN': 1.0, 'OFAC': 1.0, 'EU': 0.95, 'UK': 0.95, 'MLCU': 0.9}
    source_weight = source_weights.get(entity.get('list_source', 'OTHER'), 0.85)
    final_score = min(1.0, (best_overall_score * source_weight) + bonus)
    return {'name_score': name_score, 'phonetic_score': phonetic_score, 'levenshtein_score': levenshtein_score, 'best_alias_score': best_alias_score, 'best_score': final_score, 'alias_scores': alias_scores}

def apply_filters(entities: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
    filtered = []
    for entity in entities:
        if filters.get('nationality'):
            entity_nationalities = entity.get('nationalities', []) or []
            if not any(filters['nationality'].upper() in n.upper() for n in entity_nationalities):
                continue
        if filters.get('date_of_birth'):
            entity_dob = entity.get('date_of_birth_text', '')
            if not entity_dob or filters['date_of_birth'] not in entity_dob:
                continue
        if filters.get('date_from') or filters.get('date_to'):
            entity_date = entity.get('date_listed')
            if entity_date:
                try:
                    entity_dt = datetime.strptime(entity_date, '%Y-%m-%d')
                    if filters.get('date_from'):
                        from_dt = datetime.strptime(filters['date_from'], '%Y-%m-%d')
                        if entity_dt < from_dt:
                            continue
                    if filters.get('date_to'):
                        to_dt = datetime.strptime(filters['date_to'], '%Y-%m-%d')
                        if entity_dt > to_dt:
                            continue
                except:
                    pass
        if filters.get('program'):
            if filters['program'].lower() not in entity.get('program', '').lower():
                continue
        filtered.append(entity)
    return filtered

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
        filters = {'nationality': data.get('nationality', '').strip(), 'date_of_birth': data.get('date_of_birth', '').strip(), 'date_from': data.get('date_from', '').strip(), 'date_to': data.get('date_to', '').strip(), 'program': data.get('program', '').strip(), 'min_score': float(data.get('min_score', 0.6))}
        if not name:
            return jsonify({"success": False, "error": "Name required"}), 400
        try:
            response = supabase.table('sanctions_list').select('*').ilike('entity_name', f'%{name}%').limit(300).execute()
            all_matches = response.data if response.data else []
            logger.info(f"Found {len(all_matches)} initial matches")
        except Exception as e:
            logger.error(f"DB error: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500
        type_filtered = [e for e in all_matches if e.get('entity_type') == entity_type]
        filtered_entities = apply_filters(type_filtered, filters)
        matches = []
        for entity in filtered_entities:
            scores = calculate_weighted_score(name, entity, filters)
            if scores['best_score'] >= filters['min_score']:
                matches.append({**entity, **scores})
        matches.sort(key=lambda x: x.get('best_score', 0), reverse=True)
        matches = matches[:20]
        status = 'no_match'
        if matches:
            if matches[0]['best_score'] >= 0.9:
                status = 'match'
            elif matches[0]['best_score'] >= 0.75:
                status = 'potential_match'
            else:
                status = 'low_confidence_match'
        logger.info(f"Returning {len(matches)} matches, status: {status}")
        return jsonify({"success": True, "data": {"screening_id": f"SCR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(name) % 10000:04d}", "status": status, "matches": matches, "filters_applied": filters, "search_metadata": {"total_scanned": len(all_matches), "after_filters": len(filtered_entities), "returned": len(matches)}}}), 200
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sanctions/bulk-screen', methods=['POST', 'OPTIONS'])
def bulk_screen():
    if request.method == 'OPTIONS':
        return '', 204
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({"success": False, "error": "Only CSV files accepted"}), 400
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_data = csv.DictReader(stream)
        results = []
        for row in csv_data:
            name = row.get('name', '').strip()
            entity_type = row.get('type', 'individual').strip().lower()
            if not name:
                continue
            try:
                response = supabase.table('sanctions_list').select('*').ilike('entity_name', f'%{name}%').eq('entity_type', entity_type).limit(50).execute()
                entities = response.data if response.data else []
                matches = []
                for entity in entities:
                    scores = calculate_weighted_score(name, entity, {})
                    if scores['best_score'] >= 0.6:
                        matches.append({'entity_name': entity.get('entity_name'), 'list_source': entity.get('list_source'), 'score': scores['best_score'], 'program': entity.get('program')})
                matches.sort(key=lambda x: x['score'], reverse=True)
                top_match = matches[0] if matches else None
                status = 'no_match'
                if top_match:
                    status = 'match' if top_match['score'] >= 0.85 else 'potential_match'
                results.append({'name': name, 'type': entity_type, 'status': status, 'match_count': len(matches), 'top_match': top_match})
            except Exception as e:
                results.append({'name': name, 'type': entity_type, 'status': 'error', 'error': str(e)})
        return jsonify({"success": True, "data": {"total_screened": len(results), "results": results}}), 200
    except Exception as e:
        logger.error(f"Bulk screen error: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        total = supabase.table('sanctions_list').select('*', count='exact').execute()
        sources = supabase.table('sanctions_list').select('list_source').execute()
        source_counts = {}
        for item in sources.data:
            source = item.get('list_source', 'Unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        types = supabase.table('sanctions_list').select('entity_type').execute()
        type_counts = {}
        for item in types.data:
            etype = item.get('entity_type', 'Unknown')
            type_counts[etype] = type_counts.get(etype, 0) + 1
        return jsonify({"success": True, "data": {"total_records": total.count, "by_source": source_counts, "by_type": type_counts}}), 200
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
