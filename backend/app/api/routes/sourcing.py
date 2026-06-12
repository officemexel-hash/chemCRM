from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.sourcing import (
    SourcingBatchImportRequest,
    SourcingBatchRead,
    SourcingBatchReportRead,
)
from app.services.sourcing_batch import SourcingBatchService


router = APIRouter(prefix="/sourcing", tags=["sourcing"])


@router.post("/batches", response_model=SourcingBatchRead, status_code=status.HTTP_201_CREATED)
def create_sourcing_batch(
    payload: SourcingBatchImportRequest,
    db: Session = Depends(get_db),
) -> SourcingBatchRead:
    batch = SourcingBatchService(db).create_batch(payload)
    db.commit()
    return batch


@router.get("/batches/{batch_id}", response_model=SourcingBatchRead)
def get_sourcing_batch(batch_id: str, db: Session = Depends(get_db)) -> SourcingBatchRead:
    batch = SourcingBatchService(db).get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sourcing batch not found")
    return batch


@router.get("/batches/{batch_id}/report", response_model=SourcingBatchReportRead)
def get_sourcing_report(batch_id: str, db: Session = Depends(get_db)) -> SourcingBatchReportRead:
    report = SourcingBatchService(db).get_report(batch_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sourcing batch not found")
    return report
