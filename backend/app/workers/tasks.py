import logging

from app.db.models.message import InboundMessage, OutboundMessage
from app.db.models.quote import Quote
from app.db.models.substance import Substance
from app.db.models.supplier import SupplierCompany, SupplierContact
from app.db.session import SessionLocal
from app.messaging.email.models import EmailMessage
from app.messaging.email.sender import MockEmailProvider
from app.services.audit_log import AuditLogService
from app.services.channel_router import ChannelRouter
from app.services.followup_generator import FollowupGenerator
from app.services.policy_engine import PolicyEngine
from app.services.quote_extractor import QuoteExtractor
from app.services.rfq_generator import RFQGenerator
from app.services.substance_enrichment import SubstanceEnrichmentService
from app.services.supplier_classifier import SupplierClassifier
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def enrich_substance_task(self, substance_id: str) -> dict:
    with SessionLocal() as db:
        substance = db.get(Substance, substance_id)
        if not substance:
            return {"status": "failed", "error": "Substance not found"}
        result = SubstanceEnrichmentService().enrich_by_cas(substance.cas)
        substance.primary_name = result.primary_name
        substance.molecular_formula = result.molecular_formula
        substance.pubchem_cid = result.pubchem_cid
        AuditLogService(db).log("task_enrich_substance_completed", "substance", substance_id, {"provider": "celery"})
        db.commit()
        return {"status": "enriched", "substance_id": substance_id, "primary_name": result.primary_name}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def classify_supplier_task(self, supplier_id: str) -> dict:
    with SessionLocal() as db:
        supplier = db.get(SupplierCompany, supplier_id)
        if not supplier:
            return {"status": "failed", "error": "Supplier not found"}
        classification = SupplierClassifier().classify(supplier)
        supplier.company_type = classification.company_type
        supplier.supplier_score = classification.supplier_score
        supplier.risk_score = classification.risk_score
        supplier.risk_level = classification.risk_level
        AuditLogService(db).log("task_classify_supplier_completed", "supplier", supplier_id, {"company_type": classification.company_type})
        db.commit()
        return {"status": "classified", "supplier_id": supplier_id, "company_type": classification.company_type}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def generate_rfq_task(self, campaign_id: str, supplier_id: str) -> dict:
    with SessionLocal() as db:
        from app.db.models.campaign import RfqCampaign
        campaign = db.get(RfqCampaign, campaign_id)
        supplier = db.get(SupplierCompany, supplier_id)
        if not campaign or not supplier:
            return {"status": "failed", "error": "Campaign or supplier not found"}
        draft = RFQGenerator(None).generate(campaign.substance, campaign, supplier)
        AuditLogService(db).log("task_generate_rfq_completed", "campaign", campaign_id)
        db.commit()
        return {"status": "generated", "subject": draft.subject}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_email_task(self, outbound_message_id: str) -> dict:
    with SessionLocal() as db:
        msg = db.get(OutboundMessage, outbound_message_id)
        if not msg:
            return {"status": "failed", "error": "Message not found"}
        contact = db.get(SupplierContact, msg.contact_id)
        if not contact:
            return {"status": "failed", "error": "Contact not found"}
        router = ChannelRouter()
        result = router.send(msg, contact)
        if result["status"] == "sent":
            msg.status = "sent"
            AuditLogService(db).log("task_send_email_completed", "outbound_message", outbound_message_id, result)
        db.commit()
        return result


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def extract_quote_task(self, inbound_message_id: str) -> dict:
    with SessionLocal() as db:
        msg = db.get(InboundMessage, inbound_message_id)
        if not msg:
            return {"status": "failed", "error": "Message not found"}
        body = msg.body or ""
        extracted = QuoteExtractor().extract(body)
        quote = Quote(
            company_id=msg.company_id,
            campaign_id=msg.campaign_id,
            extracted_from_message_id=inbound_message_id,
            price=extracted.get("price"),
            currency=extracted.get("currency"),
            unit=extracted.get("unit"),
            moq=extracted.get("moq"),
            incoterms=extracted.get("incoterms"),
            lead_time=extracted.get("lead_time"),
            status="parsed",
        )
        db.add(quote)
        db.flush()
        AuditLogService(db).log("task_extract_quote_completed", "quote", quote.id)
        db.commit()
        return {"status": "extracted", "quote_id": quote.id}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def generate_followup_task(self, inbound_message_id: str) -> dict:
    with SessionLocal() as db:
        msg = db.get(InboundMessage, inbound_message_id)
        if not msg:
            return {"status": "failed", "error": "Message not found"}
        gen = FollowupGenerator()
        followup = gen.generate(msg.body or "")
        AuditLogService(db).log("task_generate_followup_completed", "inbound_message", inbound_message_id)
        db.commit()
        return {"status": "generated", "followup": followup.body[:200] if followup else ""}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def evaluate_policy_task(self, outbound_message_id: str) -> dict:
    with SessionLocal() as db:
        msg = db.get(OutboundMessage, outbound_message_id)
        if not msg:
            return {"status": "failed", "error": "Message not found"}
        decision = PolicyEngine().evaluate_outbound_message(msg, None, None, None, None)
        msg.policy_decision = decision.decision.value
        msg.policy_reasons = decision.reasons
        AuditLogService(db).log("task_evaluate_policy_completed", "outbound_message", outbound_message_id, {"decision": decision.decision.value})
        db.commit()
        return {"status": "evaluated", "decision": decision.decision.value}


# ── Remaining tasks (skeletons for less critical workflows) ──

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def discovery_task(self, campaign_id: str | None = None, substance_id: str | None = None) -> dict:
    with SessionLocal() as db:
        AuditLogService(db).log("task_discovery_queued", "campaign" if campaign_id else "substance", campaign_id or substance_id)
        db.commit()
    return {"status": "manual_review_required", "campaign_id": campaign_id, "substance_id": substance_id}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def fetch_page_task(self, url: str) -> dict:
    return {"status": "manual_review_required", "url": url}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def extract_supplier_task(self, snapshot_id: str) -> dict:
    return {"status": "manual_review_required", "snapshot_id": snapshot_id}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def submit_form_task(self, outbound_message_id: str) -> dict:
    with SessionLocal() as db:
        AuditLogService(db).log("task_submit_form_queued", "outbound_message", outbound_message_id)
        db.commit()
    return {"status": "manual_review_required", "outbound_message_id": outbound_message_id}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def poll_inbox_task(self) -> dict:
    return {"status": "ok", "new_messages": 0}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def parse_inbound_message_task(self, inbound_message_id: str) -> dict:
    with SessionLocal() as db:
        AuditLogService(db).log("task_parse_inbound_queued", "inbound_message", inbound_message_id)
        db.commit()
    return {"status": "queued", "inbound_message_id": inbound_message_id}
