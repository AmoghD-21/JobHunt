# app/routers/jobs.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from aggregator import sync_all_sources

router = APIRouter(prefix="/jobs", tags=["Jobs Dashboard"])

@router.post("/sync")
async def trigger_job_sync(
    q: str | None = Query(None, description="Keyword filter for syncing entries"), 
    db: Session = Depends(get_db)
):
    added = await sync_all_sources(db, keyword=q)
    return {"message": "Synchronization operation completed.", "new_records_added": added}

@router.get("")
def list_jobs(
    q: str | None = Query(None, description="Search filter for title or company"), 
    db: Session = Depends(get_db)
):
    query = db.query(models.Job)
    if q:
        query = query.filter(
            (models.Job.title.ilike(f"%{q}%")) | (models.Job.company.ilike(f"%{q}%"))
        )
    return query.order_by(models.Job.id.desc()).all()