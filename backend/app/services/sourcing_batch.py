import re
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models.campaign import RfqCampaign
from app.db.models.message import InboundMessage, OutboundMessage
from app.db.models.quote import Quote
from app.db.models.settings import Setting
from app.db.models.substance import Substance
from app.db.models.task import ManualTask
from app.schemas.sourcing import (
    DEFAULT_SOURCING_CHANNELS,
    SourcingBatchImportRequest,
    SourcingBatchItemRead,
    SourcingBatchRead,
    SourcingBatchReportRead,
    SourcingBatchSummary,
    SourcingQueryRead,
    SourcingTaskRead,
)
from app.services.audit_log import AuditLogService
from app.services.cas_validator import is_valid_cas, normalize_cas
from app.services.search_query_generator import generate_search_queries


BATCH_KEY_PREFIX = "sourcing_batch:"
CAS_LIKE_PATTERN = re.compile(r"\b\d{2,7}-\d{2}-\d\b")

CHANNEL_PLAN = {
    "legal_search": "Generate legal search/API queries; no Google scraping or rate-limit bypass.",
    "contact_form": "Create reviewed form-submission tasks; CAPTCHA/login/terms issues stay manual.",
    "alibaba_internal": "Create Alibaba inquiry/chat draft tasks for authorized portal users only.",
    "made_in_china_internal": "Create Made-in-China inquiry draft tasks for authorized portal users only.",
    "molbase_internal": "Create Molbase profile/inquiry review tasks; API/UI flow only.",
    "indiamart_internal": "Create IndiaMART inquiry review tasks; authorized UI/API flow only.",
    "whatsapp_business": "Use WhatsApp Business API flow only after consent evidence.",
    "telegram_bot": "Use Telegram Bot/API or official channel only after consent evidence.",
    "signal_manual": "Signal remains manual-task only.",
    "threema_gateway": "Use Threema Gateway only after consent evidence.",
    "wickr_manual": "Wickr remains manual-task only.",
}


class SourcingBatchService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditLogService(db)

    def create_batch(self, payload: SourcingBatchImportRequest) -> SourcingBatchRead:
        batch_id = str(uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        channels = _normalize_channels(payload.channels)
        raw_inputs = _parse_cas_inputs(payload)

        summary = SourcingBatchSummary(total_inputs=len(raw_inputs))
        items: list[SourcingBatchItemRead] = []
        seen_valid: set[str] = set()

        for raw_cas in raw_inputs:
            normalized = normalize_cas(raw_cas)
            if not is_valid_cas(normalized):
                summary.invalid += 1
                items.append(
                    SourcingBatchItemRead(
                        raw_cas=raw_cas,
                        cas=normalized,
                        status="invalid",
                        errors=["Invalid CAS format or checksum."],
                    )
                )
                continue

            if normalized in seen_valid:
                summary.duplicates += 1
                items.append(
                    SourcingBatchItemRead(
                        raw_cas=raw_cas,
                        cas=normalized,
                        status="duplicate",
                        errors=["Duplicate CAS in batch input."],
                    )
                )
                continue
            seen_valid.add(normalized)
            summary.valid += 1

            substance, created_substance = self._get_or_create_substance(normalized)
            if created_substance:
                summary.substances_created += 1

            campaign = None
            if payload.create_campaigns:
                campaign = self._create_campaign(payload, substance, batch_id)
                summary.campaigns_created += 1

            synonyms = [synonym.synonym for synonym in getattr(substance, "synonyms", []) or []]
            queries = [
                SourcingQueryRead(
                    query=query.query,
                    priority=query.priority,
                    source_reason=query.source_reason,
                )
                for query in generate_search_queries(substance.cas, substance.primary_name, synonyms[:5])
            ]
            summary.queries_generated += len(queries)

            tasks = self._create_channel_tasks(
                channels=channels,
                cas=substance.cas,
                substance_id=substance.id,
                campaign_id=campaign.id if campaign else None,
                queries=queries,
            )
            summary.manual_tasks_created += len(tasks)

            items.append(
                SourcingBatchItemRead(
                    raw_cas=raw_cas,
                    cas=substance.cas,
                    status="ready",
                    substance_id=substance.id,
                    campaign_id=campaign.id if campaign else None,
                    queries=queries,
                    tasks=tasks,
                )
            )

        batch = SourcingBatchRead(
            batch_id=batch_id,
            name=payload.name,
            created_at=created_at,
            channels=channels,
            summary=summary,
            items=items,
        )
        self._save_batch(batch)
        self.audit.log(
            "sourcing_batch_imported",
            "sourcing_batch",
            batch_id,
            {
                "name": payload.name,
                "summary": summary.model_dump(),
                "channels": channels,
            },
        )
        return batch

    def get_batch(self, batch_id: str) -> SourcingBatchRead | None:
        row = self.db.get(Setting, f"{BATCH_KEY_PREFIX}{batch_id}")
        if row is None or row.value is None:
            return None
        return SourcingBatchRead.model_validate(row.value)

    def get_report(self, batch_id: str) -> SourcingBatchReportRead | None:
        batch = self.get_batch(batch_id)
        if batch is None:
            return None

        campaign_ids = [item.campaign_id for item in batch.items if item.campaign_id]
        substance_ids = [item.substance_id for item in batch.items if item.substance_id]
        manual_task_ids = [task.id for item in batch.items for task in item.tasks]

        return SourcingBatchReportRead(
            batch=batch,
            campaign_ids=campaign_ids,
            substance_ids=substance_ids,
            manual_task_ids=manual_task_ids,
            outbound_messages=_count_for_ids(self.db, OutboundMessage, OutboundMessage.campaign_id, campaign_ids),
            inbound_messages=_count_for_ids(self.db, InboundMessage, InboundMessage.campaign_id, campaign_ids),
            quotes=_count_for_ids(self.db, Quote, Quote.campaign_id, campaign_ids),
            channel_plan={channel: CHANNEL_PLAN[channel] for channel in batch.channels if channel in CHANNEL_PLAN},
        )

    def _get_or_create_substance(self, cas: str) -> tuple[Substance, bool]:
        substance = self.db.scalar(
            select(Substance)
            .options(selectinload(Substance.synonyms), selectinload(Substance.regulatory_flags))
            .where(Substance.cas == cas)
        )
        if substance is not None:
            return substance, False
        substance = Substance(
            cas=cas,
            regulatory_status="unknown",
            requires_manual_review=True,
        )
        self.db.add(substance)
        self.db.flush()
        self.audit.log("substance_created_from_batch", "substance", substance.id, {"cas": cas})
        return substance, True

    def _create_campaign(
        self, payload: SourcingBatchImportRequest, substance: Substance, batch_id: str
    ) -> RfqCampaign:
        requirements = {
            **payload.requirements,
            "source": "sourcing_batch",
            "sourcing_batch_id": batch_id,
            "requested_channels": payload.channels,
        }
        campaign = RfqCampaign(
            substance_id=substance.id,
            quantity=payload.quantity,
            destination_country=payload.destination_country,
            required_grade=payload.required_grade,
            intended_use=payload.intended_use,
            requirements=requirements,
            status="sourcing",
            auto_send_enabled=payload.auto_send_enabled,
        )
        self.db.add(campaign)
        self.db.flush()
        self.audit.log(
            "campaign_created_from_batch",
            "campaign",
            campaign.id,
            {"substance_id": substance.id, "batch_id": batch_id},
        )
        return campaign

    def _create_channel_tasks(
        self,
        channels: list[str],
        cas: str,
        substance_id: str,
        campaign_id: str | None,
        queries: list[SourcingQueryRead],
    ) -> list[SourcingTaskRead]:
        tasks: list[SourcingTaskRead] = []
        related_object_type = "campaign" if campaign_id else "substance"
        related_object_id = campaign_id or substance_id
        query_preview = "; ".join(query.query for query in queries[:8])

        if "legal_search" in channels:
            tasks.append(
                self._create_task(
                    "sourcing_discovery",
                    f"Review legal supplier discovery for CAS {cas}",
                    (
                        "Use legal search APIs, public B2B directories, supplier websites, or manually imported URLs. "
                        f"Initial queries: {query_preview}"
                    ),
                    related_object_type,
                    related_object_id,
                    "legal_search",
                )
            )

        if "contact_form" in channels:
            tasks.append(
                self._create_task(
                    "contact_form_review",
                    f"Prepare contact form RFQ drafts for CAS {cas}",
                    (
                        "Detect public business contact forms and prepare reviewed RFQ drafts. "
                        "Do not bypass CAPTCHA, login, rate limits, or portal terms."
                    ),
                    related_object_type,
                    related_object_id,
                    "contact_form",
                )
            )

        for channel in channels:
            if channel in {"alibaba_internal", "made_in_china_internal", "molbase_internal", "indiamart_internal"}:
                tasks.append(
                    self._create_task(
                        "marketplace_inquiry_review",
                        f"Prepare {channel.replace('_', ' ')} inquiry draft for CAS {cas}",
                        (
                            "Use only an authorized business account, official UI/API flow, and human-reviewed supplier evidence. "
                            "Login, CAPTCHA, terms acceptance, and final send remain manual unless a compliant official API is configured."
                        ),
                        related_object_type,
                        related_object_id,
                        channel,
                    )
                )

        for channel in channels:
            if channel in {"whatsapp_business", "telegram_bot", "signal_manual", "threema_gateway", "wickr_manual"}:
                tasks.append(
                    self._create_task(
                        "messenger_consent_review",
                        f"Review {channel.replace('_', ' ')} path for CAS {cas}",
                        (
                            "Create a draft/manual task only. Automated messenger contact requires official business/API flow "
                            "and consent_evidence. Signal and Wickr remain manual-only in MVP."
                        ),
                        related_object_type,
                        related_object_id,
                        channel,
                    )
                )
        return tasks

    def _create_task(
        self,
        task_type: str,
        title: str,
        description: str,
        related_object_type: str,
        related_object_id: str | None,
        channel: str | None,
    ) -> SourcingTaskRead:
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
        self.audit.log(
            "manual_task_created",
            "manual_task",
            task.id,
            {"task_type": task_type, "channel": channel},
        )
        return SourcingTaskRead(
            id=task.id,
            task_type=task_type,
            title=title,
            channel=channel,
        )

    def _save_batch(self, batch: SourcingBatchRead) -> None:
        row = Setting(
            key=f"{BATCH_KEY_PREFIX}{batch.batch_id}",
            value=batch.model_dump(mode="json"),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(row)
        self.db.flush()


def _parse_cas_inputs(payload: SourcingBatchImportRequest) -> list[str]:
    inputs: list[str] = []
    inputs.extend(item.strip() for item in payload.cas_numbers if item.strip())
    if payload.csv_text:
        for match in CAS_LIKE_PATTERN.finditer(payload.csv_text):
            inputs.append(match.group(0).strip())
    return inputs


def _normalize_channels(channels: list[str]) -> list[str]:
    allowed = set(CHANNEL_PLAN)
    normalized: list[str] = []
    for channel in channels or DEFAULT_SOURCING_CHANNELS:
        value = channel.strip().lower()
        if value in allowed and value not in normalized:
            normalized.append(value)
    return normalized or DEFAULT_SOURCING_CHANNELS.copy()


def _count_for_ids(db: Session, model, column, ids: list[str]) -> int:
    if not ids:
        return 0
    return int(db.scalar(select(func.count(model.id)).where(column.in_(ids))) or 0)
