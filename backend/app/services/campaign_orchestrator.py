from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.base import new_uuid
from app.db.models.campaign import RfqCampaign
from app.db.models.message import OutboundMessage
from app.db.models.substance import Substance
from app.db.models.supplier import SupplierCompany, SupplierContact
from app.db.models.task import ManualTask
from app.messaging.email.models import EmailMessage
from app.messaging.email.sender import MockEmailProvider, SMTPEmailSender
from app.services.app_settings import AppSettingsService
from app.services.audit_log import AuditLogService
from app.services.policy_engine import PolicyEngine
from app.services.rfq_generator import RFQGenerator
from app.services.safety_override import SafetyOverrideService


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AutonomousRunOptions:
    supplier_ids: list[str] = field(default_factory=list)
    dry_run: bool = False
    allow_duplicates: bool = False


@dataclass(frozen=True)
class AutonomousRunItem:
    supplier_id: str
    contact_id: str | None
    outbound_message_id: str | None
    policy_decision: str
    status: str
    actions: list[str]
    reasons: list[str]


@dataclass(frozen=True)
class AutonomousRunResult:
    campaign_id: str
    dry_run: bool
    generated: int
    sent: int
    simulated: int
    requires_approval: int
    blocked: int
    skipped: int
    items: list[AutonomousRunItem]


class CampaignOrchestrator:
    def __init__(self, db: Session, strictness: str = "standard") -> None:
        self.db = db
        self.audit = AuditLogService(db)
        self.rfq_generator = RFQGenerator(AppSettingsService(db).get())
        self.safety_override = SafetyOverrideService(db).get()
        self.strictness = strictness
        self.policy_engine = PolicyEngine(self.safety_override, strictness=strictness)
        self.email_sender = SMTPEmailSender()
        self.mock_sender = MockEmailProvider()

    def run(self, campaign_id: str, options: AutonomousRunOptions) -> AutonomousRunResult:
        campaign = self._load_campaign(campaign_id)
        suppliers = self._load_suppliers(options.supplier_ids)
        items: list[AutonomousRunItem] = []

        generated = sent = simulated = requires_approval = blocked = skipped = 0
        for supplier in suppliers:
            contact = self._select_contact(supplier)
            if contact is None:
                task = self._create_task(
                    "missing_contact",
                    "Supplier has no usable contact",
                    f"Add a public business contact with source_url and evidence_text for {supplier.name}.",
                    "supplier",
                    supplier.id,
                    dry_run=options.dry_run,
                )
                skipped += 1
                items.append(
                    AutonomousRunItem(
                        supplier_id=supplier.id,
                        contact_id=None,
                        outbound_message_id=None,
                        policy_decision="SKIPPED",
                        status="manual_task" if task else "dry_run",
                        actions=["add_supplier_contact"],
                        reasons=["supplier has no contacts"],
                    )
                )
                continue

            if not options.allow_duplicates and self._existing_message(campaign.id, supplier.id, contact.id):
                skipped += 1
                items.append(
                    AutonomousRunItem(
                        supplier_id=supplier.id,
                        contact_id=contact.id,
                        outbound_message_id=None,
                        policy_decision="SKIPPED",
                        status="skipped_duplicate",
                        actions=[],
                        reasons=["existing outbound message for campaign/supplier/contact"],
                    )
                )
                continue

            draft = self.rfq_generator.generate(campaign.substance, campaign, supplier)
            message = OutboundMessage(
                id=new_uuid(),
                campaign_id=campaign.id,
                company_id=supplier.id,
                contact_id=contact.id,
                channel=contact.channel,
                subject=draft.subject,
                body=draft.body,
                status="draft",
            )
            decision = self.policy_engine.evaluate_outbound_message(
                message, supplier, campaign.substance, contact, campaign
            )
            message.policy_decision = decision.decision.value
            message.policy_reasons = decision.reasons
            message.approval_required = decision.decision.value not in {"ALLOW_AUTO_SEND", "TEST_OVERRIDE_ALLOW"}

            actions = list(decision.required_actions)
            generated += 1
            if decision.decision.value == "ALLOW_AUTO_SEND":
                if options.dry_run:
                    message.status = "dry_run_allow_auto_send"
                    actions.append("would_send_mock")
                else:
                    sent += 1
                    send_result = self._do_send(message, contact)
                    message.status = "sent" if send_result else "send_failed"
                    message.sent_at = datetime.now(timezone.utc) if send_result else None
                    message.external_message_id = send_result if isinstance(send_result, str) else None
                    message.approval_required = False
                    actions.append("sent_mock")
            elif decision.decision.value == "TEST_OVERRIDE_ALLOW":
                simulated += 1
                message.status = "test_override_simulated_send"
                message.approval_required = False
                actions.append("simulated_send_only")
            elif decision.decision.value == "BLOCK":
                blocked += 1
                message.status = "blocked"
                self._create_task(
                    "policy_blocked",
                    "Policy blocked outbound RFQ",
                    "; ".join(decision.reasons),
                    "outbound_message",
                    message.id,
                    dry_run=options.dry_run,
                )
                actions.append("created_policy_block_task")
            else:
                requires_approval += 1
                message.status = "requires_approval"
                self._create_task(
                    "approval_needed",
                    "Approve RFQ before sending",
                    "; ".join(decision.reasons),
                    "outbound_message",
                    message.id,
                    dry_run=options.dry_run,
                )
                actions.append("created_approval_task")

            if not options.dry_run:
                self.db.add(message)
                self.db.flush()
                self.audit.log(
                    "autonomous_rfq_evaluated",
                    "outbound_message",
                    message.id,
                    {
                        "campaign_id": campaign.id,
                        "supplier_id": supplier.id,
                        "contact_id": contact.id,
                        "policy_decision": message.policy_decision,
                        "status": message.status,
                        "actions": actions,
                        "test_override_active": self.safety_override.active,
                    },
                )

            items.append(
                AutonomousRunItem(
                    supplier_id=supplier.id,
                    contact_id=contact.id,
                    outbound_message_id=None if options.dry_run else message.id,
                    policy_decision=decision.decision.value,
                    status=message.status or "draft",
                    actions=actions,
                    reasons=decision.reasons,
                )
            )

        self.audit.log(
            "autonomous_campaign_run",
            "campaign",
            campaign.id,
            {
                "dry_run": options.dry_run,
                "generated": generated,
                "sent": sent,
                "simulated": simulated,
                "requires_approval": requires_approval,
                "blocked": blocked,
                "skipped": skipped,
                "test_override_active": self.safety_override.active,
            },
        )
        return AutonomousRunResult(
            campaign_id=campaign.id,
            dry_run=options.dry_run,
            generated=generated,
            sent=sent,
            simulated=simulated,
            requires_approval=requires_approval,
            blocked=blocked,
            skipped=skipped,
            items=items,
        )

    def _do_send(self, message: OutboundMessage, contact: SupplierContact) -> str | bool:
        """MVP send path uses mock providers only."""
        channel = (contact.channel or "email").lower()

        if channel == "email":
            email_msg = EmailMessage(
                to=contact.value,
                subject=message.subject or "RFQ Inquiry",
                body=message.body or "",
            )
            result = self.mock_sender.send(email_msg)
            return result.external_message_id or True

        if channel == "form":
            logger.info(
                "Contact form send is represented as a reviewed mock submission for %s",
                contact.source_url or contact.value,
            )
            return f"form-mock-{message.id}"

        logger.info("Marketplace/messenger channel %s remains draft/manual/API-only", channel)
        return f"mock-{message.id}"

    def batch_approve_and_send(
        self, campaign_id: str, message_ids: list[str] | None = None, user_id: str | None = None
    ) -> dict:
        """Approve all pending messages for a campaign and send them."""
        campaign = self._load_campaign(campaign_id)
        statement = select(OutboundMessage).where(
            OutboundMessage.campaign_id == campaign_id,
            OutboundMessage.status.in_(["requires_approval", "draft"]),
        )
        if message_ids:
            statement = statement.where(OutboundMessage.id.in_(message_ids))

        messages = list(self.db.scalars(statement))
        approved = sent = failed = 0
        results: list[dict] = []

        for message in messages:
            supplier = self.db.scalar(
                select(SupplierCompany)
                .options(selectinload(SupplierCompany.contacts))
                .where(SupplierCompany.id == message.company_id)
            )
            contact = self.db.get(SupplierContact, message.contact_id)
            if not supplier or not contact:
                failed += 1
                results.append({"message_id": message.id, "status": "context_missing"})
                continue

            decision = self.policy_engine.evaluate_outbound_message(
                message, supplier, campaign.substance, contact, campaign
            )
            message.policy_decision = decision.decision.value
            message.policy_reasons = decision.reasons

            # Approve and send
            message.status = "approved"
            message.approval_required = False
            message.approved_at = datetime.now(timezone.utc)
            send_result = self._do_send(message, contact)
            if send_result:
                message.status = "sent"
                message.sent_at = datetime.now(timezone.utc)
                message.external_message_id = send_result if isinstance(send_result, str) else None
                sent += 1
                results.append({"message_id": message.id, "status": "sent"})
            else:
                message.status = "send_failed"
                failed += 1
                results.append({"message_id": message.id, "status": "send_failed"})
            approved += 1

        # Update campaign batch approval
        if user_id:
            campaign.batch_approved = True
            campaign.batch_approved_by = user_id
            campaign.batch_approved_at = datetime.now(timezone.utc)

        self.audit.log(
            "campaign_batch_approved_and_sent",
            "campaign",
            campaign_id,
            {"approved": approved, "sent": sent, "failed": failed},
        )
        self.db.commit()
        return {"approved": approved, "sent": sent, "failed": failed, "results": results}

    def _load_campaign(self, campaign_id: str) -> RfqCampaign:
        campaign = self.db.scalar(
            select(RfqCampaign)
            .options(selectinload(RfqCampaign.substance).selectinload(Substance.regulatory_flags))
            .where(RfqCampaign.id == campaign_id)
        )
        if campaign is None:
            raise ValueError("Campaign not found")
        return campaign

    def _load_suppliers(self, supplier_ids: list[str]) -> list[SupplierCompany]:
        statement = select(SupplierCompany).options(selectinload(SupplierCompany.contacts))
        if supplier_ids:
            statement = statement.where(SupplierCompany.id.in_(supplier_ids))
        return list(self.db.scalars(statement.order_by(SupplierCompany.created_at.asc())))

    def _select_contact(self, supplier: SupplierCompany) -> SupplierContact | None:
        contacts = list(supplier.contacts or [])
        if not contacts:
            return None
        return next((contact for contact in contacts if contact.is_primary), contacts[0])

    def _existing_message(self, campaign_id: str, supplier_id: str, contact_id: str) -> bool:
        return (
            self.db.scalar(
                select(OutboundMessage.id).where(
                    OutboundMessage.campaign_id == campaign_id,
                    OutboundMessage.company_id == supplier_id,
                    OutboundMessage.contact_id == contact_id,
                )
            )
            is not None
        )

    def _create_task(
        self,
        task_type: str,
        title: str,
        description: str,
        related_object_type: str,
        related_object_id: str | None,
        dry_run: bool,
    ) -> ManualTask | None:
        if dry_run:
            return None
        task = ManualTask(
            task_type=task_type,
            title=title,
            description=description,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
            status="open",
        )
        self.db.add(task)
        self.db.flush()
        self.audit.log("manual_task_created", "manual_task", task.id, {"task_type": task_type})
        return task
