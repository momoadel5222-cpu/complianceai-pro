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
import jellyfish
import re
from rapidfuzz import process, fuzz as rfuzz

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173", 
            "https://complianceai-pro.vercel.app",
            "https://complianceai-pro.vercel.app/"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

DATABASE_URL = os.environ.get("DATABASE_URL")

# Check if DATABASE_URL is set
if not DATABASE_URL:
    logger.error("❌ DATABASE_URL not set in environment variables!")
    db_available = False
else:
    logger.info(f"✅ DATABASE_URL found: {DATABASE_URL[:20]}...")
    db_available = True

def get_db_connection():
    """Get database connection with proper error handling"""
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable is not set!")
        return None
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info("🔧 Fixed postgres:// to postgresql://")
    
    logger.info(f"🔗 Database URL: {database_url[:60]}...")
    
    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        cursor.close()
        logger.info("✅ Database connection successful and tested")
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"❌ Database operational error: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected database error: {e}")
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

# Arabic to English transliteration mapping
ARABIC_TO_ENGLISH = {
    'ا': 'a', 'أ': 'a', 'إ': 'e', 'آ': 'a', 'ى': 'a', 'ة': 'h',
    'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j', 'ح': 'h', 'خ': 'kh',
    'د': 'd', 'ذ': 'th', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh',
    'ص': 's', 'ض': 'd', 'ط': 't', 'ظ': 'z', 'ع': 'a', 'غ': 'gh',
    'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n',
    'ه': 'h', 'و': 'w', 'ي': 'y', 'ئ': 'e', 'ؤ': 'o', 'ء': "'"
}

def contains_arabic(text):
    """Check if text contains Arabic characters"""
    arabic_pattern = re.compile('[\u0600-\u06FF]')
    return bool(arabic_pattern.search(text))

def transliterate_arabic_to_english(text):
    """Transliterate Arabic text to English"""
    result = []
    for char in text:
        if char in ARABIC_TO_ENGLISH:
            result.append(ARABIC_TO_ENGLISH[char])
        else:
            result.append(char)
    return ''.join(result)

def advanced_phonetic_matching(name1, name2):
    """Advanced phonetic matching using multiple algorithms"""
    scores = []
    
    # Soundex
    soundex1 = jellyfish.soundex(name1)
    soundex2 = jellyfish.soundex(name2)
    soundex_score = 1.0 if soundex1 == soundex2 else 0.0
    
    # Metaphone
    metaphone1 = jellyfish.metaphone(name1)
    metaphone2 = jellyfish.metaphone(name2)
    metaphone_score = 1.0 if metaphone1 == metaphone2 else 0.0
    
    # NYSIIS
    nysiis1 = jellyfish.nysiis(name1)
    nysiis2 = jellyfish.nysiis(name2)
    nysiis_score = 1.0 if nysiis1 == nysiis2 else 0.0
    
    # Match Rating Approach
    try:
        mra1 = jellyfish.match_rating_codex(name1)
        mra2 = jellyfish.match_rating_codex(name2)
        mra_score = 1.0 if mra1 == mra2 else 0.0
    except:
        mra_score = 0.0
    
    # Average phonetic scores
    phonetic_score = (soundex_score + metaphone_score + nysiis_score + mra_score) / 4.0
    
    return phonetic_score

def generate_name_variations(name):
    """Generate common name variations and misspellings"""
    variations = set()
    name_lower = name.lower()
    
    # Original
    variations.add(name_lower)
    
    # Common substitutions
    substitutions = {
        'y': ['i', 'ie'],
        'i': ['y', 'ie'],
        'k': ['c', 'q'],
        'c': ['k', 's'],
        's': ['c', 'z'],
        'z': ['s'],
        'ph': ['f'],
        'f': ['ph'],
        'ou': ['o', 'u'],
        'ae': ['e', 'a'],
        'th': ['t'],
        'gh': ['g']
    }
    
    # Generate variations with substitutions
    for old, news in substitutions.items():
        for new in news:
            if old in name_lower:
                variations.add(name_lower.replace(old, new))
            if new in name_lower:
                variations.add(name_lower.replace(new, old))
    
    # Remove spaces and add
    variations.add(name_lower.replace(' ', ''))
    variations.add(name_lower.replace('-', ''))
    
    # Add common prefixes/suffixes variations
    words = name_lower.split()
    if len(words) > 1:
        # First + last
        variations.add(f"{words[0]} {words[-1]}")
        # Initials
        variations.add(' '.join([w[0] for w in words]))
    
    return list(variations)

def calculate_advanced_match_score(search_name, target_name):
    """Calculate advanced match score using multiple algorithms"""
    if not search_name or not target_name:
        return 0.0
    
    search_norm = search_name.lower().strip()
    target_norm = target_name.lower().strip()
    
    # Exact match
    if search_norm == target_norm:
        return 0.95  # Never 100% to leave room for manual verification
    
    # Multiple fuzzy matching algorithms with different weights
    ratio_score = fuzz.ratio(search_norm, target_norm) / 100.0
    partial_score = fuzz.partial_ratio(search_norm, target_norm) / 100.0
    token_sort_score = fuzz.token_sort_ratio(search_norm, target_norm) / 100.0
    token_set_score = fuzz.token_set_ratio(search_norm, target_norm) / 100.0
    
    # RapidFuzz weighted ratio (more advanced)
    rapidfuzz_score = rfuzz.WRatio(search_norm, target_norm) / 100.0
    
    # Phonetic matching score
    phonetic_score = advanced_phonetic_matching(search_norm, target_norm)
    
    # Calculate weighted composite score
    weights = {
        'ratio': 0.15,
        'partial': 0.20,
        'token_sort': 0.20,
        'token_set': 0.20,
        'rapidfuzz': 0.15,
        'phonetic': 0.10
    }
    
    composite_score = (
        ratio_score * weights['ratio'] +
        partial_score * weights['partial'] +
        token_sort_score * weights['token_sort'] +
        token_set_score * weights['token_set'] +
        rapidfuzz_score * weights['rapidfuzz'] +
        phonetic_score * weights['phonetic']
    )
    
    # Apply penalties for significant differences
    length_penalty = min(1.0, len(search_norm) / len(target_norm)) if len(target_norm) > 0 else 0.5
    composite_score *= length_penalty
    
    # Ensure score is between 0 and 0.91
    final_score = min(0.91, max(0.0, composite_score))
    
    return round(final_score, 3)

def get_ai_enhanced_analysis(entity, match_score, search_name, match_context):
    """Get comprehensive AI-powered risk analysis"""
    if not groq_client:
        return None, None, None
    
    try:
        prompt = f"""
        ACT as a compliance and due diligence expert. Analyze this sanctions/PEP screening match:

        SCREENING CONTEXT:
        - Searched Name: {search_name}
        - Match Confidence: {match_score * 100}%
        - Match Type: {match_context}

        MATCHED ENTITY DETAILS:
        - Full Name: {entity.get('entity_name', 'N/A')}
        - Entity Type: {entity.get('entity_type', 'N/A')}
        - List Source: {entity.get('list_source', 'N/A')}
        - Program/Sanction: {entity.get('program', 'N/A')}
        - Nationalities: {entity.get('nationalities', 'N/A')}
        - Date of Birth: {entity.get('date_of_birth', 'N/A')}
        - Place of Birth: {entity.get('place_of_birth', 'N/A')}
        - Aliases: {entity.get('aliases', 'N/A')}
        - Is PEP: {entity.get('is_pep', False)}
        - Additional Info: {entity.get('remarks', 'N/A')}

        Provide a comprehensive analysis in THREE parts:

        1. RISK ASSESSMENT: 
           - Overall risk level and confidence
           - Key risk factors identified
           - Compliance implications

        2. MATCH ANALYSIS:
           - Analysis of name matching confidence
           - Contextual factors supporting/contradicting the match
           - Potential false positive indicators

        3. DUE DILIGENCE RECOMMENDATIONS:
           - Immediate actions required
           - Additional verification steps
           - Ongoing monitoring recommendations

        Be thorough, professional, and risk-focused.
        """
        
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800
        )
        
        response = completion.choices[0].message.content
        
        # Parse the response into three parts
        parts = {
            'risk_assessment': '',
            'match_analysis': '',
            'recommendations': ''
        }
        
        current_section = None
        for line in response.split('\n'):
            line = line.strip()
            if 'RISK ASSESSMENT' in line.upper():
                current_section = 'risk_assessment'
            elif 'MATCH ANALYSIS' in line.upper():
                current_section = 'match_analysis'
            elif 'DUE DILIGENCE' in line.upper() or 'RECOMMENDATIONS' in line.upper():
                current_section = 'recommendations'
            elif current_section and line:
                parts[current_section] += line + ' '
        
        # Clean up the text
        for key in parts:
            parts[key] = parts[key].strip()
            if not parts[key]:
                parts[key] = "Analysis not available."
        
        return parts['risk_assessment'], parts['match_analysis'], parts['recommendations']
        
    except Exception as e:
        logger.error(f"AI enhanced analysis error: {e}")
        return None, None, None

def get_overall_ai_intelligence(matches, search_name, search_params):
    """Get overall AI intelligence for the screening session"""
    if not groq_client or not matches:
        return None
    
    try:
        prompt = f"""
        Provide comprehensive due diligence intelligence for this screening session:

        SEARCH PARAMETERS:
        - Name: {search_name}
        - Entity Type: {search_params.get('type', 'N/A')}
        - Nationality: {search_params.get('nationality', 'Not specified')}
        - Language: {search_params.get('language', 'English')}

        SCREENING RESULTS:
        - Total Matches Found: {len(matches)}
        - Highest Confidence Match: {matches[0]['entity_name'] if matches else 'None'}
        - Top Match Confidence: {matches[0]['combined_score'] * 100 if matches else 0}%
        - Risk Level: {matches[0]['risk_assessment']['level'] if matches else 'Low'}

        KEY MATCHES:
        {[f"{i+1}. {match['entity_name']} ({match['list_source']}) - {match['combined_score']*100}% confidence" for i, match in enumerate(matches[:3])]}

        Provide a strategic intelligence brief covering:

        1. OVERALL RISK PROFILE: Summary of compliance risk
        2. KEY FINDINGS: Most significant matches and patterns
        3. BUSINESS IMPLICATIONS: Potential impact on business relationships
        4. ACTION PLAN: Recommended due diligence workflow
        5. MONITORING RECOMMENDATIONS: Ongoing compliance measures

        Focus on practical, actionable intelligence for compliance officers.
        """
        
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Overall AI intelligence error: {e}")
        return None

def calculate_intelligent_risk_score(entity, match_score, match_context):
    """Calculate intelligent risk score considering multiple factors"""
    base_score = match_score * 40  # Base weight for name matching
    
    # Program/Sanction severity
    program = (entity.get('program') or '').lower()
    if any(k in program for k in ['terrorism', 'proliferation', 'narcotics']):
        base_score += 35
    elif any(k in program for k in ['weapons', 'wmd', 'military']):
        base_score += 25
    elif 'pep' in program.lower() or entity.get('is_pep'):
        base_score += 20
    else:
        base_score += 10

    # Source credibility weighting
    source = entity.get('list_source', '').upper()
    if source in ['OFAC', 'UN']:
        base_score += 20
    elif source in ['EU', 'UK']:
        base_score += 15
    elif source == 'PEP':
        base_score += 10

    # Match context adjustment
    if match_context == 'exact':
        base_score += 5
    elif match_context == 'phonetic':
        base_score += 2

    final_score = min(100, base_score)

    # Risk level classification
    if final_score >= 80:
        level = "CRITICAL"
    elif final_score >= 65:
        level = "HIGH"
    elif final_score >= 45:
        level = "MEDIUM"
    elif final_score >= 25:
        level = "LOW"
    else:
        level = "MINIMAL"

    return {
        'score': round(final_score, 1),
        'level': level,
        'factors': {
            'name_match': match_score * 95,
            'program_severity': program,
            'source_credibility': source,
            'match_context': match_context
        }
    }

def enhanced_bilingual_search(name, entity_type, conn, language='english'):
    """Enhanced search with bilingual support and advanced matching"""
    all_results = []
    search_terms = set()
    
    # Base search terms
    search_terms.add(name)
    
    # Generate name variations
    name_variations = generate_name_variations(name)
    search_terms.update(name_variations[:10])  # Limit variations
    
    # Bilingual processing
    if language == 'arabic' or contains_arabic(name):
        english_translation = transliterate_arabic_to_english(name)
        search_terms.add(english_translation)
        # Generate variations for English translation too
        english_variations = generate_name_variations(english_translation)
        search_terms.update(english_variations[:5])
    
    # Phonetic variations
    phonetic_terms = [
        jellyfish.soundex(name),
        jellyfish.metaphone(name),
        jellyfish.nysiis(name)
    ]
    search_terms.update(phonetic_terms)
    
    logger.info(f"🔍 Enhanced bilingual search with {len(search_terms)} terms")
    
    with conn.cursor() as cursor:
        for term in list(search_terms)[:15]:  # Limit total queries
            try:
                query = """
                SELECT * FROM sanctions_list
                WHERE entity_type = %s
                AND (
                    entity_name ILIKE %s 
                    OR %s = ANY(aliases)
                    OR entity_name ILIKE %s
                )
                LIMIT 50;
                """
                cursor.execute(query, (entity_type, f'%{term}%', term, f'{term}%'))
                results = cursor.fetchall()
                
                if results:
                    all_results.extend(results)
            except Exception as e:
                logger.error(f"Search error for '{term}': {e}")
    
    # Remove duplicates by ID
    unique_results = {item['id']: item for item in all_results}.values()
    return list(unique_results)

# Keep existing demo data function (same as before)
def get_demo_data(name: str, entity_type: str) -> List[Dict]:
    """Provide demo data when database is not available"""
    # ... (keep your existing demo data function exactly as is)
    logger.info("Using demo data - database not available")
    
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
    
    if entity_type == 'individual':
        demo_data = demo_individuals
    else:
        demo_data = demo_entities
    
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

@app.route('/api/debug', methods=['GET'])
def debug_info():
    """Debug endpoint to check environment and database"""
    conn = get_db_connection()
    
    debug_info = {
        "database_url_exists": bool(os.environ.get("DATABASE_URL")),
        "database_url_length": len(os.environ.get("DATABASE_URL", "")),
        "database_connected": bool(conn),
        "groq_api_key_exists": bool(os.environ.get("GROQ_API_KEY")),
        "environment_variables": [key for key in os.environ.keys() if 'DATABASE' in key or 'GROQ' in key or 'POSTGRES' in key]
    }
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM sanctions_list LIMIT 1")
            result = cursor.fetchone()
            debug_info["database_test_query"] = "success"
            debug_info["sample_count"] = result['count'] if result else 0
            cursor.close()
            conn.close()
        except Exception as e:
            debug_info["database_test_query"] = f"failed: {str(e)}"
            if conn:
                conn.close()
    
    return jsonify(debug_info)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'status': 'demo',
                'total_sanctions': 0,
                'message': 'Running in demo mode'
            }), 200
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM sanctions_list")
        result = cursor.fetchone()
        total = result['total'] if result else 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'active',
            'total_sanctions': total
        }), 200
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({
            'status': 'error',
            'total_sanctions': 0,
            'error': str(e)
        }), 500

@app.route('/api/screen', methods=['POST', 'OPTIONS'])
def sanctions_screen():
    if request.method == 'OPTIONS':
        return '', 204

    conn = None
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        entity_type = data.get('type', 'individual')
        use_ai = data.get('enhanced_ai', True)
        phonetic_search = data.get('phonetic_search', True)
        language = data.get('language', 'english')
        nationality_filter = data.get('nationality', '').strip()

        if not name:
            return jsonify({"success": False, "error": "Name required"}), 400

        logger.info(f"🔍 Advanced AI Screening: {name} (type={entity_type}, language={language})")

        # Enhanced search processing
        search_name = name
        phonetic_suggestions = generate_name_variations(name)
        
        # Bilingual processing
        if language == 'arabic' or contains_arabic(name):
            english_translation = transliterate_arabic_to_english(name)
            phonetic_suggestions.extend(generate_name_variations(english_translation))
            logger.info(f"🌍 Bilingual processing: {name} -> {english_translation}")

        conn = get_db_connection()
        
        if not conn:
            all_matches = get_demo_data(name, entity_type)
            is_demo_mode = True
        else:
            try:
                all_matches = enhanced_bilingual_search(name, entity_type, conn, language)
                logger.info(f"📊 Found {len(all_matches)} potential matches")
                is_demo_mode = False
            except Exception as e:
                logger.error(f"DB error: {str(e)}")
                all_matches = get_demo_data(name, entity_type)
                is_demo_mode = True

        matches = []
        for entity in all_matches:
            if nationality_filter:
                nats = entity.get('nationalities', []) or []
                if not any(nationality_filter.lower() in (n or '').lower() for n in nats):
                    continue

            entity_name = entity.get('entity_name', '')
            
            # Advanced matching with context detection
            match_score = calculate_advanced_match_score(name, entity_name)
            match_context = "exact" if match_score > 0.9 else "phonetic" if match_score > 0.7 else "fuzzy"
            
            # Check aliases with advanced matching
            alias_scores = []
            for alias in (entity.get('aliases', []) or [])[:10]:
                if alias:
                    alias_score = calculate_advanced_match_score(name, str(alias))
                    alias_scores.append(alias_score)

            best_score = max([match_score] + alias_scores) if alias_scores else match_score

            if best_score > 0.25:  # Reasonable threshold for advanced matching
                risk = calculate_intelligent_risk_score(entity, best_score, match_context)
                
                # Enhanced AI analysis
                risk_analysis = None
                match_analysis = None
                recommendations = None
                if use_ai and groq_client:
                    risk_analysis, match_analysis, recommendations = get_ai_enhanced_analysis(
                        entity, best_score, name, match_context
                    )
                
                # Format data for response
                aliases = entity.get('aliases', []) or []
                aliases_str = ', '.join([a for a in aliases if a]) if aliases else 'None'
                nationalities = entity.get('nationalities', []) or []
                nats_str = ', '.join([n for n in nationalities if n]) if nationalities else 'Not specified'
                dob = entity.get('date_of_birth') or entity.get('dob') or 'Not specified'
                place_of_birth = entity.get('place_of_birth') or entity.get('pob') or 'Not specified'
                remarks = entity.get('remarks', '') or ''
                jurisdiction = entity.get('jurisdiction', '') or ''
                
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
                    'match_score': round(match_score, 3),
                    'best_fuzzy_score': round(best_score, 3),
                    'combined_score': round(best_score, 3),
                    'risk_assessment': risk,
                    'risk_analysis': risk_analysis,
                    'match_analysis': match_analysis,
                    'recommendations': recommendations,
                    'match_context': match_context,
                    'phonetic_matches': phonetic_suggestions[:5]
                })

        matches.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        matches = matches[:12]

        # Overall AI intelligence
        overall_ai_intelligence = None
        risk_level = matches[0]['risk_assessment']['level'] if matches else "LOW"
        if use_ai and groq_client:
            search_params = {
                'type': entity_type,
                'nationality': nationality_filter,
                'language': language
            }
            overall_ai_intelligence = get_overall_ai_intelligence(matches, name, search_params)

        logger.info(f"✅ Returning {len(matches)} enhanced matches with advanced AI analysis")

        return jsonify({
            "name": name,
            "match_found": len(matches) > 0,
            "matches": [
                {
                    "name": m['entity_name'],
                    "list_type": m.get('list_source', 'Unknown'),
                    "confidence": m['combined_score'],
                    "program": m.get('program', 'N/A'),
                    "nationalities": m['nationalities'],
                    "aliases": m['aliases'],
                    "date_of_birth": m['date_of_birth'],
                    "place_of_birth": m['place_of_birth'],
                    "jurisdiction": m.get('jurisdiction', ''),
                    "remarks": m.get('remarks', ''),
                    "is_pep": m.get('is_pep', False),
                    "risk_analysis": m.get('risk_analysis'),
                    "match_analysis": m.get('match_analysis'),
                    "recommendations": m.get('recommendations'),
                    "match_context": m.get('match_context'),
                    "phonetic_matches": m.get('phonetic_matches', [])
                }
                for m in matches[:10]
            ],
            "risk_level": risk_level,
            "timestamp": datetime.now().isoformat(),
            "demo_mode": is_demo_mode,
            "ai_intelligence": overall_ai_intelligence,
            "phonetic_suggestions": phonetic_suggestions[:8],
            "total_matches": len(matches)
        }), 200

    except Exception as e:
        logger.error(f"❌ Advanced screening error: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# Keep other endpoints (register, login, logout) the same as before
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
    logger.info(f"🚀 Starting advanced AI screening server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)