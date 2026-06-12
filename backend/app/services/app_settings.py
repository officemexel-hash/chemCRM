from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models.settings import Setting
from app.schemas.app_settings import (
    AppSettings,
    ControlledQuestion,
    ConversationTrainingScenario,
    ResponsePlaybookRule,
)


APP_SETTINGS_KEY = "app_settings"


def default_app_settings() -> AppSettings:
    return AppSettings(
        controlled_questions=[
            ControlledQuestion(
                key="product_identity",
                category="product",
                text="Please confirm exact CAS number, product name, grade, purity/assay, and available synonyms/trade names.",
                required=True,
            ),
            ControlledQuestion(
                key="documents",
                category="documents",
                text="Please confirm availability of COA, SDS/MSDS, specification sheet, and TDS.",
                required=True,
            ),
            ControlledQuestion(
                key="supplier_role",
                category="supplier",
                text="Please confirm whether you are the manufacturer, authorized distributor, or trading company, and provide manufacturer name and country of origin.",
                required=True,
            ),
            ControlledQuestion(
                key="commercial_terms",
                category="commercial",
                text="Please provide MOQ, price per kg, price breaks, sample availability, lead time, shelf life, and packaging options.",
                required=True,
            ),
            ControlledQuestion(
                key="logistics_compliance",
                category="logistics",
                text="Please confirm Incoterms options, shipping feasibility, ADR/DG class, UN number, HS code suggestion, REACH status, and any export/import restrictions.",
                required=True,
            ),
            ControlledQuestion(
                key="payment_invoice",
                category="payment",
                text="Please confirm payment terms, advance payment percentage, invoice availability, and accepted secure payment methods.",
                required=True,
            ),
        ],
        response_playbook=[
            ResponsePlaybookRule(
                name="Missing documents",
                trigger_terms=["no coa", "no sds", "no msds", "cannot provide coa", "cannot provide sds"],
                supplier_intent="missing_documents",
                recommended_action="request_documents_or_reject",
                response_template=(
                    "Thank you for the clarification. We require accurate COA and SDS/MSDS before any procurement review can continue. "
                    "Please provide these documents or confirm that you cannot supply them."
                ),
                creates_manual_task=True,
            ),
            ResponsePlaybookRule(
                name="Move to marketplace/internal chat",
                trigger_terms=["contact supplier", "alibaba", "made-in-china", "marketplace chat", "inquiry center"],
                supplier_intent="marketplace_internal_contact",
                recommended_action="manual_marketplace_task",
                response_template=(
                    "We can continue through the official marketplace inquiry flow after internal approval. "
                    "Please keep all product, document, and trade information accurate and complete."
                ),
                creates_manual_task=True,
            ),
            ResponsePlaybookRule(
                name="Fraud or evasion",
                trigger_terms=["misdeclare", "fake invoice", "false declaration", "avoid customs", "ship as gift", "no invoice"],
                supplier_intent="fraud_or_evasion",
                recommended_action="block",
                response_template=(
                    "We cannot proceed with any false declaration, missing invoice, or workaround of applicable rules."
                ),
                creates_manual_task=True,
                block_if_matched=True,
            ),
        ],
        training_scenarios=[
            ConversationTrainingScenario(
                name="Supplier misses COA/SDS",
                supplier_message="We can quote, but COA and SDS are not available before payment.",
                expected_action="request_documents_or_reject",
                notes="System should not proceed without documents.",
            ),
            ConversationTrainingScenario(
                name="Supplier suggests marketplace chat",
                supplier_message="Please contact us through Alibaba inquiry center for the quotation.",
                expected_action="manual_marketplace_task",
                notes="System should create a manual marketplace task.",
            ),
            ConversationTrainingScenario(
                name="Supplier suggests false declaration",
                supplier_message="We can ship as gift with no invoice to avoid customs issues.",
                expected_action="block",
                notes="System must block and flag fraud/evasion.",
            ),
        ],
    )


class AppSettingsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self) -> AppSettings:
        row = self.db.get(Setting, APP_SETTINGS_KEY)
        if row is None or row.value is None:
            return default_app_settings()
        return AppSettings.model_validate(row.value)

    def get_with_updated_at(self) -> tuple[AppSettings, str | None]:
        row = self.db.get(Setting, APP_SETTINGS_KEY)
        if row is None or row.value is None:
            return default_app_settings(), None
        updated_at = row.updated_at.isoformat() if row.updated_at else None
        return AppSettings.model_validate(row.value), updated_at

    def save(self, settings: AppSettings) -> AppSettings:
        row = self.db.get(Setting, APP_SETTINGS_KEY)
        value = settings.model_dump(mode="json")
        if row is None:
            row = Setting(key=APP_SETTINGS_KEY, value=value, updated_at=datetime.now(timezone.utc))
            self.db.add(row)
        else:
            row.value = value
            row.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return settings
