"""Substance Research API — per-substance research dossier with supplier
interactions, production analysis, and Incoterms comparison."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.research import (
    IncotermsComparisonResponse,
    ProductionAnalysisCreate,
    ProductionMethodRead,
    ResearchDossierResponse,
    SupplierInteractionCreate,
    SupplierInteractionRead,
)
from app.services.research_service import ResearchService

router = APIRouter(prefix="/research", tags=["research"])


@router.get("/substance/{substance_id}", response_model=ResearchDossierResponse)
def get_research_dossier(substance_id: str, db: Session = Depends(get_db)) -> ResearchDossierResponse:
    """Get the full research dossier for a substance: all supplier interactions,
    production analyses, pricing data, and Incoterms comparison guide."""
    try:
        return ResearchService(db).get_dossier(substance_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/substance/{substance_id}/interactions", response_model=SupplierInteractionRead, status_code=status.HTTP_201_CREATED)
def log_supplier_interaction(
    substance_id: str,
    payload: SupplierInteractionCreate,
    db: Session = Depends(get_db),
) -> SupplierInteractionRead:
    """Log a new supplier contact/interaction for this substance.

    Records who was contacted, through which channel, what terms they offered,
    which Incoterms, packaging, transport modes, and the outcome status.
    """
    try:
        result = ResearchService(db).add_interaction(substance_id, payload)
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/substance/{substance_id}/analyze-production", response_model=list[ProductionMethodRead])
def analyze_production(
    substance_id: str,
    payload: ProductionAnalysisCreate | None = None,
    db: Session = Depends(get_db),
) -> list[ProductionMethodRead]:
    """Run production analysis for a substance.

    Returns known synthesis routes with:
    - Equipment needed (with cost estimates)
    - Sub-products/precursors (with auto-found suppliers)
    - Raw material costs, labor, utilities
    - Total estimated production cost per kg
    - Safety notes and permits needed

    If no pre-configured methods exist for this CAS, returns a generic template.
    """
    try:
        result = ResearchService(db).analyze_production(substance_id, payload)
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/substance/{substance_id}/incoterms-comparison", response_model=IncotermsComparisonResponse)
def compare_incoterms(substance_id: str, db: Session = Depends(get_db)) -> IncotermsComparisonResponse:
    """Compare all Incoterms across transport modes for this substance.

    Shows you which terms are available for sea/air/road/rail/multimodal,
    and who is responsible (seller vs buyer) for each cost component.
    """
    try:
        return ResearchService(db).compare_incoterms(substance_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
