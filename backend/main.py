import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Load .env in development (ignored in Render if not present)
load_dotenv()

# Read DB URL from environment variable
DATABASE_URL = os.getenv("COCKROACH_URL")

app = FastAPI(
    title="ComplianceAI Pro API",
    description="Sanctions and PEP Screening API with mock data support",
    version="2.1.0"  # Updated version
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
        print("⚠️ No database connection (COCKROACH_URL not set). Using mock data.")
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
    type: Optional[str] = None  # Changed from entity_type to type for consistency with frontend

class ScreenResponse(BaseModel):
    query: str
    entity_type: Optional[str]
    matches: List[dict]
    total_matches: int
    limit: int = 100
    offset: int = 0

# Matching logic (unchanged)
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

# Health endpoints (unchanged)
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
                "database": "not configured",
                "message": "COCKROACH_URL environment variable not set",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

        result = execute_query("SELECT COUNT(*) as count FROM sanctions_list", fetch_one=True)
        if result and result['count'] is not None:
            return {
                "status": "healthy",
                "database": "connected",
                "database_type": "CockroachDB",
                "total_entities": result['count'],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            raise Exception("Query returned no results")
    except Exception as e:
        print(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "ComplianceAI Pro API",
        "version": "2.1.0",
        "status": "operational",
        "database": "CockroachDB" if DATABASE_URL else "None (mock mode)",
        "docs": "/docs",
        "endpoints": {
            "screen": {"method": "POST", "path": "/api/screen", "description": "Screen an entity"},
            "health": {"method": "GET", "path": "/api/health", "description": "Detailed health check"},
            "stats": {"method": "GET", "path": "/api/stats", "description": "Get statistics"},
            "history": {"method": "GET", "path": "/api/history", "description": "Get screening history"}
        }
    }

# Enhanced Screening endpoint with pagination
@app.post("/api/screen")
async def screen_entity(
    request: ScreenRequest,
    limit: int = Query(100, gt=0, le=1000, description="Maximum number of results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="Minimum match score to include")
):
    name = request.name.strip()
    entity_type = request.type  # Using 'type' from request

    if not name or len(name) < 2:
        raise HTTPException(status_code=400, detail="Name must be at least 2 characters")

    # If we have a database, use it. Otherwise, return mock data.
    if DATABASE_URL:
        try:
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

            # Add pagination and ordering
            query += " ORDER BY entity_name LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            results = execute_query(query, tuple(params))

            if not results:
                return {
                    "query": name,
                    "entity_type": entity_type,
                    "matches": [],
                    "total_matches": 0,
                    "limit": limit,
                    "offset": offset
                }

            matches = []
            for row in results:
                score, match_type = calculate_match_score(row['entity_name'], name)
                if score >= min_score:  # Apply minimum score filter
                    matches.append({**row, 'combined_score': score, 'match_type': match_type})

            matches.sort(key=lambda x: x['combined_score'], reverse=True)
            return {
                "query": name,
                "entity_type": entity_type,
                "matches": matches,
                "total_matches": len(matches),
                "limit": limit,
                "offset": offset
            }
        except Exception as e:
            print(f"Database query failed: {e}")
            # Fall back to mock data if DB fails
            return generate_mock_response(name, entity_type, limit, offset, min_score)
    else:
        # No database configured - return mock data
        return generate_mock_response(name, entity_type, limit, offset, min_score)

def generate_mock_response(name: str, entity_type: Optional[str] = None, limit: int = 100, offset: int = 0, min_score: float = 0.0):
    """Generate mock response for testing without a database"""
    all_mock_matches = [
        {
            "id": "mock_1",
            "entity_name": name,
            "entity_type": entity_type or "individual",
            "first_name": name.split()[0] if name.split() else "John",
            "last_name": name.split()[-1] if len(name.split()) > 1 else "Doe",
            "list_source": "OFAC",
            "program": "SDN",
            "is_pep": False,
            "pep_level": None,
            "position": None,
            "jurisdiction": "US",
            "nationalities": ["US"],
            "aliases": [],
            "date_of_birth": "1970-01-01",
            "remarks": "This is a mock entry for testing",
            "last_updated_date": datetime.utcnow().isoformat() + "Z",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "combined_score": 1.0,
            "match_type": "exact"
        },
        {
            "id": "mock_2",
            "entity_name": f"{name} Associates",
            "entity_type": entity_type or "entity",
            "first_name": None,
            "last_name": None,
            "list_source": "EU",
            "program": "Consolidated",
            "is_pep": True,
            "pep_level": "high",
            "position": "CEO",
            "jurisdiction": "UK",
            "nationalities": ["UK"],
            "aliases": [f"Also known as {name}"],
            "date_of_birth": "1965-05-15",
            "remarks": "Mock PEP entry for testing",
            "last_updated_date": datetime.utcnow().isoformat() + "Z",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "combined_score": 0.85,
            "match_type": "partial"
        },
        {
            "id": "mock_3",
            "entity_name": f"{name} Group",
            "entity_type": entity_type or "entity",
            "first_name": None,
            "last_name": None,
            "list_source": "UN",
            "program": "Consolidated",
            "is_pep": False,
            "pep_level": None,
            "position": "Chairman",
            "jurisdiction": "CH",
            "nationalities": ["CH"],
            "aliases": [f"Also known as {name} Group"],
            "date_of_birth": None,
            "remarks": "Mock entity for testing",
            "last_updated_date": datetime.utcnow().isoformat() + "Z",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "combined_score": 0.75,
            "match_type": "partial"
        },
        {
            "id": "mock_4",
            "entity_name": f"Formerly {name}",
            "entity_type": entity_type or "individual",
            "first_name": name.split()[0] if name.split() else "John",
            "last_name": name.split()[-1] if len(name.split()) > 1 else "Doe",
            "list_source": "UK",
            "program": "Sanctions",
            "is_pep": True,
            "pep_level": "medium",
            "position": "Former Minister",
            "jurisdiction": "UK",
            "nationalities": ["UK", "US"],
            "aliases": [f"{name}", f"{name} Jr."],
            "date_of_birth": "1950-06-20",
            "remarks": "Mock PEP with aliases",
            "last_updated_date": datetime.utcnow().isoformat() + "Z",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "combined_score": 0.60,
            "match_type": "fuzzy"
        }
    ]

    # Apply score filter
    filtered_matches = [m for m in all_mock_matches if m['combined_score'] >= min_score]

    # Apply pagination
    paginated_matches = filtered_matches[offset:offset + limit]

    return {
        "query": name,
        "entity_type": entity_type,
        "matches": paginated_matches,
        "total_matches": len(filtered_matches),
        "limit": limit,
        "offset": offset
    }

# Stats endpoint (unchanged)
@app.get("/api/stats")
async def get_statistics():
    try:
        if not DATABASE_URL:
            return {
                "status": "mock",
                "message": "Returning mock statistics (no database configured)",
                "total_entities": 1250,
                "total_peps": 342,
                "total_sanctions": 908,
                "by_source": {
                    "OFAC": 450,
                    "EU": 320,
                    "UN": 210,
                    "UK": 180,
                    "Other": 90
                },
                "by_region": {
                    "Egypt": 45,
                    "UAE": 32,
                    "Saudi Arabia": 28,
                    "Kuwait": 15,
                    "Switzerland": 10
                },
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }

        total = execute_query("SELECT COUNT(*) as count FROM sanctions_list", fetch_one=True)
        total_count = total['count'] if total else 0

        pep = execute_query("SELECT COUNT(*) as count FROM sanctions_list WHERE is_pep = TRUE", fetch_one=True)
        pep_count = pep['count'] if pep else 0

        sources = execute_query("""
            SELECT list_source, COUNT(*) as count
            FROM sanctions_list
            GROUP BY list_source
            ORDER BY count DESC
        """)
        by_source = {row['list_source']: row['count'] for row in sources} if sources else {}

        mena = execute_query("""
            SELECT jurisdiction, COUNT(*) as count
            FROM sanctions_list
            WHERE is_pep = TRUE AND jurisdiction IN ('eg','kw','ae','sa','bh','om','qa','ch')
            GROUP BY jurisdiction
        """)
        country_map = {
            'eg': 'Egypt', 'kw': 'Kuwait', 'ae': 'UAE', 'sa': 'Saudi Arabia',
            'bh': 'Bahrain', 'om': 'Oman', 'qa': 'Qatar', 'ch': 'Switzerland'
        }
        by_region = {country_map.get(row['jurisdiction'], row['jurisdiction']): row['count'] for row in mena} if mena else {}

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

# History endpoint (unchanged)
@app.get("/api/history")
async def get_screening_history():
    """Get recent screening history from sanctions list"""
    try:
        if not DATABASE_URL:
            return {
                "data": [
                    {
                        "id": "mock_hist_1",
                        "entity_name": "John Doe",
                        "entity_type": "individual",
                        "list_source": "OFAC",
                        "is_pep": False,
                        "pep_level": None,
                        "position": None,
                        "jurisdiction": "US",
                        "created_at": datetime.utcnow().isoformat() + "Z"
                    },
                    {
                        "id": "mock_hist_2",
                        "entity_name": "Jane Smith",
                        "entity_type": "individual",
                        "list_source": "EU",
                        "is_pep": True,
                        "pep_level": "high",
                        "position": "Director",
                        "jurisdiction": "UK",
                        "created_at": datetime.utcnow().isoformat() + "Z"
                    },
                    {
                        "id": "mock_hist_3",
                        "entity_name": "Acme Corporation",
                        "entity_type": "entity",
                        "list_source": "UN",
                        "is_pep": False,
                        "pep_level": None,
                        "position": None,
                        "jurisdiction": "CH",
                        "created_at": datetime.utcnow().isoformat() + "Z"
                    }
                ],
                "total": 3,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message": "Mock history data (no database configured)"
            }

        query = """
            SELECT
                id::text as id,
                entity_name,
                entity_type,
                list_source,
                is_pep,
                pep_level,
                position,
                jurisdiction,
                created_at::text as created_at
            FROM sanctions_list
            ORDER BY created_at DESC
            LIMIT 50
        """
        results = execute_query(query)
        return {
            "data": results if results else [],
            "total": len(results) if results else 0,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        print(f"History error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

# Startup/shutdown events
@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("🚀 ComplianceAI Pro API Starting...")
    print(f"🕒 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    if DATABASE_URL:
        print("🗄️ Database: Connected to CockroachDB")
        print("🔍 Mode: Production (real database)")
    else:
        print("⚠️ Database: Not configured")
        print("🔍 Mode: Development (mock data)")
    print("✅ Ready to serve")
    print("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    print("\n👋 ComplianceAI Pro API Shutting down...")
    print(f"🕒 Uptime: {datetime.utcnow().strftime('%H:%M:%S')}\n")

# For local dev
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="debug"
    )