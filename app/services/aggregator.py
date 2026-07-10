# app/services/aggregator.py
import httpx
from typing import List
# from app.services.base_source import BaseJobSource, AggregatedJobSchema
from .base_source import AggregatedJobSchema,BaseJobSource

from app.services import Base

from app import models
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

class RemotiveSource(BaseJobSource):
    @property
    def platform_name(self) -> str:
        return "Remotive"

    async def fetch_jobs(self, keyword: str | None = None) -> List[AggregatedJobSchema]:
        url = "https://remotive.com/api/remote-jobs"
        params = {}
        if keyword:
            params["search"] = keyword

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            except (httpx.HTTPError, ValueError) as e:
                # In production, hook this up to a logger
                print(f"Failed to fetch from Remotive: {str(e)}")
                return []

        jobs = data.get("jobs", [])
        aggregated_jobs = []
        
        for item in jobs:
            # Enforce data translation boundary
            aggregated_jobs.append(
                AggregatedJobSchema(
                    title=item.get("title", "Unknown Title"),
                    company=item.get("company_name", "Unknown Company"),
                    location=item.get("candidate_required_location", "Remote"),
                    description=item.get("description", ""),
                    source_url=item.get("url"),
                    source_platform=self.platform_name
                )
            )
        return aggregated_jobs

# Core orchestration logic to process ingestion streams into the database
async def sync_all_sources(db: Session, keyword: str | None = None) -> int:
    """Orchestrates ingestion across registered strategies and implements idempotency handling."""
    # Registering providers cleanly
    sources: List[BaseJobSource] = [RemotiveSource()]
    new_jobs_count = 0

    for source in sources:
        fetched_jobs = await source.fetch_jobs(keyword=keyword)
        for job_data in fetched_jobs:
            # Idempotency / Deduplication check at application layer before hitting unique DB constraints
            exists = db.query(models.Job).filter(models.Job.source_url == job_data.source_url).first()
            if exists:
                continue
            
            db_job = models.Job(
                title=job_data.title,
                company=job_data.company,
                location=job_data.location,
                description=job_data.description,
                source_url=job_data.source_url,
                source_platform=job_data.source_platform
            )
            db.add(db_job)
            try:
                db.commit()
                new_jobs_count += 1
            except IntegrityError:
                db.rollback()  # Resilient fallback if a concurrent thread wrote it first
                
    return new_jobs_count