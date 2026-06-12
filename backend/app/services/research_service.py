"""Substance Research Service — builds and maintains the research dossier
for each substance: supplier interactions, production analysis, Incoterms comparison."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.research import ProductionAnalysis, SubstanceResearch, SupplierInteraction
from app.db.models.substance import Substance
from app.db.models.supplier import SupplierCompany
from app.schemas.research import (
    INCOTERMS_BY_TRANSPORT,
    IncotermsComparisonResponse,
    IncotermsComparisonRow,
    ProductionAnalysisCreate,
    ProductionMethodRead,
    ResearchDossierResponse,
    SubstanceResearchRead,
    SupplierInteractionCreate,
    SupplierInteractionRead,
)
from app.services.audit_log import AuditLogService
from app.services.production_analyzer import ProductionAnalyzer

logger = logging.getLogger(__name__)


class ResearchService:
    """Manages the per-substance research dossier."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditLogService(db)
        self.analyzer = ProductionAnalyzer(db)

    # ── Dossier management ──

    def get_or_create_dossier(self, substance_id: str) -> SubstanceResearch:
        """Get existing research dossier or create a new one."""
        research = self.db.scalar(
            select(SubstanceResearch)
            .options(
                selectinload(SubstanceResearch.interactions),
                selectinload(SubstanceResearch.production_analyses),
            )
            .where(SubstanceResearch.substance_id == substance_id)
        )
        if research:
            return research

        substance = self.db.get(Substance, substance_id)
        if not substance:
            raise ValueError(f"Substance {substance_id} not found")

        research = SubstanceResearch(substance_id=substance_id, status="active")
        self.db.add(research)
        self.db.flush()
        self.audit.log("research_dossier_created", "substance_research", research.id, {"substance_id": substance_id})
        return research

    def get_dossier(self, substance_id: str) -> ResearchDossierResponse:
        """Get full research dossier for a substance."""
        research = self.get_or_create_dossier(substance_id)
        substance = self.db.get(Substance, substance_id)
        if not substance:
            raise ValueError(f"Substance {substance_id} not found")

        interactions = []
        for interaction in research.interactions or []:
            interactions.append(SupplierInteractionRead(
                id=interaction.id,
                supplier_id=interaction.supplier_id,
                supplier_name=interaction.supplier_name or "",
                supplier_country=interaction.supplier_country or "",
                supplier_type=interaction.supplier_type or "",
                contact_channel=interaction.contact_channel or "",
                contact_person=interaction.contact_person or "",
                contact_value=interaction.contact_value or "",
                outreach_date=interaction.outreach_date or "",
                response_date=interaction.response_date or "",
                response_received=interaction.response_received or False,
                response_summary=interaction.response_summary or "",
                price_per_unit=interaction.price_per_unit,
                currency=interaction.currency or "USD",
                unit=interaction.unit or "kg",
                moq=interaction.moq or "",
                incoterms_offered=list(interaction.incoterms_offered or []),
                payment_terms=interaction.payment_terms or "",
                lead_time=interaction.lead_time or "",
                sample_available=interaction.sample_available or False,
                coa_available=interaction.coa_available or False,
                sds_available=interaction.sds_available or False,
                reach_registered=interaction.reach_registered or False,
                packaging_options=list(interaction.packaging_options or []),
                transport_modes_available=list(interaction.transport_modes_available or []),
                status=interaction.status or "contacted",
                rating=interaction.rating or 0,
                notes=interaction.notes or "",
                follow_up_needed=interaction.follow_up_needed or False,
            ))

        analyses = []
        for pa in research.production_analyses or []:
            analyses.append(ProductionMethodRead(
                id=pa.id,
                method_name=pa.method_name or "",
                method_description=pa.method_description or "",
                yield_percentage=pa.yield_percentage,
                difficulty_level=pa.difficulty_level or "moderate",
                equipment_needed=list(pa.equipment_needed or []),
                sub_products=list(pa.sub_products or []),
                raw_materials_cost=pa.raw_materials_cost,
                equipment_amortization=pa.equipment_amortization,
                labor_cost_estimate=pa.labor_cost_estimate,
                utilities_cost_estimate=pa.utilities_cost_estimate,
                total_production_cost_per_kg=pa.total_production_cost_per_kg,
                currency=pa.currency or "USD",
                safety_notes=pa.safety_notes or "",
                waste_disposal_notes=pa.waste_disposal_notes or "",
                permits_needed=list(pa.permits_needed or []),
            ))

        research_read = SubstanceResearchRead(
            id=research.id,
            substance_id=research.substance_id,
            substance_name=substance.primary_name or substance.cas,
            substance_cas=substance.cas,
            status=research.status or "active",
            total_suppliers_contacted=research.total_suppliers_contacted or 0,
            total_responses=research.total_responses or 0,
            total_quotes_received=research.total_quotes_received or 0,
            best_price=research.best_price,
            best_price_currency=research.best_price_currency or "USD",
            best_price_incoterms=research.best_price_incoterms or "",
            best_price_supplier_id=research.best_price_supplier_id,
            tags=list(research.tags or []),
            research_notes=research.research_notes or "",
            interactions=interactions,
            production_analyses=analyses,
        )

        return ResearchDossierResponse(
            substance_id=substance_id,
            substance_name=substance.primary_name or substance.cas,
            substance_cas=substance.cas,
            research=research_read,
            incoterms_guide=INCOTERMS_BY_TRANSPORT,
        )

    # ── Supplier interactions ──

    def add_interaction(self, substance_id: str, data: SupplierInteractionCreate) -> SupplierInteractionRead:
        """Log a supplier contact/interaction for this substance."""
        research = self.get_or_create_dossier(substance_id)

        # Try to find existing supplier by name
        supplier_id = None
        if data.supplier_name:
            existing = self.db.scalar(
                select(SupplierCompany).where(SupplierCompany.name.ilike(f"%{data.supplier_name}%"))
            )
            if existing:
                supplier_id = existing.id

        interaction = SupplierInteraction(
            research_id=research.id,
            supplier_id=supplier_id,
            supplier_name=data.supplier_name,
            supplier_country=data.supplier_country,
            supplier_type=data.supplier_type,
            contact_channel=data.contact_channel,
            contact_person=data.contact_person,
            contact_value=data.contact_value,
            outreach_date=datetime.now(timezone.utc).isoformat(),
            response_date=datetime.now(timezone.utc).isoformat() if data.response_received else None,
            response_received=data.response_received,
            response_summary=data.response_summary,
            price_per_unit=data.price_per_unit,
            currency=data.currency,
            unit=data.unit,
            moq=data.moq,
            incoterms_offered=data.incoterms_offered,
            payment_terms=data.payment_terms,
            lead_time=data.lead_time,
            sample_available=data.sample_available,
            coa_available=data.coa_available,
            sds_available=data.sds_available,
            reach_registered=data.reach_registered,
            packaging_options=data.packaging_options,
            transport_modes_available=data.transport_modes_available,
            status=data.status,
            rating=data.rating,
            notes=data.notes,
        )
        self.db.add(interaction)

        # Update research summary stats
        research.total_suppliers_contacted = (research.total_suppliers_contacted or 0) + 1
        if data.response_received:
            research.total_responses = (research.total_responses or 0) + 1
        if data.price_per_unit:
            research.total_quotes_received = (research.total_quotes_received or 0) + 1
            if research.best_price is None or data.price_per_unit < research.best_price:
                research.best_price = data.price_per_unit
                research.best_price_currency = data.currency
                research.best_price_incoterms = (data.incoterms_offered or ["EXW"])[0]
                research.best_price_supplier_id = supplier_id

        self.db.flush()
        self.audit.log(
            "supplier_interaction_logged",
            "supplier_interaction",
            interaction.id,
            {"substance_id": substance_id, "supplier_name": data.supplier_name, "status": data.status},
        )

        return SupplierInteractionRead(
            id=interaction.id,
            supplier_id=interaction.supplier_id,
            supplier_name=interaction.supplier_name or "",
            supplier_country=interaction.supplier_country or "",
            supplier_type=interaction.supplier_type or "",
            contact_channel=interaction.contact_channel or "",
            contact_person=interaction.contact_person or "",
            contact_value=interaction.contact_value or "",
            outreach_date=interaction.outreach_date or "",
            response_date=interaction.response_date or "",
            response_received=interaction.response_received or False,
            response_summary=interaction.response_summary or "",
            price_per_unit=interaction.price_per_unit,
            currency=interaction.currency or "USD",
            unit=interaction.unit or "kg",
            moq=interaction.moq or "",
            incoterms_offered=list(interaction.incoterms_offered or []),
            payment_terms=interaction.payment_terms or "",
            lead_time=interaction.lead_time or "",
            sample_available=interaction.sample_available or False,
            coa_available=interaction.coa_available or False,
            sds_available=interaction.sds_available or False,
            reach_registered=interaction.reach_registered or False,
            packaging_options=list(interaction.packaging_options or []),
            transport_modes_available=list(interaction.transport_modes_available or []),
            status=interaction.status or "contacted",
            rating=interaction.rating or 0,
            notes=interaction.notes or "",
            follow_up_needed=interaction.follow_up_needed or False,
        )

    # ── Production analysis ──

    def analyze_production(self, substance_id: str, payload: ProductionAnalysisCreate | None = None) -> list[ProductionMethodRead]:
        """Run production analysis for a substance and save results."""
        research = self.get_or_create_dossier(substance_id)
        substance = self.db.get(Substance, substance_id)
        if not substance:
            raise ValueError(f"Substance {substance_id} not found")

        # Run the analyzer
        methods = self.analyzer.analyze(substance)

        # Save to DB
        saved = []
        for method in methods:
            # Only save if this method doesn't already exist
            existing = self.db.scalar(
                select(ProductionAnalysis).where(
                    ProductionAnalysis.research_id == research.id,
                    ProductionAnalysis.method_name == method["method_name"],
                )
            )
            if existing:
                saved.append(existing)
                continue

            pa = ProductionAnalysis(
                research_id=research.id,
                method_name=method.get("method_name", ""),
                method_description=method.get("method_description", ""),
                yield_percentage=method.get("yield_percentage"),
                difficulty_level=method.get("difficulty_level"),
                equipment_needed=method.get("equipment_needed", []),
                sub_products=method.get("sub_products", []),
                raw_materials_cost=method.get("raw_materials_cost"),
                equipment_amortization=method.get("equipment_amortization"),
                labor_cost_estimate=method.get("labor_cost_estimate"),
                utilities_cost_estimate=method.get("utilities_cost_estimate"),
                total_production_cost_per_kg=method.get("total_production_cost_per_kg"),
                currency=method.get("currency", "USD"),
                safety_notes=method.get("safety_notes", ""),
                waste_disposal_notes=method.get("waste_disposal_notes", ""),
                permits_needed=method.get("permits_needed", []),
            )
            self.db.add(pa)
            saved.append(pa)

        self.db.flush()
        self.audit.log(
            "production_analysis_run",
            "substance_research",
            research.id,
            {"substance_id": substance_id, "methods_found": len(methods)},
        )

        return [
            ProductionMethodRead(
                id=pa.id,
                method_name=pa.method_name or "",
                method_description=pa.method_description or "",
                yield_percentage=pa.yield_percentage,
                difficulty_level=pa.difficulty_level or "moderate",
                equipment_needed=list(pa.equipment_needed or []),
                sub_products=list(pa.sub_products or []),
                raw_materials_cost=pa.raw_materials_cost,
                equipment_amortization=pa.equipment_amortization,
                labor_cost_estimate=pa.labor_cost_estimate,
                utilities_cost_estimate=pa.utilities_cost_estimate,
                total_production_cost_per_kg=pa.total_production_cost_per_kg,
                currency=pa.currency or "USD",
                safety_notes=pa.safety_notes or "",
                waste_disposal_notes=pa.waste_disposal_notes or "",
                permits_needed=list(pa.permits_needed or []),
            )
            for pa in saved
        ]

    # ── Incoterms comparison ──

    def compare_incoterms(self, substance_id: str) -> IncotermsComparisonResponse:
        """Generate Incoterms comparison across all transport modes for this substance."""
        rows: list[IncotermsComparisonRow] = []
        all_incoterms_seen: set[str] = set()

        for transport_mode, data in INCOTERMS_BY_TRANSPORT.items():
            for incoterms, resp in data["responsibility"].items():
                if incoterms not in all_incoterms_seen:
                    all_incoterms_seen.add(incoterms)
                    rows.append(IncotermsComparisonRow(
                        incoterms=incoterms,
                        transport_modes=[transport_mode],
                        export_clearance=resp.get("export_clearance", ""),
                        freight=resp.get("freight", ""),
                        insurance=resp.get("insurance", ""),
                        import_clearance=resp.get("import_clearance", ""),
                        unloading=resp.get("unloading", ""),
                        best_for=transport_mode,
                    ))
                else:
                    # Add transport mode to existing row
                    for row in rows:
                        if row.incoterms == incoterms:
                            row.transport_modes.append(transport_mode)

        # Sort by risk/complexity (buyer responsible = higher risk)
        def risk_order(row: IncotermsComparisonRow) -> int:
            buyer_count = sum(1 for v in [
                row.export_clearance, row.freight, row.insurance,
                row.import_clearance, row.unloading,
            ] if v == "buyer")
            return buyer_count

        rows.sort(key=risk_order)

        return IncotermsComparisonResponse(substance_id=substance_id, rows=rows)
