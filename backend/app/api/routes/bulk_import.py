import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.bulk_import import BulkImportItem, BulkImportJob
from app.db.session import get_db
from app.schemas.bulk_import import BulkImportItemRead, BulkImportJobRead
from app.services.audit_log import AuditLogService
from app.services.bulk_import import BulkImportService

router = APIRouter(prefix="/bulk-import", tags=["bulk-import"])


@router.post("/upload", response_model=BulkImportJobRead, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile, db: Session = Depends(get_db)) -> BulkImportJob:
    """Accept .csv or .xlsx file with CAS numbers."""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("csv", "xlsx", "xls"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .csv and .xlsx files are accepted")

    settings = get_settings()
    os.makedirs(settings.storage_path, exist_ok=True)

    content = await file.read()
    service = BulkImportService(db)
    job = service.create_job(file.filename, file.filename)

    # Save file
    filepath = os.path.join(settings.storage_path, f"import_{job.id}.{ext}")
    with open(filepath, "wb") as f:
        f.write(content)
    job.filename = filepath
    db.commit()
    db.refresh(job)

    # Parse
    try:
        if ext == "csv":
            items = service.parse_csv(content, job.id)
        else:
            items = service.parse_excel(content, job.id)
    except Exception as e:
        job.status = "failed"
        job.error_details = {"parse_error": str(e)}
        db.commit()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Parse error: {e}")

    for item in items:
        db.add(item)
    db.flush()
    job.total_rows = len(items)
    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/process", response_model=BulkImportJobRead)
def process_job(job_id: str, db: Session = Depends(get_db)) -> BulkImportJob:
    """Validate CAS numbers and create Substance records."""
    service = BulkImportService(db)
    try:
        job = service.validate_and_create(job_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return job


@router.post("/{job_id}/enrich")
def enrich_substances(job_id: str, db: Session = Depends(get_db)) -> dict:
    """Enrich all newly created substances from a bulk import job."""
    service = BulkImportService(db)
    return service.enrich_substances(job_id)


@router.get("/{job_id}", response_model=BulkImportJobRead)
def get_job(job_id: str, db: Session = Depends(get_db)) -> BulkImportJob:
    job = db.get(BulkImportJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.get("/{job_id}/items", response_model=list[BulkImportItemRead])
def get_job_items(job_id: str, db: Session = Depends(get_db)) -> list[BulkImportItem]:
    return list(db.scalars(select(BulkImportItem).where(BulkImportItem.job_id == job_id).order_by(BulkImportItem.row_number)))
