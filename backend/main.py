import os
from dotenv import load_dotenv

# Load .env in development (ignored in Render if not present)
load_dotenv()

# ✅ CORRECT: Read from environment variable named "COCKROACH_URL"
DATABASE_URL = os.getenv("COCKROACH_URL")

if not DATABASE_URL:
    raise RuntimeError("❌ Missing COCKROACH_URL environment variable")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(
    title="ComplianceAI Pro API",
    description="Sanctions and PEP Screening API",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database function (replacing your config.execute_query)
def execute_query(query: str, params: tuple = (), fetch_one: bool = False):
    """Execute a query and return results"""
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        
        if fetch_one:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()
            
        return result
        
    except Exception as e:
        print(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

# Request/Response Models
class ScreenRequest(BaseModel):
    name: str
    entity_type: Optional[str] = None

def calculate_match_score(entity_name: str, search_name: str) -> tuple:
    """Calculate similarity score between entity name and search query"""
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
    
    common_words = search_words & entity_words
    total_words = search_words | entity_words
    
    if common_words:
        overlap_ratio = len(common_words) / len(total_words)
        score = 0.4 + (overlap_ratio * 0.4)
        return (score, "fuzzy")
    
    return (0.2, "fuzzy")

# API Endpoints
@app.get("/")
async def root():
    return {
        "service": "ComplianceAI Pro API",
        "version": "2.0.0",
        "status": "operational",
        "database": "CockroachDB"
    }

@app.get("/api/health")
async def health_check():
    try:
        result = execute_query(
            "SELECT COUNT(*) as count FROM sanctions_list",
            fetch_one=True
        )
        
        if result and result['count'] is not None:
            return {
                "status": "healthy",
                "database": "connected",
                "database_type": "CockroachDB",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            raise Exception("Database query returned no results")
            
    except Exception as e:
        print(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/api/screen")
async def screen_entity(request: ScreenRequest):
    try:
        name = request.name.strip()
        entity_type = request.entity_type
        
        if not name or len(name) < 2:
            raise HTTPException(status_code=400, detail="Name must be at least 2 characters")
        
        query = """
            SELECT 
                id::text as id,
                entity_name,
                entity_type,
                first_name,
                last_name,
                list_source,
                program,
                is_pep,
                pep_level,
                position,
                jurisdiction,
                nationalities,
                aliases,
                date_of_birth::text as date_of_birth,
                remarks,
                last_updated_date::text as last_updated_date,
                created_at::text as created_at
            FROM sanctions_list
            WHERE LOWER(entity_name) LIKE LOWER(%s)
        """
        
        params = [f'%{name}%']
        
        if entity_type:
            query += " AND entity_type = %s"
            params.append(entity_type)
        
        query += " ORDER BY entity_name LIMIT 100"
        
        results = execute_query(query, tuple(params))
        
        if not results:
            return {
                "query": name,
                "entity_type": entity_type,
                "matches": [],
                "total_matches": 0
            }
        
        matches = []
        for row in results:
            score, match_type = calculate_match_score(row['entity_name'], name)
            
            matches.append({
                **row,
                'combined_score': score,
                'match_type': match_type
            })
        
        matches.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return {
            "query": name,
            "entity_type": entity_type,
            "matches": matches,
            "total_matches": len(matches)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Search error for '{request.name}': {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/stats")
async def get_statistics():
    try:
        total_result = execute_query("SELECT COUNT(*) as count FROM sanctions_list", fetch_one=True)
        total_count = total_result['count'] if total_result else 0
        
        pep_result = execute_query("SELECT COUNT(*) as count FROM sanctions_list WHERE is_pep = TRUE", fetch_one=True)
        pep_count = pep_result['count'] if pep_result else 0
        
        source_results = execute_query("""
            SELECT list_source, COUNT(*) as count
            FROM sanctions_list
            GROUP BY list_source
            ORDER BY count DESC
        """)
        
        by_source = {}
        if source_results:
            by_source = {row['list_source']: row['count'] for row in source_results}
        
        mena_results = execute_query("""
            SELECT jurisdiction, COUNT(*) as count
            FROM sanctions_list
            WHERE is_pep = TRUE 
            AND jurisdiction IN ('eg', 'kw', 'ae', 'sa', 'bh', 'om', 'qa')
            GROUP BY jurisdiction
        """)
        
        by_region = {}
        country_map = {'eg': 'Egypt', 'kw': 'Kuwait', 'ae': 'UAE', 'sa': 'Saudi Arabia', 'bh': 'Bahrain', 'om': 'Oman', 'qa': 'Qatar'}
        
        if mena_results:
            for row in mena_results:
                country_name = country_map.get(row['jurisdiction'], row['jurisdiction'])
                by_region[country_name] = row['count']
        
        return {
            "total_entities": total_count,
            "total_peps": pep_count,
            "total_sanctions": total_count - pep_count,
            "by_source": by_source,
            "by_region": by_region,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("🚀 ComplianceAI Pro API Starting...")
    print("=" * 60)
    print(f"📊 Database: CockroachDB")
    
    try:
        result = execute_query("SELECT COUNT(*) as count FROM sanctions_list", fetch_one=True)
        if result:
            print(f"✅ Database connected: {result['count']:,} entities loaded")
        
        pep_result = execute_query("SELECT COUNT(*) as count FROM sanctions_list WHERE is_pep = TRUE", fetch_one=True)
        if pep_result:
            print(f"🎩 PEPs available: {pep_result['count']:,}")
        
        print("=" * 60)
        print("✅ API Ready!")
        print("=" * 60)
        
    except Exception as e:
        print(f"⚠️ Database connection warning: {e}")
        print("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    print("\n👋 ComplianceAI Pro API Shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)