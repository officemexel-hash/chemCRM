from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.substance import RegulatoryFlag, Substance, SubstanceSynonym
from app.db.session import get_db
from app.schemas.substance import RegulatoryFlagRead, SubstanceCreate, SubstanceRead
from app.schemas.substance_intelligence import (
    ManufacturingAnalysisRequest,
    SubstanceManufacturingAnalysisRead,
    SubstanceSourcingProfileRead,
)
from app.services.audit_log import AuditLogService
from app.services.cas_validator import validate_cas_or_raise
from app.services.regulatory_screening import RegulatoryScreeningService
from app.services.substance_enrichment import SubstanceEnrichmentService, decimal_or_none
from app.services.substance_intelligence import SubstanceIntelligenceService


router = APIRouter(prefix="/substances", tags=["substances"])


@router.post("", response_model=SubstanceRead, status_code=status.HTTP_201_CREATED)
def create_substance(payload: SubstanceCreate, db: Session = Depends(get_db)) -> Substance:
    cas = validate_cas_or_raise(payload.cas)
    existing = db.scalar(
        select(Substance)
        .options(selectinload(Substance.synonyms), selectinload(Substance.regulatory_flags))
        .where(Substance.cas == cas)
    )
    if existing:
        return existing
    substance = Substance(
        cas=cas,
        primary_name=payload.primary_name,
        regulatory_status="unknown" if not payload.primary_name else "unreviewed",
        requires_manual_review=not bool(payload.primary_name),
    )
    db.add(substance)
    db.flush()
    AuditLogService(db).log("substance_created", "substance", substance.id, {"cas": cas})
    db.commit()
    return _load_substance(db, substance.id)


@router.get("", response_model=list[SubstanceRead])
def list_substances(db: Session = Depends(get_db)) -> list[Substance]:
    return list(
        db.scalars(
            select(Substance)
            .options(selectinload(Substance.synonyms), selectinload(Substance.regulatory_flags))
            .order_by(Substance.created_at.desc())
        )
    )


@router.get("/{substance_id}", response_model=SubstanceRead)
def get_substance(substance_id: str, db: Session = Depends(get_db)) -> Substance:
    return _load_substance(db, substance_id)


@router.post("/{substance_id}/enrich", response_model=SubstanceRead)
def enrich_substance(substance_id: str, db: Session = Depends(get_db)) -> Substance:
    substance = _load_substance(db, substance_id)
    result = SubstanceEnrichmentService().enrich_by_cas(substance.cas)
    substance.primary_name = result.primary_name
    substance.iupac_name = result.iupac_name
    substance.molecular_formula = result.molecular_formula
    substance.molecular_weight = decimal_or_none(result.molecular_weight)
    substance.pubchem_cid = result.pubchem_cid
    substance.ec_number = result.ec_number
    substance.requires_manual_review = result.requires_manual_review

    substance.synonyms.clear()
    for synonym in result.synonyms[:30]:
        substance.synonyms.append(SubstanceSynonym(synonym=synonym, source="enrichment"))

    screening = RegulatoryScreeningService().screen(
        cas=substance.cas,
        primary_name=result.primary_name,
        synonyms=result.synonyms,
        known_status="unreviewed" if result.primary_name else "unknown",
    )
    substance.regulatory_status = screening.regulatory_status
    substance.requires_manual_review = substance.requires_manual_review or screening.requires_manual_review
    substance.regulatory_flags.clear()
    for flag in screening.flags:
        substance.regulatory_flags.append(RegulatoryFlag(**flag))

    AuditLogService(db).log(
        "substance_enriched",
        "substance",
        substance.id,
        {
            "cas": substance.cas,
            "sources": result.data_sources,
            "confidence": result.confidence,
            "warnings": result.warnings,
        },
    )
    db.commit()
    return _load_substance(db, substance.id)


@router.get("/{substance_id}/regulatory-flags", response_model=list[RegulatoryFlagRead])
def get_regulatory_flags(substance_id: str, db: Session = Depends(get_db)) -> list[RegulatoryFlag]:
    _load_substance(db, substance_id)
    return list(db.scalars(select(RegulatoryFlag).where(RegulatoryFlag.substance_id == substance_id)))


@router.get("/{substance_id}/intelligence", response_model=SubstanceSourcingProfileRead)
def get_substance_intelligence(
    substance_id: str, db: Session = Depends(get_db)
) -> SubstanceSourcingProfileRead:
    try:
        return SubstanceIntelligenceService(db).sourcing_profile(substance_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{substance_id}/manufacturing-analysis", response_model=SubstanceManufacturingAnalysisRead)
def create_manufacturing_analysis(
    substance_id: str,
    payload: ManufacturingAnalysisRequest,
    db: Session = Depends(get_db),
) -> SubstanceManufacturingAnalysisRead:
    try:
        return SubstanceIntelligenceService(db).analyze_manufacturing(substance_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{substance_id}/manufacturing-analyses", response_model=list[SubstanceManufacturingAnalysisRead])
def list_manufacturing_analyses(
    substance_id: str, db: Session = Depends(get_db)
) -> list[SubstanceManufacturingAnalysisRead]:
    try:
        return SubstanceIntelligenceService(db).list_manufacturing_analyses(substance_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _load_substance(db: Session, substance_id: str) -> Substance:
    substance = db.scalar(
        select(Substance)
        .options(selectinload(Substance.synonyms), selectinload(Substance.regulatory_flags))
        .where(Substance.id == substance_id)
    )
    if substance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Substance not found")
    return substance
