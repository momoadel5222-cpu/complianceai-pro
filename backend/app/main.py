from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
from groq import Groq

from .db import get_supabase_client, test_connection

load_dotenv()

app = FastAPI(title="ComplianceAI Pro API", version="3.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GROQ Client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class ScreeningRequest(BaseModel):
    name: str
    country: Optional[str] = None
    date_of_birth: Optional[str] = None

class Match(BaseModel):
    entity_name: str
    entity_type: Optional[str]
    list_source: Optional[str]
    program: Optional[str]
    nationalities: Optional[List[str]]
    date_of_birth: Optional[str]
    match_score: float

@app.get("/")
def root():
    return {
        "service": "ComplianceAI Pro API",
        "version": "3.0.0",
        "database": "Supabase",
        "ai_engine": "GROQ (Llama 3.3 70B)",
        "endpoints": {
            "health": "/api/health",
            "screen": "/api/screen",
            "stats": "/api/stats"
        }
    }

@app.get("/api/health")
def health():
    db_status = test_connection()
    return {
        "status": "healthy",
        "database": db_status,
        "ai": "ready" if os.getenv("GROQ_API_KEY") else "not_configured"
    }

@app.post("/api/screen")
async def screen_entity(request: ScreeningRequest):
    try:
        supabase = get_supabase_client()
        
        # Search sanctions by name
        result = supabase.table('sanctions_list')\
            .select('*')\
            .ilike('entity_name', f'%{request.name}%')\
            .limit(10)\
            .execute()
        
        matches = []
        for record in result.data:
            matches.append({
                "entity_name": record.get("entity_name", ""),
                "entity_type": record.get("entity_type"),
                "list_source": record.get("list_source"),
                "program": record.get("program"),
                "nationalities": record.get("nationalities", []),
                "date_of_birth": record.get("date_of_birth"),
                "match_score": 0.85
            })
        
        # AI Risk Analysis if matches found
        ai_analysis = None
        if matches and os.getenv("GROQ_API_KEY"):
            try:
                prompt = f"""Analyze this compliance screening result:
                
Entity Searched: {request.name}
Country: {request.country or 'Not provided'}
DOB: {request.date_of_birth or 'Not provided'}

Matches Found: {len(matches)}
Top Match: {matches[0]['entity_name']} ({matches[0]['list_source']})

Provide a brief risk assessment (2-3 sentences) and recommended action."""

                completion = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=200
                )
                
                ai_analysis = completion.choices[0].message.content
            except Exception as e:
                ai_analysis = f"AI analysis unavailable: {str(e)}"
        
        return {
            "query": {
                "name": request.name,
                "country": request.country,
                "date_of_birth": request.date_of_birth
            },
            "total_matches": len(matches),
            "matches": matches,
            "ai_analysis": ai_analysis,
            "risk_level": "HIGH" if matches else "LOW",
            "recommended_action": "ESCALATE" if matches else "APPROVE"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screening failed: {str(e)}")

@app.get("/api/stats")
async def get_stats():
    try:
        supabase = get_supabase_client()
        result = supabase.table('sanctions_list').select("*", count='exact').limit(1).execute()
        
        return {
            "total_sanctions": result.count,
            "database": "Supabase",
            "status": "operational"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
