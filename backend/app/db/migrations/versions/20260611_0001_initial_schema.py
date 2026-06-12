"""initial schema

Revision ID: 20260611_0001
Revises:
Create Date: 2026-06-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260611_0001"
down_revision = None
branch_labels = None
depends_on = None


JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "substances",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cas", sa.Text(), nullable=False, unique=True),
        sa.Column("primary_name", sa.Text()),
        sa.Column("iupac_name", sa.Text()),
        sa.Column("molecular_formula", sa.Text()),
        sa.Column("molecular_weight", sa.Numeric()),
        sa.Column("pubchem_cid", sa.Text()),
        sa.Column("ec_number", sa.Text()),
        sa.Column("hs_code_suggested", sa.Text()),
        sa.Column("hs_code_confidence", sa.Numeric()),
        sa.Column("regulatory_status", sa.Text()),
        sa.Column("requires_manual_review", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_substances_cas", "substances", ["cas"])

    op.create_table(
        "substance_synonyms",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("substance_id", sa.String(36), sa.ForeignKey("substances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("synonym", sa.Text(), nullable=False),
        sa.Column("source", sa.Text()),
    )
    op.create_index("ix_substance_synonyms_substance_id", "substance_synonyms", ["substance_id"])

    op.create_table(
        "regulatory_flags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("substance_id", sa.String(36), sa.ForeignKey("substances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("flag_type", sa.Text()),
        sa.Column("severity", sa.Text()),
        sa.Column("source", sa.Text()),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_regulatory_flags_substance_id", "regulatory_flags", ["substance_id"])

    op.create_table(
        "supplier_companies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("website", sa.Text()),
        sa.Column("country", sa.Text()),
        sa.Column("address", sa.Text()),
        sa.Column("company_type", sa.Text()),
        sa.Column("registration_number", sa.Text()),
        sa.Column("vat_number", sa.Text()),
        sa.Column("eori_number", sa.Text()),
        sa.Column("verified_status", sa.Text()),
        sa.Column("supplier_score", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("risk_score", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("risk_level", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_supplier_companies_name", "supplier_companies", ["name"])
    op.create_index("ix_supplier_companies_country", "supplier_companies", ["country"])

    op.create_table(
        "supplier_contacts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("supplier_companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("contact_person", sa.Text()),
        sa.Column("source_url", sa.Text()),
        sa.Column("evidence_text", sa.Text()),
        sa.Column("consent_status", sa.Text()),
        sa.Column("consent_evidence_id", sa.String(36)),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_supplier_contacts_channel", "supplier_contacts", ["channel"])

    op.create_table(
        "consent_evidence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("supplier_companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contact_channel", sa.Text()),
        sa.Column("evidence_type", sa.Text()),
        sa.Column("source_url", sa.Text()),
        sa.Column("source_text", sa.Text()),
        sa.Column("screenshot_path", sa.Text()),
        sa.Column("collected_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "raw_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_url", sa.Text()),
        sa.Column("content_hash", sa.Text()),
        sa.Column("html_path", sa.Text()),
        sa.Column("screenshot_path", sa.Text()),
        sa.Column("fetched_at", sa.DateTime(timezone=True)),
        sa.Column("fetch_status", sa.Text()),
    )

    op.create_table(
        "product_offers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("supplier_companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("substance_id", sa.String(36), sa.ForeignKey("substances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_url", sa.Text()),
        sa.Column("listed_name", sa.Text()),
        sa.Column("listed_cas", sa.Text()),
        sa.Column("grade", sa.Text()),
        sa.Column("purity", sa.Text()),
        sa.Column("moq", sa.Text()),
        sa.Column("price_text", sa.Text()),
        sa.Column("currency", sa.Text()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("raw_snapshot_id", sa.String(36)),
    )

    op.create_table(
        "rfq_campaigns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("substance_id", sa.String(36), sa.ForeignKey("substances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Text()),
        sa.Column("destination_country", sa.Text()),
        sa.Column("required_grade", sa.Text()),
        sa.Column("intended_use", sa.Text()),
        sa.Column("requirements", JSONB),
        sa.Column("status", sa.Text()),
        sa.Column("auto_send_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "outbound_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("campaign_id", sa.String(36), sa.ForeignKey("rfq_campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("supplier_companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contact_id", sa.String(36), sa.ForeignKey("supplier_contacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", sa.Text()),
        sa.Column("subject", sa.Text()),
        sa.Column("body", sa.Text()),
        sa.Column("status", sa.Text()),
        sa.Column("policy_decision", sa.Text()),
        sa.Column("policy_reasons", JSONB),
        sa.Column("approval_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("approved_by", sa.String(36)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("external_message_id", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "inbound_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("supplier_companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("campaign_id", sa.String(36), sa.ForeignKey("rfq_campaigns.id", ondelete="SET NULL")),
        sa.Column("channel", sa.Text()),
        sa.Column("from_address", sa.Text()),
        sa.Column("subject", sa.Text()),
        sa.Column("body", sa.Text()),
        sa.Column("received_at", sa.DateTime(timezone=True)),
        sa.Column("parsed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("external_message_id", sa.Text()),
        sa.Column("thread_id", sa.Text()),
    )

    op.create_table(
        "quotes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("supplier_companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("substance_id", sa.String(36), sa.ForeignKey("substances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("campaign_id", sa.String(36), sa.ForeignKey("rfq_campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Text()),
        sa.Column("price", sa.Numeric()),
        sa.Column("currency", sa.Text()),
        sa.Column("unit", sa.Text()),
        sa.Column("incoterms", sa.Text()),
        sa.Column("lead_time", sa.Text()),
        sa.Column("moq", sa.Text()),
        sa.Column("payment_terms", sa.Text()),
        sa.Column("sample_available", sa.Boolean()),
        sa.Column("sample_price", sa.Text()),
        sa.Column("packaging", sa.Text()),
        sa.Column("coa_available", sa.Boolean()),
        sa.Column("sds_available", sa.Boolean()),
        sa.Column("reach_status", sa.Text()),
        sa.Column("adr_class", sa.Text()),
        sa.Column("un_number", sa.Text()),
        sa.Column("hs_code", sa.Text()),
        sa.Column("shelf_life", sa.Text()),
        sa.Column("certificates", JSONB),
        sa.Column("production_capacity", sa.Text()),
        sa.Column("red_flags", JSONB),
        sa.Column("missing_questions", JSONB),
        sa.Column("confidence", sa.Numeric()),
        sa.Column("status", sa.Text()),
        sa.Column("extracted_from_message_id", sa.String(36)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "manual_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_type", sa.Text()),
        sa.Column("title", sa.Text()),
        sa.Column("description", sa.Text()),
        sa.Column("related_object_type", sa.Text()),
        sa.Column("related_object_id", sa.String(36)),
        sa.Column("status", sa.Text()),
        sa.Column("assigned_to", sa.String(36)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor_id", sa.String(36)),
        sa.Column("actor_type", sa.Text()),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("object_type", sa.Text()),
        sa.Column("object_id", sa.String(36)),
        sa.Column("details", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_log_action", "audit_log", ["action"])

    op.create_table(
        "settings",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("value", JSONB),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for table_name in [
        "settings",
        "audit_log",
        "manual_tasks",
        "quotes",
        "inbound_messages",
        "outbound_messages",
        "rfq_campaigns",
        "product_offers",
        "raw_snapshots",
        "consent_evidence",
        "supplier_contacts",
        "supplier_companies",
        "regulatory_flags",
        "substance_synonyms",
        "substances",
        "users",
    ]:
        op.drop_table(table_name)
