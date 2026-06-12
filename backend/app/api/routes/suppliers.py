from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.quote import Quote
from app.db.models.supplier import SupplierCompany, SupplierContact
from app.db.session import get_db
from app.schemas.quote import QuoteRead
from app.schemas.supplier import (
    SupplierClassificationRead,
    SupplierContactCreate,
    SupplierContactRead,
    SupplierCreate,
    SupplierRead,
    SupplierUpdate,
)
from app.services.audit_log import AuditLogService
from app.services.supplier_classifier import SupplierClassifier


router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierRead])
def list_suppliers(db: Session = Depends(get_db)) -> list[SupplierCompany]:
    return list(
        db.scalars(
            select(SupplierCompany)
            .options(selectinload(SupplierCompany.contacts))
            .order_by(SupplierCompany.created_at.desc())
        )
    )


@router.post("", response_model=SupplierRead, status_code=status.HTTP_201_CREATED)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db)) -> SupplierCompany:
    supplier = SupplierCompany(
        name=payload.name,
        website=payload.website,
        country=payload.country,
        address=payload.address,
        company_type=payload.company_type,
        registration_number=payload.registration_number,
        vat_number=payload.vat_number,
        eori_number=payload.eori_number,
        verified_status=payload.verified_status,
        notes=payload.notes,
    )
    for contact_payload in payload.contacts:
        _ensure_contact_evidence(contact_payload)
        supplier.contacts.append(SupplierContact(**contact_payload.model_dump()))
    db.add(supplier)
    db.flush()
    AuditLogService(db).log("supplier_created", "supplier", supplier.id, {"name": supplier.name})
    db.commit()
    return _load_supplier(db, supplier.id)


@router.get("/{supplier_id}", response_model=SupplierRead)
def get_supplier(supplier_id: str, db: Session = Depends(get_db)) -> SupplierCompany:
    return _load_supplier(db, supplier_id)


@router.patch("/{supplier_id}", response_model=SupplierRead)
def patch_supplier(
    supplier_id: str, payload: SupplierUpdate, db: Session = Depends(get_db)
) -> SupplierCompany:
    supplier = _load_supplier(db, supplier_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)
    AuditLogService(db).log(
        "supplier_updated",
        "supplier",
        supplier.id,
        payload.model_dump(exclude_unset=True, mode="json"),
    )
    db.commit()
    return _load_supplier(db, supplier.id)


@router.get("/{supplier_id}/contacts", response_model=list[SupplierContactRead])
def list_contacts(supplier_id: str, db: Session = Depends(get_db)) -> list[SupplierContact]:
    _load_supplier(db, supplier_id)
    return list(db.scalars(select(SupplierContact).where(SupplierContact.company_id == supplier_id)))


@router.post("/{supplier_id}/contacts", response_model=SupplierContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(
    supplier_id: str, payload: SupplierContactCreate, db: Session = Depends(get_db)
) -> SupplierContact:
    _load_supplier(db, supplier_id)
    _ensure_contact_evidence(payload)
    contact = SupplierContact(company_id=supplier_id, **payload.model_dump())
    db.add(contact)
    db.flush()
    AuditLogService(db).log("supplier_contact_created", "supplier_contact", contact.id, payload.model_dump())
    db.commit()
    db.refresh(contact)
    return contact


@router.get("/{supplier_id}/quotes", response_model=list[QuoteRead])
def supplier_quotes(supplier_id: str, db: Session = Depends(get_db)) -> list[Quote]:
    _load_supplier(db, supplier_id)
    return list(db.scalars(select(Quote).where(Quote.company_id == supplier_id)))


@router.post("/{supplier_id}/classify", response_model=SupplierClassificationRead)
def classify_supplier(supplier_id: str, db: Session = Depends(get_db)) -> SupplierClassificationRead:
    supplier = _load_supplier(db, supplier_id)
    classification = SupplierClassifier().classify(supplier)
    supplier.company_type = classification.company_type
    supplier.supplier_score = classification.supplier_score
    supplier.risk_score = classification.risk_score
    supplier.risk_level = classification.risk_level
    AuditLogService(db).log(
        "supplier_classified",
        "supplier",
        supplier.id,
        {
            "company_type": classification.company_type,
            "supplier_score": classification.supplier_score,
            "risk_score": classification.risk_score,
            "risk_flags": classification.risk_flags,
        },
    )
    db.commit()
    return SupplierClassificationRead(**classification.__dict__)


def _load_supplier(db: Session, supplier_id: str) -> SupplierCompany:
    supplier = db.scalar(
        select(SupplierCompany)
        .options(selectinload(SupplierCompany.contacts))
        .where(SupplierCompany.id == supplier_id)
    )
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return supplier


def _ensure_contact_evidence(payload: SupplierContactCreate) -> None:
    if not payload.source_url or not payload.evidence_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Every supplier contact requires source_url and evidence_text",
        )
