from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.report import RankingRow, ReportGenerateRequest
from app.services.report_generator import ReportGeneratorService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/comparison")
def generate_comparison_report(payload: ReportGenerateRequest, db: Session = Depends(get_db)) -> dict:
    """Generate a comparison report (PDF or Excel) for all quotes in a campaign."""
    service = ReportGeneratorService(db)
    try:
        if payload.format == "xlsx":
            doc = service.generate_comparison_excel(payload.campaign_id)
        else:
            doc = service.generate_comparison_pdf(payload.campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {
        "id": doc.id,
        "doc_type": doc.doc_type,
        "file_path": doc.file_path,
        "file_size_bytes": doc.file_size_bytes,
        "format": payload.format,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.get("/ranking/{campaign_id}", response_model=list[RankingRow])
def get_ranking(campaign_id: str, db: Session = Depends(get_db)) -> list[dict]:
    """Get supplier ranking for a campaign's quotes."""
    service = ReportGeneratorService(db)
    try:
        return service.generate_supplier_ranking(campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
