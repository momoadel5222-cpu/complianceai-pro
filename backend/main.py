import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import json

# Load .env in development
load_dotenv()

# Environment variables - Supabase + GROQ
DATABASE_URL = os.getenv("DATABASE_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = FastAPI(
    title="ComplianceAI Pro API",
    description="Sanctions and PEP Screening API with AI-powered matching",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database helper
def execute_query(query: str, params: tuple = (), fetch_one: bool = False):
    if not DATABASE_URL:
        print("⚠️ No database connection (DATABASE_URL not set). Using mock data.")
        return None

    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        return cursor.fetchone() if fetch_one else cursor.fetchall()
    except Exception as e:
        print(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

# Models
class ScreenRequest(BaseModel):
    name: str
    type: Optional[str] = None
    use_ai: Optional[bool] = False

class ScreenResponse(BaseModel):
    query: str
    entity_type: Optional[str]
    matches: List[dict]
    total_matches: int
    limit: int = 100
    offset: int = 0

# Traditional matching logic
def calculate_match_score(entity_name: str, search_name: str) -> tuple:
    entity_lower = entity_name.lower().strip()
    search_lower = search_name.lower().strip()

    if entity_lower == search_lower:
        return (1.0, "exact")
    if search_lower in entity_lower:
        score = 0.85 + (len(search_lower) / len(entity_lower) * 0.14)
        return (score, "partial")
    if entity_lower in search_lower:
        return (0.80, "partial")

    search_words = set(search_lower.split())
    entity_words = set(entity_lower.split())
    if not search_words or not entity_words:
        return (0.3, "fuzzy")

    common = search_words & entity_words
    total = search_words | entity_words
    if common:
        ratio = len(common) / len(total)
        return (0.4 + ratio * 0.4, "fuzzy")
    return (0.2, "fuzzy")

# AI-powered matching using GROQ
def ai_enhanced_match(entity_name: str, search_name: str, entity_data: dict) -> dict:
    """Use GROQ AI to assess match quality and risk level"""
    if not GROQ_API_KEY:
        return {"ai_score": None, "risk_level": "unknown", "reasoning": "AI not configured"}
    
    try:
        prompt = f"""You are a compliance screening expert. Analyze if these names likely refer to the same person/entity:

Search Query: "{search_name}"
Database Match: "{entity_name}"

Entity Details:
- Type: {entity_data.get('entity_type', 'Unknown')}
- List Source: {entity_data.get('list_source', 'Unknown')}
- Program: {entity_data.get('program', 'N/A')}
- Jurisdiction: {entity_data.get('jurisdiction', 'N/A')}

Respond ONLY with valid JSON (no markdown):
{{
  "match_probability": 0.0-1.0,
  "risk_level": "low|medium|high|critical",
  "reasoning": "brief explanation",
  "recommend_action": "clear|review|block"
}}"""

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 300
            },
            timeout=10
        )
        
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            content = content.replace('```json', '').replace('```', '').strip()
            ai_result = json.loads(content)
            return ai_result
        else:
            return {"ai_score": None, "risk_level": "unknown", "reasoning": "API error"}
    
    except Exception as e:
        print(f"AI matching error: {e}")
        return {"ai_score": None, "risk_level": "unknown", "reasoning": str(e)}

# Health endpoints
@app.get("/health")
async def health_check():
    return {
        "status": "alive",
        "service": "ComplianceAI API",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/api/health")
async def detailed_health_check():
    try:
        if not DATABASE_URL:
            return {
                "status": "degraded",
                "message": "DATABASE_URL not set",
                "database": "disconnected",
                "ai_enabled": bool(GROQ_API_KEY)
            }

        result = execute_query("SELECT COUNT(*) as count FROM sanctions_list", fetch_one=True)
        total_records = result['count'] if result else 0

        pep_result = execute_query("SELECT COUNT(*) as count FROM sanctions_list WHERE is_pep = TRUE", fetch_one=True)
        sanctions_result = execute_query("SELECT COUNT(*) as count FROM sanctions_list WHERE is_pep = FALSE", fetch_one=True)
        
        pep_count = pep_result['count'] if pep_result else 0
        sanctions_count = sanctions_result['count'] if sanctions_result else 0

        return {
            "status": "healthy",
            "database": "Supabase (Connected)",
            "total_records": total_records,
            "peps": pep_count,
            "sanctions": sanctions_count,
            "ai_enabled": bool(GROQ_API_KEY),
            "version": "3.0.0"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "database": "Supabase (Error)"
        }

# Main screening endpoint
@app.post("/api/screen", response_model=ScreenResponse)
async def screen_entity(
    request: ScreenRequest,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    search_name = request.name.strip()
    entity_type = request.type
    use_ai = request.use_ai

    if not search_name:
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    query = """
        SELECT 
            entity_name,
            entity_type,
            list_source,
            program,
            jurisdiction,
            remarks,
            is_pep
        FROM sanctions_list
        WHERE LOWER(entity_name) LIKE LOWER(%s)
    """
    params = [f"%{search_name}%"]

    if entity_type:
        query += " AND entity_type = %s"
        params.append(entity_type)

    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    try:
        results = execute_query(query, tuple(params))
        
        if not results:
            return ScreenResponse(
                query=search_name,
                entity_type=entity_type,
                matches=[],
                total_matches=0,
                limit=limit,
                offset=offset
            )

        matches = []
        for row in results:
            score, match_type = calculate_match_score(row['entity_name'], search_name)
            
            match_data = {
                "entity_name": row['entity_name'],
                "entity_type": row['entity_type'],
                "list_source": row['list_source'],
                "program": row['program'],
                "jurisdiction": row['jurisdiction'],
                "remarks": row['remarks'],
                "is_pep": row['is_pep'],
                "match_score": round(score, 2),
                "match_type": match_type
            }

            if use_ai and GROQ_API_KEY and score >= 0.7:
                ai_result = ai_enhanced_match(row['entity_name'], search_name, row)
                match_data['ai_analysis'] = ai_result

            matches.append(match_data)

        matches.sort(key=lambda x: x['match_score'], reverse=True)

        count_query = """
            SELECT COUNT(*) as count
            FROM sanctions_list
            WHERE LOWER(entity_name) LIKE LOWER(%s)
        """
        count_params = [f"%{search_name}%"]
        
        if entity_type:
            count_query += " AND entity_type = %s"
            count_params.append(entity_type)
        
        total_result = execute_query(count_query, tuple(count_params), fetch_one=True)
        total_matches = total_result['count'] if total_result else len(matches)

        return ScreenResponse(
            query=search_name,
            entity_type=entity_type,
            matches=matches,
            total_matches=total_matches,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screening failed: {str(e)}")

# Stats endpoint
@app.get("/api/stats")
async def get_statistics():
    try:
        if not DATABASE_URL:
            return {"error": "Database not configured"}

        breakdown_query = """
            SELECT 
                list_source,
                COUNT(*) as count,
                COUNT(*) FILTER (WHERE is_pep = TRUE) as pep_count,
                COUNT(*) FILTER (WHERE is_pep = FALSE) as sanction_count
            FROM sanctions_list
            GROUP BY list_source
            ORDER BY count DESC
        """
        breakdown = execute_query(breakdown_query)

        return {
            "breakdown": [dict(row) for row in breakdown] if breakdown else [],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "ComplianceAI Pro API",
        "version": "3.0.0",
        "database": "Supabase",
        "ai_engine": "GROQ (Llama 3.3 70B)" if GROQ_API_KEY else "Disabled",
        "endpoints": {
            "health": "/api/health",
            "screen": "/api/screen",
            "stats": "/api/stats"
        }
    }
