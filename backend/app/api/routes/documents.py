from fastapi import APIRouter, Depends, Query, UploadFile, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.document import GeneratedDocument, DocumentTemplate
from app.db.session import get_db
from app.schemas.documents import (
    CompanyLetterheadData,
    CustomsDutyRequest,
    CustomsDutyResponse,
    IncotermsGuideResponse,
    LetterOfIntentRequest,
    LetterOfIntentResponse,
    LetterheadRequest,
    LetterheadResponse,
    PurchaseOrderRequest,
    PurchaseOrderResponse,
    SubstanceAnalogsRequest,
    SubstanceAnalogsResponse,
)
from app.services.app_settings import AppSettingsService
from app.services.audit_log import AuditLogService
from app.services.customs_service import CustomsService
from app.services.document_generator import DocumentGenerator
from app.services.substance_analogs import SubstanceAnalogsService


router = APIRouter(prefix="/documents", tags=["documents"])

_generator = DocumentGenerator()
_customs = CustomsService()
_analogs = SubstanceAnalogsService()


@router.post("/letterhead", response_model=LetterheadResponse)
def generate_letterhead(payload: LetterheadRequest, db: Session = Depends(get_db)) -> LetterheadResponse:
    payload = payload.model_copy(update={"company": payload.company or _settings_company(db)})
    return _generator.generate_letterhead(payload)


@router.post("/letter-of-intent", response_model=LetterOfIntentResponse)
def generate_loi(payload: LetterOfIntentRequest, db: Session = Depends(get_db)) -> LetterOfIntentResponse:
    payload = payload.model_copy(update={"company": payload.company or _settings_company(db)})
    response = _generator.generate_loi(payload)
    if payload.save_to_crm:
        document = _save_generated_document(
            db,
            doc_type="loi",
            response=response.model_dump(mode="json"),
            request=payload.model_dump(mode="json"),
            campaign_id=payload.campaign_id,
            company_id=payload.company_id,
            substance_id=payload.substance_id,
        )
        response = response.model_copy(update={"generated_document_id": document.id})
        db.commit()
    return response


@router.post("/purchase-order", response_model=PurchaseOrderResponse)
def generate_po(payload: PurchaseOrderRequest, db: Session = Depends(get_db)) -> PurchaseOrderResponse:
    payload = payload.model_copy(update={"company": payload.company or _settings_company(db)})
    response = _generator.generate_po(payload)
    if payload.save_to_crm:
        document = _save_generated_document(
            db,
            doc_type="po",
            response=response.model_dump(mode="json"),
            request=payload.model_dump(mode="json"),
            campaign_id=payload.campaign_id,
            quote_id=payload.quote_id,
            company_id=payload.company_id,
            substance_id=payload.substance_id,
        )
        response = response.model_copy(update={"generated_document_id": document.id})
        db.commit()
    return response


@router.get("/incoterms-guide", response_model=IncotermsGuideResponse)
def incoterms_guide(
    transport_mode: str = Query("road", description="Transport mode: sea, air, road, rail, courier, multimodal"),
) -> IncotermsGuideResponse:
    return _generator.incoterms_guide(transport_mode)


@router.post("/customs-duty", response_model=CustomsDutyResponse)
def lookup_customs(payload: CustomsDutyRequest) -> CustomsDutyResponse:
    return _customs.lookup(payload)


@router.post("/substance-analogs", response_model=SubstanceAnalogsResponse)
def find_analogs(payload: SubstanceAnalogsRequest) -> SubstanceAnalogsResponse:
    return _analogs.find_analogs(payload)


@router.get("")
def list_documents(
    doc_type: str | None = None,
    campaign_id: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    """List all generated documents with optional filters."""
    statement = select(GeneratedDocument).order_by(GeneratedDocument.created_at.desc())
    if doc_type:
        statement = statement.where(GeneratedDocument.doc_type == doc_type)
    if campaign_id:
        statement = statement.where(GeneratedDocument.campaign_id == campaign_id)
    documents = list(db.scalars(statement.limit(100)))
    return [
        {
            "id": doc.id,
            "doc_type": doc.doc_type,
            "campaign_id": doc.campaign_id,
            "quote_id": doc.quote_id,
            "company_id": doc.company_id,
            "substance_id": doc.substance_id,
            "file_path": doc.file_path,
            "file_size_bytes": doc.file_size_bytes,
            "parameters": doc.parameters,
            "status": doc.status,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        }
        for doc in documents
    ]


@router.get("/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db)) -> dict:
    """Get a single generated document metadata."""
    doc = db.get(GeneratedDocument, document_id)
    if doc is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": doc.id,
        "doc_type": doc.doc_type,
        "campaign_id": doc.campaign_id,
        "quote_id": doc.quote_id,
        "company_id": doc.company_id,
        "substance_id": doc.substance_id,
        "file_path": doc.file_path,
        "file_size_bytes": doc.file_size_bytes,
        "parameters": doc.parameters,
        "status": doc.status,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.get("/templates")
def list_templates(doc_type: str | None = Query(None), db: Session = Depends(get_db)):
    stmt = select(DocumentTemplate).order_by(DocumentTemplate.name)
    if doc_type:
        stmt = stmt.where(DocumentTemplate.doc_type == doc_type)
    templates = list(db.scalars(stmt))
    return [{"id": t.id, "doc_type": t.doc_type, "name": t.name, "is_default": t.is_default} for t in templates]


@router.get("/{document_id}/download")
def download_document(document_id: str, db: Session = Depends(get_db)):
    """Download the generated document file (PDF or HTML)."""
    doc = db.get(GeneratedDocument, document_id)
    if doc is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Document not found")

    # If there's a saved file, serve it
    if doc.file_path:
        import os
        if os.path.exists(doc.file_path):
            media_type = "application/pdf" if doc.file_path.endswith(".pdf") else "text/html"
            filename = os.path.basename(doc.file_path)
            return FileResponse(doc.file_path, media_type=media_type, filename=filename)

    # Otherwise, generate PDF from stored HTML parameters
    html_content = None
    if doc.parameters and isinstance(doc.parameters, dict):
        response_data = doc.parameters.get("response", {})
        html_content = response_data.get("html")

    if html_content:
        # Try to generate PDF
        try:
            from weasyprint import HTML
            import tempfile, os
            from app.core.config import get_settings
            settings = get_settings()
            os.makedirs(settings.storage_path, exist_ok=True)
            pdf_path = os.path.join(settings.storage_path, f"{doc.doc_type}_{doc.id[:8]}.pdf")
            HTML(string=html_content).write_pdf(pdf_path)
            doc.file_path = pdf_path
            doc.file_size_bytes = os.path.getsize(pdf_path)
            db.commit()
            return FileResponse(pdf_path, media_type="application/pdf", filename=os.path.basename(pdf_path))
        except ImportError:
            # weasyprint not available, return HTML
            return HTMLResponse(content=html_content)
        except Exception:
            return HTMLResponse(content=html_content)

    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Document file not available")


@router.get("/letterhead/preview")
def preview_letterhead(db: Session = Depends(get_db)):
    """Preview the company letterhead."""
    company = _settings_company(db)
    response = _generator.generate_letterhead(LetterheadRequest(company=company, title="Letterhead Preview"))
    return HTMLResponse(content=response.html)


# ── Rebrand MSDS/COA endpoints ──

@router.post("/rebrand")
async def rebrand_document(
    file: UploadFile,
    doc_type: str = Query("msds", description="Document type: msds or coa"),
    substance_name: str = Query("", description="Substance name for header"),
    cas: str = Query("", description="CAS number for header"),
    db: Session = Depends(get_db),
) -> dict:
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "Supplier COA/SDS rebranding is disabled. Store original supplier documents as "
            "evidence and generate only your own LOI/PO/RFQ documents."
        ),
    )


@router.post("/rebrand-text")
def rebrand_document_from_text(
    payload: dict,
    db: Session = Depends(get_db),
) -> dict:
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "Supplier COA/SDS rebranding is disabled. Store original supplier documents as "
            "evidence and generate only your own LOI/PO/RFQ documents."
        ),
    )


def _settings_company(db: Session) -> CompanyLetterheadData:
    settings = AppSettingsService(db).get()
    return CompanyLetterheadData(
        legal_name=settings.company.legal_name,
        trading_name=settings.company.trading_name,
        registration_number=settings.company.registration_number,
        vat_number=settings.company.vat_number,
        eori_number=settings.company.eori_number,
        website=settings.company.website,
        address=settings.company.address,
        country=settings.company.country,
        email=str(settings.sender.email) if settings.sender.email else None,
        phone=settings.sender.phone,
    )


def _save_generated_document(
    db: Session,
    doc_type: str,
    response: dict,
    request: dict,
    campaign_id: str | None = None,
    quote_id: str | None = None,
    company_id: str | None = None,
    substance_id: str | None = None,
) -> GeneratedDocument:
    document = GeneratedDocument(
        doc_type=doc_type,
        campaign_id=campaign_id,
        quote_id=quote_id,
        company_id=company_id,
        substance_id=substance_id,
        parameters={
            "request": request,
            "response": response,
            "storage": "database_parameters",
        },
        status="generated",
    )
    db.add(document)
    db.flush()
    AuditLogService(db).log(
        "document_generated",
        "generated_document",
        document.id,
        {"doc_type": doc_type, "campaign_id": campaign_id, "quote_id": quote_id},
    )
    return document
