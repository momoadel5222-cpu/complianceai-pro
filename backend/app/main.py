from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from .db import engine, SessionLocal
from .models import Base, ScreenRequest

app = FastAPI()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ScreenIn(BaseModel):
    name: str

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/screen")
def screen(payload: ScreenIn, db: Session = Depends(get_db)):
    row = ScreenRequest(name=payload.name)
    db.add(row)
    db.commit()
    return {"matches": [], "status": "no_match"}

@app.get("/api/screen/requests")
def list_requests(limit: int = 10, db: Session = Depends(get_db)):
    stmt = select(ScreenRequest).order_by(desc(ScreenRequest.created_at)).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [{"id": r.id, "name": r.name, "created_at": r.created_at.isoformat()} for r in rows]
