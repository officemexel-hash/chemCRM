from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.campaign import RfqCampaign
from app.db.models.message import InboundMessage, OutboundMessage
from app.db.models.quote import Quote
from app.db.models.substance import Substance
from app.db.models.supplier import SupplierCompany, SupplierContact
from app.db.session import get_db
from app.schemas.message import (
    BatchApproveRequest,
    BatchApproveResponse,
    BatchApproveResultItem,
    InboundMessageCreate,
    InboundMessageRead,
    OutboundMessageRead,
)
from app.services.audit_log import AuditLogService
from app.services.policy_engine import PolicyEngine
from app.services.quote_extractor import QuoteExtractor
from app.services.safety_override import SafetyOverrideService


router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/outbound", response_model=list[OutboundMessageRead])
def outbound_messages(db: Session = Depends(get_db)) -> list[OutboundMessage]:
    return list(db.scalars(select(OutboundMessage).order_by(OutboundMessage.created_at.desc())))


@router.get("/inbound", response_model=list[InboundMessageRead])
def inbound_messages(db: Session = Depends(get_db)) -> list[InboundMessage]:
    return list(db.scalars(select(InboundMessage).order_by(InboundMessage.received_at.desc())))


@router.post("/inbound", response_model=InboundMessageRead, status_code=status.HTTP_201_CREATED)
def create_inbound_message(
    payload: InboundMessageCreate, db: Session = Depends(get_db)
) -> InboundMessage:
    message = InboundMessage(
        **payload.model_dump(),
        received_at=datetime.now(timezone.utc),
        parsed=False,
    )
    db.add(message)
    db.flush()
    AuditLogService(db).log("inbound_message_received", "inbound_message", message.id, payload.model_dump())
    db.commit()
    db.refresh(message)
    return message


@router.post("/outbound/{message_id}/approve", response_model=OutboundMessageRead)
def approve_outbound(message_id: str, db: Session = Depends(get_db)) -> OutboundMessage:
    message = _load_outbound(db, message_id)
    if message.status == "blocked":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Blocked message cannot be approved")
    message.status = "approved"
    message.approved_at = datetime.now(timezone.utc)
    message.approval_required = False
    AuditLogService(db).log("outbound_message_approved", "outbound_message", message.id)
    db.commit()
    db.refresh(message)
    return message


@router.post("/outbound/{message_id}/send", response_model=OutboundMessageRead)
def send_outbound(message_id: str, db: Session = Depends(get_db)) -> OutboundMessage:
    message = _load_outbound(db, message_id)
    context = _message_context(db, message)
    decision = PolicyEngine(SafetyOverrideService(db).get()).evaluate_outbound_message(message, *context)
    message.policy_decision = decision.decision.value
    message.policy_reasons = decision.reasons
    if decision.decision.value == "BLOCK":
        message.status = "blocked"
        db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Policy engine blocked message")
    if decision.decision.value == "TEST_OVERRIDE_ALLOW":
        message.status = "test_override_simulated_send"
        message.external_message_id = None
        AuditLogService(db).log(
            "outbound_message_test_override_simulated",
            "outbound_message",
            message.id,
            {"policy_decision": message.policy_decision, "policy_reasons": message.policy_reasons},
        )
        db.commit()
        db.refresh(message)
        return message
    if message.status != "approved" and decision.decision.value != "ALLOW_AUTO_SEND":
        message.status = "requires_approval"
        db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Message requires approval")
    message.status = "sent"
    message.sent_at = datetime.now(timezone.utc)
    message.external_message_id = f"mock-{message.id}"
    AuditLogService(db).log(
        "outbound_message_sent",
        "outbound_message",
        message.id,
        {"provider": "mock", "policy_decision": message.policy_decision},
    )
    db.commit()
    db.refresh(message)
    return message


@router.post("/outbound/{message_id}/block", response_model=OutboundMessageRead)
def block_outbound(message_id: str, db: Session = Depends(get_db)) -> OutboundMessage:
    message = _load_outbound(db, message_id)
    message.status = "blocked"
    message.policy_decision = message.policy_decision or "BLOCK"
    AuditLogService(db).log("outbound_message_blocked", "outbound_message", message.id)
    db.commit()
    db.refresh(message)
    return message


@router.post("/outbound/batch-approve", response_model=BatchApproveResponse)
def batch_approve(payload: BatchApproveRequest, db: Session = Depends(get_db)) -> BatchApproveResponse:
    """Approve all requires_approval messages for a campaign in one action."""
    statement = select(OutboundMessage).where(
        OutboundMessage.campaign_id == payload.campaign_id,
        OutboundMessage.status.in_(["requires_approval", "draft"]),
    )
    if payload.message_ids:
        statement = statement.where(OutboundMessage.id.in_(payload.message_ids))

    messages = list(db.scalars(statement))
    approved = skipped = blocked = 0
    results: list[BatchApproveResultItem] = []

    for message in messages:
        context = _message_context(db, message)
        decision = PolicyEngine(SafetyOverrideService(db).get()).evaluate_outbound_message(message, *context)
        message.policy_decision = decision.decision.value
        message.policy_reasons = decision.reasons

        if decision.decision.value in ("BLOCK",) and message.status == "blocked":
            blocked += 1
            results.append(BatchApproveResultItem(message_id=message.id, status="blocked"))
            continue

        message.status = "approved"
        message.approved_at = datetime.now(timezone.utc)
        message.approval_required = False
        approved += 1
        results.append(BatchApproveResultItem(message_id=message.id, status="approved"))
        AuditLogService(db).log("outbound_message_batch_approved", "outbound_message", message.id)

    db.commit()
    return BatchApproveResponse(approved=approved, skipped=skipped, blocked=blocked, results=results)


@router.post("/inbound/{message_id}/parse")
def parse_inbound(message_id: str, db: Session = Depends(get_db)) -> dict:
    message = db.get(InboundMessage, message_id)
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inbound message not found")
    if message.campaign_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Message has no campaign")
    campaign = db.get(RfqCampaign, message.campaign_id)
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    extracted = QuoteExtractor().extract(message.body or "")
    first_price = extracted.prices[0] if extracted.prices else None
    quote = Quote(
        company_id=message.company_id,
        substance_id=campaign.substance_id,
        campaign_id=campaign.id,
        quantity=first_price.quantity if first_price else None,
        price=Decimal(str(first_price.price)) if first_price and first_price.price is not None else None,
        currency=first_price.currency if first_price else None,
        unit=first_price.unit if first_price else None,
        incoterms=first_price.incoterms if first_price else None,
        lead_time=extracted.lead_time,
        moq=extracted.moq,
        payment_terms=extracted.payment_terms,
        sample_available=extracted.sample_available,
        sample_price=extracted.sample_price,
        packaging=extracted.packaging,
        coa_available=extracted.coa_available,
        sds_available=extracted.sds_available,
        reach_status=extracted.reach_status,
        adr_class=extracted.adr_class,
        un_number=extracted.un_number,
        hs_code=extracted.hs_code,
        shelf_life=extracted.shelf_life,
        certificates=extracted.certificates,
        production_capacity=extracted.production_capacity,
        red_flags=extracted.red_flags,
        missing_questions=extracted.missing_questions,
        confidence=Decimal(str(extracted.confidence)),
        status="needs_review" if extracted.confidence < 0.7 else "parsed",
        extracted_from_message_id=message.id,
    )
    message.parsed = True
    db.add(quote)
    db.flush()
    AuditLogService(db).log(
        "quote_extracted",
        "quote",
        quote.id,
        {"inbound_message_id": message.id, "confidence": extracted.confidence},
    )
    db.commit()
    return {"quote_id": quote.id, "extracted": extracted.model_dump()}


def _load_outbound(db: Session, message_id: str) -> OutboundMessage:
    message = db.get(OutboundMessage, message_id)
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outbound message not found")
    return message


def _message_context(db: Session, message: OutboundMessage):
    supplier = db.scalar(
        select(SupplierCompany)
        .options(selectinload(SupplierCompany.contacts))
        .where(SupplierCompany.id == message.company_id)
    )
    campaign = db.scalar(
        select(RfqCampaign)
        .options(selectinload(RfqCampaign.substance).selectinload(Substance.regulatory_flags))
        .where(RfqCampaign.id == message.campaign_id)
    )
    contact = db.get(SupplierContact, message.contact_id)
    if supplier is None or campaign is None or contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message context not found")
    return supplier, campaign.substance, contact, campaign
