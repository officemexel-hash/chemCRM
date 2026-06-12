from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.tariff import (
    HsCodeRead,
    LegalUseRead,
    ResponsibilityMatrixRow,
    TariffRateRead,
)
from app.services.hs_code_service import HsCodeService, TariffService
from app.services.legal_use_service import LegalUseService

router = APIRouter(prefix="/tariff", tags=["tariff"])


@router.get("/hs-code/lookup", response_model=list[HsCodeRead])
def lookup_hs_code(cas: str | None = None, substance_id: str | None = None, db: Session = Depends(get_db)) -> list:
    service = HsCodeService(db)
    if cas:
        return service.lookup_by_cas(cas)
    if substance_id:
        return service.suggest_for_substance(substance_id)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide cas or substance_id")


@router.post("/hs-code/auto-assign/{substance_id}", response_model=HsCodeRead | None)
def auto_assign_hs_code(substance_id: str, db: Session = Depends(get_db)):
    service = HsCodeService(db)
    result = service.auto_assign(substance_id)
    if result is None:
        return None
    return result


@router.get("/duty-rate", response_model=TariffRateRead | None)
def get_duty_rate(hs_code: str, origin: str, destination: str, db: Session = Depends(get_db)):
    service = TariffService(db)
    return service.get_rate(hs_code, origin, destination)


@router.get("/incoterms/{incoterms}/responsibility-matrix", response_model=list[ResponsibilityMatrixRow])
def incoterms_responsibility_matrix(incoterms: str) -> list[ResponsibilityMatrixRow]:
    matrix = TariffService.get_responsibility_matrix(incoterms)
    if not matrix:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown Incoterms: {incoterms}")
    return [
        ResponsibilityMatrixRow(cost_type=cost_type, responsible_party=party)
        for cost_type, party in matrix.items()
    ]


@router.get("/incoterms-for-transport/{transport_type}")
def incoterms_for_transport(transport_type: str, db: Session = Depends(get_db)) -> dict:
    service = HsCodeService(db)
    return {"transport_type": transport_type, "recommended_incoterms": service.get_incoterms_for_transport(transport_type)}


@router.get("/legal-use/{substance_id}", response_model=list[LegalUseRead])
def legal_use_suggestions(substance_id: str, destination: str | None = None, db: Session = Depends(get_db)) -> list:
    service = LegalUseService(db)
    return service.suggest_legal_uses(substance_id, destination)


@router.get("/legal-use/{substance_id}/customs-text")
def customs_declaration_text(substance_id: str, hs_code: str, destination: str, db: Session = Depends(get_db)) -> dict:
    service = LegalUseService(db)
    text = service.generate_customs_declaration_text(substance_id, hs_code, destination)
    return {"substance_id": substance_id, "hs_code": hs_code, "destination": destination, "declaration_text": text}
