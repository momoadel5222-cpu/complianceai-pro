from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import logging
from datetime import datetime
from typing import List, Dict, Any
from fuzzywuzzy import fuzz
from groq import Groq
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

DATABASE_URL = os.environ.get("DATABASE_URL")

# Check if DATABASE_URL is set
if not DATABASE_URL:
    logger.error("❌ DATABASE_URL not set in environment variables!")
    # We'll continue but with a fallback mode
    db_available = False
else:
    logger.info(f"✅ DATABASE_URL found: {DATABASE_URL[:20]}...")
    db_available = True

def get_db_connection():
    """Get database connection with proper error handling"""
    if not db_available:
        logger.warning("Database not available - running in demo mode")
        return None
        
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

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

def normalize_name(name: str) -> str:
    """Normalize names for better matching"""
    if not name:
        return ""
    normalized = ' '.join(name.lower().strip().split())
    prefixes = ['mr.', 'mrs.', 'ms.', 'dr.', 'prof.', 'hon.']
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
    return normalized

def calculate_fuzzy_score(str1: str, str2: str) -> float:
    """Enhanced fuzzy matching with multiple algorithms"""
    if not str1 or not str2:
        return 0.0
    
    str1_norm = normalize_name(str1)
    str2_norm = normalize_name(str2)
    
    if str1_norm == str2_norm:
        return 1.0
    
    if str1_norm in str2_norm or str2_norm in str1_norm:
        return 0.95
    
    ratio = fuzz.ratio(str1_norm, str2_norm) / 100.0
    partial = fuzz.partial_ratio(str1_norm, str2_norm) / 100.0
    token_sort = fuzz.token_sort_ratio(str1_norm, str2_norm) / 100.0
    token_set = fuzz.token_set_ratio(str1_norm, str2_norm) / 100.0
    
    score = (ratio * 0.15 + partial * 0.25 + token_sort * 0.25 + token_set * 0.35)
    return round(score, 3)

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
    elif 'pep' in program.lower() or entity.get('is_pep'):
        base_score += 15
        severity = "MEDIUM"
    else:
        base_score += 10
        severity = "MEDIUM"

    source = entity.get('list_source', '').upper()
    if source in ['OFAC', 'UN']:
        base_score += 15
    elif source in ['EU', 'UK']:
        base_score += 10
    elif source == 'PEP':
        base_score += 8

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

def search_database_flexible(name: str, entity_type: str, conn) -> List[Dict]:
    """Search database with multiple strategies"""
    all_results = []
    search_terms = []

    search_terms.append(name)

    words = name.strip().split()
    if len(words) > 1:
        search_terms.extend([w for w in words if len(w) > 2])

    if len(words) >= 2:
        search_terms.append(f"{words[0]} {words[-1]}")

    seen = set()
    unique_terms = []
    for term in search_terms:
        term_lower = term.lower()
        if term_lower not in seen:
            seen.add(term_lower)
            unique_terms.append(term)

    logger.info(f"Searching with terms: {unique_terms}")

    with conn.cursor() as cursor:
        for term in unique_terms[:5]:
            try:
                query = """
                SELECT * FROM sanctions_list
                WHERE entity_type = %s
                AND (entity_name ILIKE %s OR %s = ANY(aliases))
                LIMIT 500;
                """
                cursor.execute(query, (entity_type, f'%{term}%', term))
                results = cursor.fetchall()

                if results:
                    all_results.extend(results)
                    logger.info(f"  '{term}': found {len(results)} matches")
            except Exception as e:
                logger.error(f"Search error for '{term}': {e}")

    unique_results = {item['id']: item for item in all_results}.values()
    return list(unique_results)

def get_demo_data(name: str, entity_type: str) -> List[Dict]:
    """Provide demo data when database is not available"""
    logger.info("Using demo data - database not available")
    
    # Demo data for testing
    demo_individuals = [
        {
            'id': 1,
            'entity_name': 'Mostafa Madbouly',
            'entity_type': 'individual',
            'list_source': 'PEP',
            'program': 'Egypt Prime Minister',
            'nationalities': ['EGYPTIAN'],
            'aliases': ['Mostafa Kamal Madbouly', 'مصطفى مدبولي'],
            'date_of_birth': '1966-04-28',
            'place_of_birth': 'Cairo, Egypt',
            'jurisdiction': 'Egypt',
            'remarks': 'Current Prime Minister of Egypt',
            'is_pep': True
        },
        {
            'id': 2,
            'entity_name': 'Ahmed Zewail',
            'entity_type': 'individual',
            'list_source': 'PEP',
            'program': 'Egyptian Scientist',
            'nationalities': ['EGYPTIAN', 'AMERICAN'],
            'aliases': ['Ahmed Hassan Zewail'],
            'date_of_birth': '1946-02-26',
            'place_of_birth': 'Damanhur, Egypt',
            'jurisdiction': 'Egypt, USA',
            'remarks': 'Nobel Prize winner in Chemistry',
            'is_pep': False
        },
        {
            'id': 3,
            'entity_name': 'Vladimir Putin',
            'entity_type': 'individual',
            'list_source': 'PEP',
            'program': 'Russian President',
            'nationalities': ['RUSSIAN'],
            'aliases': ['Vladimir Vladimirovich Putin', 'Владимир Путин'],
            'date_of_birth': '1952-10-07',
            'place_of_birth': 'Leningrad, Soviet Union',
            'jurisdiction': 'Russia',
            'remarks': 'Current President of Russia',
            'is_pep': True
        }
    ]
    
    demo_entities = [
        {
            'id': 101,
            'entity_name': 'Egyptian Armed Forces',
            'entity_type': 'entity',
            'list_source': 'OFAC',
            'program': 'Military Sanctions',
            'nationalities': [],
            'aliases': ['EAF', 'Egyptian Military'],
            'date_of_birth': None,
            'place_of_birth': None,
            'jurisdiction': 'Egypt',
            'remarks': 'State military organization',
            'is_pep': False
        }
    ]
    
    # Filter based on entity type
    if entity_type == 'individual':
        demo_data = demo_individuals
    else:
        demo_data = demo_entities
    
    # Simple name matching for demo
    results = []
    name_lower = name.lower()
    for item in demo_data:
        if name_lower in item['entity_name'].lower():
            results.append(item)
        else:
            for alias in item.get('aliases', []):
                if name_lower in alias.lower():
                    results.append(item)
                    break
    
    return results

@app.route('/api/health', methods=['GET'])
def health():
    conn = get_db_connection()
    db_status = "connected" if conn else "disconnected"
    if conn:
        conn.close()
    
    return jsonify({
        "status": "ok",
        "message": "Backend is running",
        "ai_enabled": groq_client is not None,
        "database": db_status,
        "demo_mode": not db_available
    }), 200

@app.route('/', methods=['GET'])
def root():
    return jsonify({"message": "ComplianceAI Backend API", "status": "running"}), 200

@app.route('/api/screen', methods=['POST', 'OPTIONS'])
@app.route('/api/sanctions/screen', methods=['POST', 'OPTIONS'])
def sanctions_screen():
    if request.method == 'OPTIONS':
        return '', 204

    conn = None
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        entity_type = data.get('type', 'individual')
        use_ai = data.get('use_ai', True)
        nationality_filter = data.get('nationality', '').strip()

        if not name:
            return jsonify({"success": False, "error": "Name required"}), 400

        logger.info(f"🔍 Screening: {name} (type={entity_type})")

        # Try to connect to database
        conn = get_db_connection()
        
        if not conn:
            # Use demo data if database is not available
            logger.warning("Using demo data - database not available")
            all_matches = get_demo_data(name, entity_type)
            is_demo_mode = True
        else:
            try:
                all_matches = search_database_flexible(name, entity_type, conn)
                logger.info(f"📊 Found {len(all_matches)} potential matches")
                is_demo_mode = False
            except Exception as e:
                logger.error(f"DB error: {str(e)}")
                # Fallback to demo data
                logger.warning("Falling back to demo data due to DB error")
                all_matches = get_demo_data(name, entity_type)
                is_demo_mode = True

        matches = []
        for entity in all_matches:
            if nationality_filter:
                nats = entity.get('nationalities', []) or []
                if not any(nationality_filter.lower() in (n or '').lower() for n in nats):
                    continue

            entity_name = entity.get('entity_name', '')
            name_score = calculate_fuzzy_score(name, entity_name)

            alias_scores = []
            matched_alias = None
            for alias in (entity.get('aliases', []) or [])[:10]:
                if alias:
                    alias_score = calculate_fuzzy_score(name, str(alias))
                    alias_scores.append(alias_score)
                    if alias_score > name_score and not matched_alias:
                        matched_alias = alias

            best_fuzzy = max([name_score] + alias_scores) if alias_scores else name_score

            if best_fuzzy > 0.3:
                risk = calculate_risk_score(entity, best_fuzzy)
                
                # Format aliases for display
                aliases = entity.get('aliases', []) or []
                aliases_str = ', '.join([a for a in aliases if a]) if aliases else 'None'
                
                # Format nationalities
                nationalities = entity.get('nationalities', []) or []
                nats_str = ', '.join([n for n in nationalities if n]) if nationalities else 'Not specified'
                
                # Get additional fields
                dob = entity.get('date_of_birth') or entity.get('dob') or 'Not specified'
                place_of_birth = entity.get('place_of_birth') or entity.get('pob') or 'Not specified'
                remarks = entity.get('remarks', '') or ''
                jurisdiction = entity.get('jurisdiction', '') or ''
                
                # Build comprehensive details
                details_parts = []
                details_parts.append(f"Program: {entity.get('program', 'N/A')}")
                details_parts.append(f"Source: {entity.get('list_source', 'Unknown')}")
                details_parts.append(f"Type: {'PEP' if entity.get('is_pep') else 'Sanctions'}")
                if aliases_str != 'None':
                    details_parts.append(f"Aliases: {aliases_str}")
                details_parts.append(f"Nationalities: {nats_str}")
                if dob != 'Not specified':
                    details_parts.append(f"DOB: {dob}")
                if place_of_birth != 'Not specified':
                    details_parts.append(f"POB: {place_of_birth}")
                if jurisdiction:
                    details_parts.append(f"Jurisdiction: {jurisdiction}")
                if remarks:
                    details_parts.append(f"Remarks: {remarks}")
                if matched_alias:
                    details_parts.append(f"Matched via alias: {matched_alias}")
                
                matches.append({
                    'id': entity.get('id'),
                    'entity_name': entity.get('entity_name'),
                    'entity_type': entity.get('entity_type'),
                    'list_source': entity.get('list_source'),
                    'program': entity.get('program'),
                    'nationalities': nats_str,
                    'aliases': aliases_str,
                    'date_of_birth': dob,
                    'place_of_birth': place_of_birth,
                    'jurisdiction': jurisdiction,
                    'remarks': remarks,
                    'is_pep': entity.get('is_pep', False),
                    'match_score': round(name_score, 3),
                    'best_fuzzy_score': round(best_fuzzy, 3),
                    'combined_score': round(best_fuzzy, 3),
                    'risk_assessment': risk,
                    'details': ' | '.join(details_parts)
                })

        matches.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        matches = matches[:20]

        logger.info(f"✅ Returning {len(matches)} matches")
        if matches:
            logger.info(f"🎯 Top: {matches[0]['entity_name']} ({matches[0]['combined_score']})")

        return jsonify({
            "name": name,
            "match_found": len(matches) > 0,
            "matches": [
                {
                    "name": m['entity_name'],
                    "list_type": m.get('list_source', 'Unknown'),
                    "confidence": m['combined_score'],
                    "details": m['details'],
                    "program": m.get('program', 'N/A'),
                    "nationalities": m['nationalities'],
                    "aliases": m['aliases'],
                    "date_of_birth": m['date_of_birth'],
                    "place_of_birth": m['place_of_birth'],
                    "jurisdiction": m.get('jurisdiction', ''),
                    "remarks": m.get('remarks', ''),
                    "is_pep": m.get('is_pep', False)
                }
                for m in matches[:10]
            ],
            "risk_level": matches[0]['risk_assessment']['level'] if matches else "Low",
            "timestamp": datetime.now().isoformat(),
            "demo_mode": is_demo_mode
        }), 200

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if conn:
            conn.close()


# ============= AUTHENTICATION ENDPOINTS =============

@app.route('/api/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 204
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name', '')
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'}), 400
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': True, 'user': {'id': 'demo', 'email': email, 'full_name': full_name, 'role': 'user'}, 'message': 'Demo registration'}), 201
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM public.profiles WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Email already registered'}), 400
        cursor.execute("INSERT INTO public.profiles (email, full_name, role) VALUES (%s, %s, 'user') RETURNING id, email, full_name, role", (email, full_name))
        user = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'user': dict(user), 'message': 'Registration successful'}), 201
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'}), 400
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': True, 'user': {'id': 'demo-user', 'email': email, 'full_name': 'Demo User', 'role': 'user'}, 'message': 'Demo login'}), 200
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, full_name, role, company FROM public.profiles WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if not user:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        return jsonify({'success': True, 'user': dict(user), 'message': 'Login successful'}), 200
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logout', methods=['POST', 'OPTIONS'])
def logout():
    if request.method == 'OPTIONS':
        return '', 204
    return jsonify({'success': True, 'message': 'Logout successful'}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)

