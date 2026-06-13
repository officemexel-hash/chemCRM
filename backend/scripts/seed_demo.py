from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.db.models import Base
from app.db.models.campaign import RfqCampaign
from app.db.models.message import InboundMessage, OutboundMessage
from app.db.models.quote import Quote
from app.db.models.substance import Substance, SubstanceSynonym
from app.db.models.supplier import SupplierCompany, SupplierContact
from app.db.models.user import User
from app.db.session import SessionLocal, engine
from app.services.audit_log import AuditLogService


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.query(User).filter(User.email == "demo@example.com").first():
            print("Demo data already exists.")
            return

        user = User(email="demo@example.com", password_hash=hash_password("ChangeMe123!"))
        ethanol = Substance(
            cas="64-17-5",
            primary_name="Ethanol",
            iupac_name="ethanol",
            molecular_formula="C2H6O",
            molecular_weight=Decimal("46.07"),
            pubchem_cid="702",
            ec_number="200-578-6",
            regulatory_status="unreviewed",
            requires_manual_review=False,
        )
        ethanol.synonyms.append(SubstanceSynonym(synonym="ethyl alcohol", source="seed"))
        water = Substance(
            cas="7732-18-5",
            primary_name="Water",
            iupac_name="oxidane",
            molecular_formula="H2O",
            molecular_weight=Decimal("18.015"),
            pubchem_cid="962",
            ec_number="231-791-2",
            regulatory_status="unreviewed",
            requires_manual_review=False,
        )

        suppliers = [
            SupplierCompany(
                name="Acme Chemical Manufacturer",
                website="https://acme.example",
                country="PL",
                address="1 Industrial Road",
                company_type="MANUFACTURER",
                registration_number="REG123",
                verified_status="audited",
                supplier_score=95,
                risk_score=0,
                risk_level="low",
                notes="Demo manufacturer with SDS, COA, MOQ, lead time and Incoterms.",
            ),
            SupplierCompany(
                name="Euro Lab Supplies",
                website="https://eurolab.example",
                country="DE",
                address="2 Lab Street",
                company_type="LAB_SUPPLIER",
                supplier_score=70,
                risk_score=10,
                risk_level="low",
                notes="Demo laboratory supplier.",
            ),
            SupplierCompany(
                name="Global Trading Demo",
                website="https://globaltrading.example",
                country="NL",
                company_type="TRADER_BROKER",
                supplier_score=35,
                risk_score=30,
                risk_level="unknown",
                notes="Demo trader requiring verification.",
            ),
        ]
        for supplier in suppliers:
            supplier.contacts.append(
                SupplierContact(
                    channel="email",
                    value=f"sales@{supplier.website.replace('https://', '')}",
                    source_url=f"{supplier.website}/contact",
                    evidence_text="Official public business inquiry contact listed on supplier website.",
                    is_primary=True,
                )
            )

        db.add_all([user, ethanol, water, *suppliers])
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            print("Demo data already exists (substances/suppliers).")
            return

        campaign = RfqCampaign(
            substance_id=ethanol.id,
            quantity="100 kg",
            destination_country="Poland",
            required_grade="technical grade",
            intended_use="lawful industrial validation",
            requirements={"documents": ["COA", "SDS"], "incoterms": ["EXW", "DAP"]},
            status="active",
            auto_send_enabled=False,
            created_by=user.id,
        )
        db.add(campaign)
        db.flush()

        outbound_1 = OutboundMessage(
            campaign_id=campaign.id,
            company_id=suppliers[0].id,
            contact_id=suppliers[0].contacts[0].id,
            channel="email",
            subject="RFQ: Ethanol / CAS 64-17-5 / 100 kg",
            body="Demo RFQ draft asking for COA, SDS, MOQ, lead time, Incoterms and compliance status.",
            status="requires_approval",
            policy_decision="REQUIRES_APPROVAL",
            policy_reasons=["Demo campaign auto-send disabled."],
            approval_required=True,
        )
        outbound_2 = OutboundMessage(
            campaign_id=campaign.id,
            company_id=suppliers[1].id,
            contact_id=suppliers[1].contacts[0].id,
            channel="email",
            subject="RFQ: Ethanol / CAS 64-17-5 / 100 kg",
            body="Demo RFQ draft.",
            status="draft",
            policy_decision="DRAFT_ONLY",
            policy_reasons=["Demo draft."],
            approval_required=True,
        )
        inbound = InboundMessage(
            company_id=suppliers[0].id,
            campaign_id=campaign.id,
            channel="email",
            from_address=suppliers[0].contacts[0].value,
            subject="Re: RFQ Ethanol",
            body="CAS 64-17-5 confirmed. Price: USD 12.50/kg EXW. MOQ: 25 kg. Lead time: 14 days. COA and SDS available. Payment: TT.",
            received_at=datetime.now(timezone.utc),
            parsed=True,
        )
        db.add_all([outbound_1, outbound_2, inbound])
        db.flush()

        quote = Quote(
            company_id=suppliers[0].id,
            substance_id=ethanol.id,
            campaign_id=campaign.id,
            quantity="25 kg",
            price=Decimal("12.50"),
            currency="USD",
            unit="kg",
            incoterms="EXW",
            lead_time="14 days",
            moq="25 kg",
            payment_terms="TT",
            coa_available=True,
            sds_available=True,
            confidence=Decimal("0.75"),
            status="parsed",
            extracted_from_message_id=inbound.id,
        )
        db.add(quote)
        AuditLogService(db).log("demo_seeded", "campaign", campaign.id, {"suppliers": len(suppliers)})
        db.commit()
        print("Demo data seeded. Login: demo@example.com / ChangeMe123!")


if __name__ == "__main__":
    seed()
