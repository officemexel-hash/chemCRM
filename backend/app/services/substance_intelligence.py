from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.campaign import RfqCampaign
from app.db.models.intelligence import SubstanceManufacturingAnalysis
from app.db.models.message import InboundMessage, OutboundMessage
from app.db.models.quote import Quote
from app.db.models.substance import Substance
from app.db.models.supplier import ProductOffer, SupplierCompany
from app.db.models.task import ManualTask
from app.schemas.substance_intelligence import (
    IncotermsTransportProfile,
    ManufacturingAnalysisRequest,
    SubstanceContactHistoryItem,
    SubstanceContactRecord,
    SubstanceManufacturingAnalysisRead,
    SubstanceProductOfferRecord,
    SubstanceProfileSummary,
    SubstanceQuoteTerms,
    SubstanceSourcingProfileRead,
    SubstanceSupplierRecord,
)
from app.services.audit_log import AuditLogService
from app.services.hs_code_service import INCOTERMS_MATRIX, TRANSPORT_INCOTERMS


class SubstanceIntelligenceService:
    """Build a substance-centered sourcing and manufacturing intelligence view."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def sourcing_profile(self, substance_id: str) -> SubstanceSourcingProfileRead:
        substance = self._load_substance(substance_id)
        campaigns = self._campaigns(substance_id)
        campaign_ids = [campaign.id for campaign in campaigns]
        quotes = self._quotes(substance_id)
        offers = self._offers(substance_id)
        outbound = self._outbound(campaign_ids)
        inbound = self._inbound(campaign_ids)

        supplier_ids = {
            quote.company_id for quote in quotes
        } | {
            offer.company_id for offer in offers
        } | {
            message.company_id for message in outbound
        } | {
            message.company_id for message in inbound
        }
        suppliers = self._suppliers(supplier_ids)

        quotes_by_supplier = _group_by_company(quotes)
        offers_by_supplier = _group_by_company(offers)
        outbound_by_supplier = _group_by_company(outbound)
        inbound_by_supplier = _group_by_company(inbound)

        supplier_records: list[SubstanceSupplierRecord] = []
        for supplier in suppliers:
            supplier_quotes = quotes_by_supplier.get(supplier.id, [])
            supplier_offers = offers_by_supplier.get(supplier.id, [])
            history = _history_items(
                supplier.id,
                outbound_by_supplier.get(supplier.id, []),
                inbound_by_supplier.get(supplier.id, []),
            )
            supplier_records.append(
                SubstanceSupplierRecord(
                    id=supplier.id,
                    name=supplier.name,
                    website=supplier.website,
                    country=supplier.country,
                    company_type=supplier.company_type,
                    supplier_score=supplier.supplier_score,
                    risk_score=supplier.risk_score,
                    risk_level=supplier.risk_level,
                    contacts=[
                        SubstanceContactRecord(
                            id=contact.id,
                            channel=contact.channel,
                            value=contact.value,
                            contact_person=contact.contact_person,
                            source_url=contact.source_url,
                            evidence_text=contact.evidence_text,
                            consent_status=contact.consent_status,
                        )
                        for contact in supplier.contacts
                    ],
                    quotes=[_quote_terms(quote) for quote in supplier_quotes],
                    product_offers=[_offer_record(offer) for offer in supplier_offers],
                    contact_history=history,
                    latest_contact_at=_latest_history_timestamp(history),
                    quoted_packaging=sorted({quote.packaging for quote in supplier_quotes if quote.packaging}),
                    quoted_incoterms=sorted({quote.incoterms for quote in supplier_quotes if quote.incoterms}),
                )
            )

        summary = SubstanceProfileSummary(
            id=substance.id,
            cas=substance.cas,
            primary_name=substance.primary_name,
            regulatory_status=substance.regulatory_status,
            requires_manual_review=substance.requires_manual_review,
            supplier_count=len(supplier_records),
            contact_count=sum(len(item.contacts) for item in supplier_records),
            quote_count=len(quotes),
            offer_count=len(offers),
            countries=sorted({supplier.country for supplier in suppliers if supplier.country}),
            best_price=_best_price(quotes),
            best_price_currency=_best_price_field(quotes, "currency"),
            best_price_unit=_best_price_field(quotes, "unit"),
        )
        return SubstanceSourcingProfileRead(
            summary=summary,
            suppliers=supplier_records,
            incoterms_by_transport=_incoterms_profiles(),
            open_questions=_open_questions(substance, supplier_records),
        )

    def analyze_manufacturing(
        self, substance_id: str, payload: ManufacturingAnalysisRequest
    ) -> SubstanceManufacturingAnalysisRead:
        substance = self._load_substance(substance_id)
        template = _safe_template_for(substance)
        blocked_reasons = _manufacturing_review_reasons(substance)
        status = "manual_review_required" if blocked_reasons else "draft_feasibility"

        input_materials = template["input_materials"] if payload.include_raw_material_sourcing and not blocked_reasons else []
        sourcing_queries = _input_material_queries(input_materials) if input_materials else []
        cost_model = _cost_model(payload, template, input_materials, blocked_reasons)

        result = SubstanceManufacturingAnalysisRead(
            substance_id=substance.id,
            target_quantity=payload.target_quantity,
            target_grade=payload.target_grade,
            intended_use=payload.intended_use,
            destination_country=payload.destination_country,
            status=status,
            route_type=template["route_type"] if not blocked_reasons else None,
            process_overview=template["process_overview"] if not blocked_reasons else None,
            required_equipment=template["required_equipment"] if not blocked_reasons else [],
            input_materials=input_materials,
            cost_drivers=template["cost_drivers"] if not blocked_reasons else [],
            cost_model=cost_model,
            sourcing_queries=sourcing_queries,
            compliance_notes=template["compliance_notes"] + _common_compliance_notes(),
            safety_notes=template["safety_notes"] + _common_safety_notes(),
            blocked_reasons=blocked_reasons,
            confidence=Decimal("0.42") if not blocked_reasons else Decimal("0.12"),
        )

        if payload.save_to_crm:
            analysis = SubstanceManufacturingAnalysis(
                substance_id=result.substance_id,
                target_quantity=result.target_quantity,
                target_grade=result.target_grade,
                intended_use=result.intended_use,
                destination_country=result.destination_country,
                status=result.status,
                route_type=result.route_type,
                process_overview=result.process_overview,
                required_equipment=result.required_equipment,
                input_materials=result.input_materials,
                cost_drivers=result.cost_drivers,
                cost_model=result.cost_model,
                sourcing_queries=result.sourcing_queries,
                compliance_notes=result.compliance_notes,
                safety_notes=result.safety_notes,
                blocked_reasons=result.blocked_reasons,
                confidence=result.confidence,
            )
            self.db.add(analysis)
            self.db.flush()
            if payload.create_raw_material_tasks and result.sourcing_queries:
                self._create_raw_material_tasks(analysis.id, result.sourcing_queries)
            AuditLogService(self.db).log(
                "substance_manufacturing_analysis_created",
                "substance",
                substance.id,
                {
                    "analysis_id": analysis.id,
                    "status": analysis.status,
                    "blocked_reasons": analysis.blocked_reasons,
                    "raw_material_queries": len(result.sourcing_queries),
                },
            )
            self.db.commit()
            self.db.refresh(analysis)
            return _analysis_read(analysis)

        return result

    def list_manufacturing_analyses(self, substance_id: str) -> list[SubstanceManufacturingAnalysisRead]:
        self._load_substance(substance_id)
        analyses = list(
            self.db.scalars(
                select(SubstanceManufacturingAnalysis)
                .where(SubstanceManufacturingAnalysis.substance_id == substance_id)
                .order_by(SubstanceManufacturingAnalysis.created_at.desc())
            )
        )
        return [_analysis_read(item) for item in analyses]

    def _load_substance(self, substance_id: str) -> Substance:
        substance = self.db.scalar(
            select(Substance)
            .options(selectinload(Substance.regulatory_flags))
            .where(Substance.id == substance_id)
        )
        if substance is None:
            raise ValueError("Substance not found")
        return substance

    def _campaigns(self, substance_id: str) -> list[RfqCampaign]:
        return list(self.db.scalars(select(RfqCampaign).where(RfqCampaign.substance_id == substance_id)))

    def _quotes(self, substance_id: str) -> list[Quote]:
        return list(self.db.scalars(select(Quote).where(Quote.substance_id == substance_id)))

    def _offers(self, substance_id: str) -> list[ProductOffer]:
        return list(self.db.scalars(select(ProductOffer).where(ProductOffer.substance_id == substance_id)))

    def _outbound(self, campaign_ids: list[str]) -> list[OutboundMessage]:
        if not campaign_ids:
            return []
        return list(self.db.scalars(select(OutboundMessage).where(OutboundMessage.campaign_id.in_(campaign_ids))))

    def _inbound(self, campaign_ids: list[str]) -> list[InboundMessage]:
        if not campaign_ids:
            return []
        return list(self.db.scalars(select(InboundMessage).where(InboundMessage.campaign_id.in_(campaign_ids))))

    def _suppliers(self, supplier_ids: set[str]) -> list[SupplierCompany]:
        if not supplier_ids:
            return []
        return list(
            self.db.scalars(
                select(SupplierCompany)
                .options(selectinload(SupplierCompany.contacts))
                .where(SupplierCompany.id.in_(supplier_ids))
                .order_by(SupplierCompany.supplier_score.desc(), SupplierCompany.name.asc())
            )
        )

    def _create_raw_material_tasks(self, analysis_id: str, sourcing_queries: list[dict]) -> None:
        for item in sourcing_queries[:12]:
            material = item.get("material") or "input material"
            query = item.get("query") or material
            task = ManualTask(
                task_type="raw_material_sourcing_review",
                title=f"Review input material sourcing: {material}",
                description=f"Validate suppliers and quotes for input material query: {query}",
                related_object_type="substance_manufacturing_analysis",
                related_object_id=analysis_id,
                status="open",
            )
            self.db.add(task)


def _group_by_company(items) -> dict[str, list]:
    grouped: dict[str, list] = {}
    for item in items:
        grouped.setdefault(item.company_id, []).append(item)
    return grouped


def _quote_terms(quote: Quote) -> SubstanceQuoteTerms:
    return SubstanceQuoteTerms(
        id=quote.id,
        campaign_id=quote.campaign_id,
        quantity=quote.quantity,
        price=quote.price,
        currency=quote.currency,
        unit=quote.unit,
        incoterms=quote.incoterms,
        transport_mode=_transport_modes_for_incoterm(quote.incoterms),
        lead_time=quote.lead_time,
        moq=quote.moq,
        payment_terms=quote.payment_terms,
        packaging=quote.packaging,
        coa_available=quote.coa_available,
        sds_available=quote.sds_available,
        reach_status=quote.reach_status,
        adr_class=quote.adr_class,
        un_number=quote.un_number,
        hs_code=quote.hs_code,
        confidence=quote.confidence,
        status=quote.status,
    )


def _offer_record(offer: ProductOffer) -> SubstanceProductOfferRecord:
    return SubstanceProductOfferRecord(
        id=offer.id,
        source_url=offer.source_url,
        listed_name=offer.listed_name,
        listed_cas=offer.listed_cas,
        grade=offer.grade,
        purity=offer.purity,
        moq=offer.moq,
        price_text=offer.price_text,
        currency=offer.currency,
        last_seen_at=offer.last_seen_at,
    )


def _history_items(company_id: str, outbound: list[OutboundMessage], inbound: list[InboundMessage]) -> list[SubstanceContactHistoryItem]:
    items: list[SubstanceContactHistoryItem] = []
    for message in outbound:
        items.append(
            SubstanceContactHistoryItem(
                id=message.id,
                direction="outbound",
                company_id=company_id,
                channel=message.channel,
                subject=message.subject,
                status=message.status,
                policy_decision=message.policy_decision,
                timestamp=message.sent_at or message.approved_at or message.created_at,
                summary=_short_text(message.body),
            )
        )
    for message in inbound:
        items.append(
            SubstanceContactHistoryItem(
                id=message.id,
                direction="inbound",
                company_id=company_id,
                channel=message.channel,
                subject=message.subject,
                status="parsed" if message.parsed else "received",
                timestamp=message.received_at,
                summary=_short_text(message.body),
            )
        )
    fallback = datetime.min.replace(tzinfo=timezone.utc)
    return sorted(items, key=lambda item: item.timestamp or fallback, reverse=True)


def _latest_history_timestamp(history: list[SubstanceContactHistoryItem]):
    timestamps = [item.timestamp for item in history if item.timestamp]
    return max(timestamps) if timestamps else None


def _short_text(value: str | None) -> str | None:
    if not value:
        return None
    normalized = " ".join(value.split())
    return normalized[:220]


def _best_price(quotes: list[Quote]) -> Decimal | None:
    prices = [quote.price for quote in quotes if quote.price is not None]
    return min(prices) if prices else None


def _best_price_field(quotes: list[Quote], field: str) -> str | None:
    priced = [quote for quote in quotes if quote.price is not None]
    if not priced:
        return None
    best = min(priced, key=lambda quote: quote.price)
    return getattr(best, field)


def _incoterms_profiles() -> list[IncotermsTransportProfile]:
    profiles: list[IncotermsTransportProfile] = []
    for mode, incoterms in TRANSPORT_INCOTERMS.items():
        profiles.append(
            IncotermsTransportProfile(
                transport_mode=mode,
                recommended_incoterms=incoterms,
                responsibility_matrix={
                    term: INCOTERMS_MATRIX.get(term, {}) for term in incoterms
                },
            )
        )
    return profiles


def _transport_modes_for_incoterm(incoterms: str | None) -> str | None:
    if not incoterms:
        return None
    term = incoterms.upper()
    modes = [mode for mode, terms in TRANSPORT_INCOTERMS.items() if term in terms]
    return ", ".join(modes) if modes else "check_incoterms_context"


def _open_questions(substance: Substance, suppliers: list[SubstanceSupplierRecord]) -> list[str]:
    questions: list[str] = []
    if not substance.hs_code_suggested and not getattr(substance, "hs_code_confirmed", None):
        questions.append("Confirm HS code before customs or PO issuance.")
    if not suppliers:
        questions.append("No supplier records are linked to this substance yet.")
    if suppliers and not any(record.quotes for record in suppliers):
        questions.append("No parsed supplier quotes are available for comparison.")
    if suppliers and not any(record.quoted_packaging for record in suppliers):
        questions.append("Packaging terms are missing from supplier quotes.")
    if suppliers and not any(record.quoted_incoterms for record in suppliers):
        questions.append("Incoterms are missing from supplier quotes.")
    return questions


def _manufacturing_review_reasons(substance: Substance) -> list[str]:
    reasons: list[str] = []
    status = (substance.regulatory_status or "unknown").lower()
    if status in {"regulated", "restricted", "blocked"}:
        reasons.append(f"regulatory_status={status}; manufacturing analysis requires expert review")
    if substance.requires_manual_review:
        reasons.append("substance requires manual review before production feasibility analysis")
    for flag in substance.regulatory_flags or []:
        severity = (flag.severity or "").lower()
        if severity in {"critical", "high"}:
            reasons.append(f"regulatory flag requires review: {flag.flag_type or 'unknown'}")
    return reasons


def _safe_template_for(substance: Substance) -> dict:
    key = (substance.cas or "").strip()
    name = (substance.primary_name or "").lower()
    if key == "7732-18-5" or name == "water":
        return _water_template()
    if key == "64-17-5" or "ethanol" in name:
        return _ethanol_template()
    if "sodium carbonate" in name or key == "497-19-8":
        return _sodium_carbonate_template()
    return _generic_template(substance)


def _water_template() -> dict:
    return {
        "route_type": "purification and quality-controlled packaging",
        "process_overview": "High-level feasibility view for producing purified process water through pretreatment, purification, storage, QA release, and packaging. This is not a process recipe.",
        "required_equipment": [
            {"category": "pretreatment", "examples": ["particulate filtration", "softening or deionization module"]},
            {"category": "purification", "examples": ["reverse osmosis", "UV treatment", "polishing filtration"]},
            {"category": "storage", "examples": ["sanitary tanks", "recirculation loop"]},
            {"category": "quality", "examples": ["conductivity meter", "microbiological sampling workflow"]},
            {"category": "packaging", "examples": ["clean filling station", "labeling and batch records"]},
        ],
        "input_materials": [
            {"name": "municipal or industrial water feed", "role": "feedstock", "sourcing_queries": ["bulk industrial water supply", "process water utility provider"]},
            {"name": "filter media and cartridges", "role": "consumable", "sourcing_queries": ["industrial water filter cartridge supplier", "RO pretreatment media supplier"]},
            {"name": "packaging containers", "role": "packaging", "sourcing_queries": ["HDPE drum supplier", "IBC container supplier"]},
        ],
        "cost_drivers": _default_cost_drivers(),
        "compliance_notes": ["Confirm grade-specific requirements such as technical, purified, sterile, or pharma-grade water."],
        "safety_notes": ["Maintain contamination controls and batch traceability."],
    }


def _ethanol_template() -> dict:
    return {
        "route_type": "commodity-scale fermentation or petrochemical route assessment",
        "process_overview": "High-level feasibility view comparing procurement versus commodity production routes. Details are limited to equipment classes and cost drivers; no process parameters, yields, or operating instructions are provided.",
        "required_equipment": [
            {"category": "feedstock handling", "examples": ["bulk liquid storage", "metering and transfer systems"]},
            {"category": "conversion", "examples": ["industrial reactor or fermentation vessel", "process control system"]},
            {"category": "separation", "examples": ["distillation train", "dehydration or polishing system"]},
            {"category": "QA/QC", "examples": ["GC or equivalent assay workflow", "water content testing", "COA generation process"]},
            {"category": "packaging", "examples": ["drum or IBC filling line", "flammable liquid storage controls"]},
        ],
        "input_materials": [
            {"name": "carbohydrate feedstock or petrochemical feedstock", "role": "primary feedstock category", "sourcing_queries": ["industrial carbohydrate feedstock supplier", "chemical feedstock distributor"]},
            {"name": "process consumables", "role": "operating consumables", "sourcing_queries": ["industrial processing consumables supplier", "filtration aid supplier"]},
            {"name": "flammable liquid packaging", "role": "packaging", "sourcing_queries": ["UN approved steel drum supplier", "flammable liquid IBC supplier"]},
        ],
        "cost_drivers": _default_cost_drivers()
        + [{"name": "excise or alcohol-specific controls", "impact": "can dominate landed cost and documentation burden"}],
        "compliance_notes": ["Alcohol products can trigger excise, licensing, denaturing, storage, and transport requirements depending on country and use."],
        "safety_notes": ["Treat as flammable liquid; verify storage, ADR/DG transport, and insurance requirements."],
    }


def _sodium_carbonate_template() -> dict:
    return {
        "route_type": "commodity inorganic chemical route assessment",
        "process_overview": "High-level feasibility view for a commodity inorganic chemical. The analysis is limited to equipment classes, feedstock categories, and cost drivers.",
        "required_equipment": [
            {"category": "bulk solids handling", "examples": ["silos", "conveyors", "dust collection"]},
            {"category": "thermal or crystallization section", "examples": ["industrial kiln or crystallizer class equipment"]},
            {"category": "separation and drying", "examples": ["filter", "dryer", "screening"]},
            {"category": "packaging", "examples": ["bagging line", "bulk loading system"]},
        ],
        "input_materials": [
            {"name": "sodium source feedstock", "role": "feedstock category", "sourcing_queries": ["bulk sodium feedstock supplier", "industrial alkali raw material supplier"]},
            {"name": "carbonate source feedstock", "role": "feedstock category", "sourcing_queries": ["industrial carbonate feedstock supplier", "bulk limestone supplier"]},
            {"name": "industrial bags or big bags", "role": "packaging", "sourcing_queries": ["chemical FIBC supplier", "industrial bag supplier"]},
        ],
        "cost_drivers": _default_cost_drivers(),
        "compliance_notes": ["Validate dust control, worker exposure, and product grade requirements."],
        "safety_notes": ["Review dust handling, eye/skin exposure, and bulk storage controls."],
    }


def _generic_template(substance: Substance) -> dict:
    name = substance.primary_name or substance.cas
    return {
        "route_type": "manual feasibility scoping",
        "process_overview": f"High-level procurement-versus-manufacture scoping for {name}. Detailed chemistry, synthesis conditions, yields, catalysts, and process instructions require expert review and are not generated by this MVP.",
        "required_equipment": [
            {"category": "raw material receiving", "examples": ["qualified receiving area", "batch traceability workflow"]},
            {"category": "processing", "examples": ["appropriate industrial processing equipment to be specified by process engineer"]},
            {"category": "quality", "examples": ["COA workflow", "SDS review", "retention sample process"]},
            {"category": "packaging", "examples": ["compatible packaging selected after hazard review"]},
        ],
        "input_materials": [
            {"name": "qualified input material categories", "role": "to be specified", "sourcing_queries": [f"{name} input material supplier", f"{name} contract manufacturing feasibility"]},
            {"name": "compatible packaging", "role": "packaging", "sourcing_queries": ["chemical packaging supplier", "UN approved packaging supplier"]},
        ],
        "cost_drivers": _default_cost_drivers(),
        "compliance_notes": ["Manual expert review is required before treating any route or material list as actionable."],
        "safety_notes": ["Do not use this high-level scoping as a production instruction."],
    }


def _default_cost_drivers() -> list[dict]:
    return [
        {"name": "input materials", "impact": "quoted raw material or semi-product cost"},
        {"name": "utilities", "impact": "energy, water, gas, cooling, compressed air"},
        {"name": "labor and QA", "impact": "batch release, documentation, COA/SDS handling"},
        {"name": "waste treatment", "impact": "effluent, residues, contaminated packaging"},
        {"name": "packaging", "impact": "drums, IBCs, bags, labels, pallets"},
        {"name": "logistics", "impact": "Incoterms, transport mode, insurance, duty, VAT"},
        {"name": "compliance", "impact": "permits, audits, storage class, dangerous goods handling"},
    ]


def _common_compliance_notes() -> list[str]:
    return [
        "Confirm lawful intended use, destination rules, import/export controls, and document requirements before sourcing inputs.",
        "Cost model is procurement screening only and does not replace regulatory, customs, EHS, or process-engineering review.",
    ]


def _common_safety_notes() -> list[str]:
    return [
        "No synthesis recipe, process parameters, yields, or bypass guidance are provided.",
        "Create raw-material supplier tasks only for lawful, documented, business-to-business sourcing.",
    ]


def _input_material_queries(input_materials: list[dict]) -> list[dict]:
    queries: list[dict] = []
    for material in input_materials:
        for query in material.get("sourcing_queries", []):
            queries.append(
                {
                    "material": material.get("name"),
                    "role": material.get("role"),
                    "query": query,
                    "source_reason": "input material cost model",
                    "requires_manual_review": True,
                }
            )
    return queries


def _cost_model(payload: ManufacturingAnalysisRequest, template: dict, input_materials: list[dict], blocked_reasons: list[str]) -> dict:
    return {
        "method": "screening_only",
        "target_quantity": payload.target_quantity,
        "target_grade": payload.target_grade,
        "destination_country": payload.destination_country,
        "route_type": None if blocked_reasons else template["route_type"],
        "line_items": [
            {"category": "input_materials", "status": "needs_quotes", "basis": [item.get("name") for item in input_materials]},
            {"category": "utilities", "status": "estimate_required", "basis": "site-specific"},
            {"category": "labor_qa", "status": "estimate_required", "basis": "site-specific"},
            {"category": "packaging", "status": "needs_quotes", "basis": "quote packaging and transport mode"},
            {"category": "logistics_customs", "status": "needs_quotes", "basis": "Incoterms, transport mode, duty, VAT"},
            {"category": "compliance_ehs", "status": "manual_review", "basis": "substance, destination, intended use"},
        ],
        "calculation_rule": "total_estimated_cost = input_materials + utilities + labor_qa + packaging + logistics_customs + compliance_ehs + contingency",
        "contingency_recommendation": "Add a documented contingency range after supplier quotes and EHS review.",
        "blocked": bool(blocked_reasons),
    }


def _analysis_read(analysis: SubstanceManufacturingAnalysis) -> SubstanceManufacturingAnalysisRead:
    return SubstanceManufacturingAnalysisRead(
        id=analysis.id,
        substance_id=analysis.substance_id,
        target_quantity=analysis.target_quantity,
        target_grade=analysis.target_grade,
        intended_use=analysis.intended_use,
        destination_country=analysis.destination_country,
        status=analysis.status,
        route_type=analysis.route_type,
        process_overview=analysis.process_overview,
        required_equipment=analysis.required_equipment or [],
        input_materials=analysis.input_materials or [],
        cost_drivers=analysis.cost_drivers or [],
        cost_model=analysis.cost_model or {},
        sourcing_queries=analysis.sourcing_queries or [],
        compliance_notes=analysis.compliance_notes or [],
        safety_notes=analysis.safety_notes or [],
        blocked_reasons=analysis.blocked_reasons or [],
        confidence=analysis.confidence,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
    )
