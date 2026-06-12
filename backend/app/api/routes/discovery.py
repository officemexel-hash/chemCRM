from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.snapshot import RawSnapshot
from app.db.models.task import ManualTask
from app.db.session import get_db
from app.services.audit_log import AuditLogService
from app.utils.hashing import sha256_text
from app.utils.urls import normalize_url


router = APIRouter(prefix="/discovery", tags=["discovery"])


class DiscoveryStartRequest(BaseModel):
    substance_id: str | None = None
    campaign_id: str | None = None


class ImportUrlsRequest(BaseModel):
    urls: list[str] = Field(min_length=1)


@router.post("/start")
def start_discovery(payload: DiscoveryStartRequest, db: Session = Depends(get_db)) -> dict:
    task = ManualTask(
        task_type="discovery_review",
        title="Review legal search provider configuration",
        description="Discovery is queued as a manual/legal-provider workflow in MVP unless a configured SearchProvider is available.",
        related_object_type="campaign" if payload.campaign_id else "substance",
        related_object_id=payload.campaign_id or payload.substance_id,
    )
    db.add(task)
    db.flush()
    AuditLogService(db).log("discovery_started", "manual_task", task.id, payload.model_dump())
    db.commit()
    return {"job_id": task.id, "status": "manual_task_created"}


@router.get("/jobs/{job_id}")
def get_discovery_job(job_id: str, db: Session = Depends(get_db)) -> dict:
    task = db.get(ManualTask, job_id)
    if task:
        return {"job_id": task.id, "status": task.status, "title": task.title}
    return {"job_id": job_id, "status": "not_found"}


@router.post("/import-urls")
def import_urls(payload: ImportUrlsRequest, db: Session = Depends(get_db)) -> dict:
    snapshots: list[RawSnapshot] = []
    for url in payload.urls:
        normalized = normalize_url(url)
        snapshot = RawSnapshot(
            source_url=normalized,
            content_hash=sha256_text(normalized),
            fetched_at=datetime.now(timezone.utc),
            fetch_status="manual_import",
        )
        db.add(snapshot)
        snapshots.append(snapshot)
    db.flush()
    AuditLogService(db).log(
        "discovery_urls_imported",
        "raw_snapshot",
        None,
        {"count": len(snapshots), "urls": [snapshot.source_url for snapshot in snapshots]},
    )
    db.commit()
    return {"imported": len(snapshots), "snapshot_ids": [snapshot.id for snapshot in snapshots]}


@router.get("/results")
def discovery_results(db: Session = Depends(get_db)) -> list[dict]:
    snapshots = list(db.scalars(select(RawSnapshot).order_by(RawSnapshot.fetched_at.desc()).limit(100)))
    return [
        {
            "snapshot_id": item.id,
            "source_url": item.source_url,
            "fetch_status": item.fetch_status,
            "fetched_at": item.fetched_at,
        }
        for item in snapshots
    ]
