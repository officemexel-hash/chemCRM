from dataclasses import asdict
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.campaign import RfqCampaign
from app.db.models.message import OutboundMessage
from app.db.models.quote import Quote
from app.db.models.substance import Substance
from app.db.models.supplier import SupplierCompany, SupplierContact
from app.db.session import get_db
from app.schemas.campaign import (
    AutonomousRunRequest,
    AutonomousRunResponse,
    CampaignComparisonRow,
    CampaignCreate,
    CampaignRead,
)
from app.schemas.message import OutboundMessageRead
from app.schemas.quote import QuoteRead
from app.services.audit_log import AuditLogService
from app.services.app_settings import AppSettingsService
from app.services.campaign_orchestrator import AutonomousRunOptions, CampaignOrchestrator
from app.services.policy_engine import PolicyEngine
from app.services.rfq_generator import RFQGenerator


router = APIRouter(prefix="/campaigns", tags=["campaigns"])


class GenerateRFQRequest(BaseModel):
    supplier_id: str
    contact_id: str


@router.post("", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)) -> RfqCampaign:
    substance = db.get(Substance, payload.substance_id)
    if substance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Substance not found")
    campaign = RfqCampaign(**payload.model_dump(), status="draft")
    db.add(campaign)
    db.flush()
    AuditLogService(db).log("campaign_created", "campaign", campaign.id, payload.model_dump())
    db.commit()
    db.refresh(campaign)
    return campaign


@router.get("", response_model=list[CampaignRead])
def list_campaigns(db: Session = Depends(get_db)) -> list[RfqCampaign]:
    return list(db.scalars(select(RfqCampaign).order_by(RfqCampaign.created_at.desc())))


@router.get("/{campaign_id}", response_model=CampaignRead)
def get_campaign(campaign_id: str, db: Session = Depends(get_db)) -> RfqCampaign:
    campaign = db.get(RfqCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


@router.post("/{campaign_id}/generate-rfq", response_model=OutboundMessageRead)
def generate_rfq(
    campaign_id: str, payload: GenerateRFQRequest, db: Session = Depends(get_db)
) -> OutboundMessage:
    campaign = db.scalar(
        select(RfqCampaign)
        .options(selectinload(RfqCampaign.substance).selectinload(Substance.regulatory_flags))
        .where(RfqCampaign.id == campaign_id)
    )
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    supplier = db.scalar(
        select(SupplierCompany)
        .options(selectinload(SupplierCompany.contacts))
        .where(SupplierCompany.id == payload.supplier_id)
    )
    contact = db.get(SupplierContact, payload.contact_id)
    if supplier is None or contact is None or contact.company_id != supplier.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier/contact not found")

    draft = RFQGenerator(AppSettingsService(db).get()).generate(campaign.substance, campaign, supplier)
    message = OutboundMessage(
        campaign_id=campaign.id,
        company_id=supplier.id,
        contact_id=contact.id,
        channel=contact.channel,
        subject=draft.subject,
        body=draft.body,
        status="draft",
    )
    decision = PolicyEngine().evaluate_outbound_message(
        message, supplier, campaign.substance, contact, campaign
    )
    message.policy_decision = decision.decision.value
    message.policy_reasons = decision.reasons
    message.approval_required = decision.decision.value != "ALLOW_AUTO_SEND"
    if decision.decision.value == "BLOCK":
        message.status = "blocked"
    elif decision.decision.value == "REQUIRES_APPROVAL":
        message.status = "requires_approval"
    elif decision.decision.value == "TEST_OVERRIDE_ALLOW":
        message.status = "test_override_simulation"
        message.approval_required = False
    db.add(message)
    db.flush()
    AuditLogService(db).log(
        "outbound_message_created",
        "outbound_message",
        message.id,
        {"policy_decision": message.policy_decision, "policy_reasons": message.policy_reasons},
    )
    db.commit()
    db.refresh(message)
    return message


@router.post("/{campaign_id}/run-autonomous", response_model=AutonomousRunResponse)
def run_campaign_autonomous(
    campaign_id: str,
    payload: AutonomousRunRequest,
    db: Session = Depends(get_db),
) -> AutonomousRunResponse:
    try:
        result = CampaignOrchestrator(db).run(
            campaign_id,
            AutonomousRunOptions(
                supplier_ids=payload.supplier_ids,
                dry_run=payload.dry_run,
                allow_duplicates=payload.allow_duplicates,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    db.commit()
    return AutonomousRunResponse.model_validate(asdict(result))


@router.get("/{campaign_id}/messages", response_model=list[OutboundMessageRead])
def campaign_messages(campaign_id: str, db: Session = Depends(get_db)) -> list[OutboundMessage]:
    return list(db.scalars(select(OutboundMessage).where(OutboundMessage.campaign_id == campaign_id)))


@router.get("/{campaign_id}/quotes", response_model=list[QuoteRead])
def campaign_quotes(campaign_id: str, db: Session = Depends(get_db)) -> list[Quote]:
    return list(db.scalars(select(Quote).where(Quote.campaign_id == campaign_id)))


@router.get("/{campaign_id}/comparison", response_model=list[CampaignComparisonRow])
def campaign_comparison(campaign_id: str, db: Session = Depends(get_db)) -> list[CampaignComparisonRow]:
    rows = list(
        db.execute(
            select(Quote, SupplierCompany)
            .join(SupplierCompany, SupplierCompany.id == Quote.company_id)
            .where(Quote.campaign_id == campaign_id)
        )
    )
    numeric_prices = [Decimal(row.Quote.price) for row in rows if row.Quote.price is not None]
    best_price = min(numeric_prices) if numeric_prices else None
    comparison: list[CampaignComparisonRow] = []
    for row in rows:
        quote: Quote = row.Quote
        supplier: SupplierCompany = row.SupplierCompany
        comparison.append(
            CampaignComparisonRow(
                quote_id=quote.id,
                supplier=supplier.name,
                country=supplier.country,
                price=float(quote.price) if quote.price is not None else None,
                currency=quote.currency,
                unit=quote.unit,
                moq=quote.moq,
                incoterms=quote.incoterms,
                lead_time=quote.lead_time,
                payment_terms=quote.payment_terms,
                coa_available=quote.coa_available,
                sds_available=quote.sds_available,
                reach_status=quote.reach_status,
                adr_class=quote.adr_class,
                risk_level=supplier.risk_level,
                confidence=float(quote.confidence) if quote.confidence is not None else None,
                best_quote=best_price is not None and quote.price == best_price,
            )
        )
    return comparison
