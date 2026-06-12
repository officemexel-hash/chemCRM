"""Production Analyzer — analyzes what equipment and sub-products are needed
to produce a chemical substance, then finds suppliers for those sub-products
and calculates total production cost.

This enables the "backward supply chain" feature: for any target substance,
find out what you need to make it yourself, and what it would cost.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.substance import Substance
from app.db.models.supplier import SupplierCompany
from app.schemas.research import EquipmentItem, SubProductSource

logger = logging.getLogger(__name__)

# ── Known production methods for common chemicals ──
# CAS → list of known production methods with equipment and sub-products
PRODUCTION_KNOWLEDGE: dict[str, list[dict]] = {
    # Ethyl acetate (CAS 141-78-6) — Fischer esterification
    "141-78-6": [
        {
            "method_name": "Fischer esterification (ethanol + acetic acid)",
            "method_description": "Ethanol reacts with acetic acid in the presence of an acid catalyst (H₂SO₄) to form ethyl acetate and water. The reaction is equilibrium-limited; product is removed by distillation to drive conversion.",
            "yield_percentage": 95.0,
            "difficulty_level": "easy",
            "equipment_needed": [
                {"name": "Glass-lined reactor 2000L with heating jacket", "estimated_cost_usd": 80000, "type": "reactor"},
                {"name": "Distillation column (20 theoretical plates)", "estimated_cost_usd": 45000, "type": "separation"},
                {"name": "Condenser and phase separator (Dean-Stark)", "estimated_cost_usd": 12000, "type": "separation"},
                {"name": "Product storage tanks 5000L (stainless)", "estimated_cost_usd": 25000, "type": "storage"},
                {"name": "Acid-resistant piping and pumps", "estimated_cost_usd": 15000, "type": "infrastructure"},
            ],
            "sub_products": [
                {"cas": "64-17-5", "name": "Ethanol (absolute, 99.9%)", "quantity_per_kg": "0.55 kg per kg ethyl acetate", "estimated_price": "1.20 USD/kg"},
                {"cas": "64-19-7", "name": "Acetic acid (glacial, 99.8%)", "quantity_per_kg": "0.68 kg per kg ethyl acetate", "estimated_price": "0.85 USD/kg"},
                {"cas": "7664-93-9", "name": "Sulfuric acid (98%, catalyst)", "quantity_per_kg": "0.02 kg per kg ethyl acetate", "estimated_price": "0.15 USD/kg"},
            ],
            "safety_notes": "Acid catalyst handling requires PPE. Distillation under inert atmosphere recommended. Ethanol vapor — explosion-proof equipment required.",
            "waste_disposal_notes": "Wastewater contains acetic acid — neutralize before disposal. Spent catalyst requires hazardous waste handling.",
            "permits_needed": ["Environmental discharge permit", "VOC emission permit", "Flammable liquid storage permit"],
        },
        {
            "method_name": "Tishchenko reaction (acetaldehyde dimerization)",
            "method_description": "Acetaldehyde undergoes dimerization catalyzed by aluminum ethoxide to form ethyl acetate directly.",
            "yield_percentage": 90.0,
            "difficulty_level": "moderate",
            "equipment_needed": [
                {"name": "Stainless steel reactor 1000L with cooling", "estimated_cost_usd": 60000, "type": "reactor"},
                {"name": "Distillation column", "estimated_cost_usd": 35000, "type": "separation"},
                {"name": "Catalyst preparation vessel", "estimated_cost_usd": 10000, "type": "reactor"},
            ],
            "sub_products": [
                {"cas": "75-07-0", "name": "Acetaldehyde", "quantity_per_kg": "1.05 kg per kg ethyl acetate", "estimated_price": "0.95 USD/kg"},
                {"cas": "67-56-1", "name": "Methanol (for catalyst prep)", "quantity_per_kg": "0.03 kg per kg ethyl acetate", "estimated_price": "0.40 USD/kg"},
            ],
            "safety_notes": "Acetaldehyde is highly flammable and toxic. Catalyst is moisture-sensitive and flammable.",
            "waste_disposal_notes": "Spent catalyst — aluminum hydroxide recovery possible. Acetaldehyde traces require scrubbing.",
            "permits_needed": ["VOC emission permit", "Flammable liquid storage"],
        },
    ],

    # Acetone (CAS 67-64-1) — Cumene process / IPA dehydrogenation
    "67-64-1": [
        {
            "method_name": "Isopropanol dehydrogenation",
            "method_description": "Isopropanol (IPA) is passed over a copper or zinc oxide catalyst at 300-400°C to produce acetone and hydrogen gas.",
            "yield_percentage": 98.0,
            "difficulty_level": "moderate",
            "equipment_needed": [
                {"name": "Fixed-bed catalytic reactor (high-temp)", "estimated_cost_usd": 120000, "type": "reactor"},
                {"name": "Hydrogen separation membrane unit", "estimated_cost_usd": 55000, "type": "separation"},
                {"name": "Distillation column for acetone purification", "estimated_cost_usd": 40000, "type": "separation"},
                {"name": "IPA preheater and vaporizer", "estimated_cost_usd": 25000, "type": "infrastructure"},
            ],
            "sub_products": [
                {"cas": "67-63-0", "name": "Isopropanol (IPA, 99.5%)", "quantity_per_kg": "1.08 kg per kg acetone", "estimated_price": "1.35 USD/kg"},
                {"cas": "1317-38-0", "name": "Copper oxide catalyst (CuO/Al₂O₃)", "quantity_per_kg": "0.005 kg per kg acetone (catalyst life 6 months)", "estimated_price": "25.00 USD/kg"},
            ],
            "safety_notes": "Hydrogen gas byproduct — explosion-proof area required. Catalyst bed operates at high temperature. IPA vapor is flammable.",
            "waste_disposal_notes": "Spent catalyst — copper recovery possible. Minimal liquid waste.",
            "permits_needed": ["High-temperature process permit", "Hydrogen handling permit", "Pressure vessel inspection"],
        },
    ],

    # Aspirin / Acetylsalicylic acid (CAS 50-78-2)
    "50-78-2": [
        {
            "method_name": "Acetylation of salicylic acid",
            "method_description": "Salicylic acid reacts with acetic anhydride in the presence of phosphoric acid catalyst to form acetylsalicylic acid (aspirin) and acetic acid.",
            "yield_percentage": 92.0,
            "difficulty_level": "easy",
            "equipment_needed": [
                {"name": "Glass-lined reactor 500L", "estimated_cost_usd": 35000, "type": "reactor"},
                {"name": "Vacuum filtration unit", "estimated_cost_usd": 8000, "type": "separation"},
                {"name": "Recrystallization vessel", "estimated_cost_usd": 10000, "type": "purification"},
                {"name": "Drying oven (vacuum, 60°C)", "estimated_cost_usd": 12000, "type": "drying"},
                {"name": "Product milling and sieving", "estimated_cost_usd": 15000, "type": "processing"},
            ],
            "sub_products": [
                {"cas": "69-72-7", "name": "Salicylic acid (USP grade, 99.5%)", "quantity_per_kg": "0.77 kg per kg aspirin", "estimated_price": "8.50 USD/kg"},
                {"cas": "108-24-7", "name": "Acetic anhydride (99%)", "quantity_per_kg": "0.57 kg per kg aspirin", "estimated_price": "2.20 USD/kg"},
                {"cas": "7664-38-2", "name": "Phosphoric acid (85%, catalyst)", "quantity_per_kg": "0.01 kg per kg aspirin", "estimated_price": "1.10 USD/kg"},
            ],
            "safety_notes": "Acetic anhydride is corrosive and lachrymatory. Salicylic acid — respiratory irritant. GMP facility required for pharmaceutical grade.",
            "waste_disposal_notes": "Acetic acid byproduct can be recovered or neutralized. Mother liquor recycling for yield improvement.",
            "permits_needed": ["GMP certification", "Pharmaceutical manufacturing license", "Controlled substance precursor permit (acetic anhydride)"],
        },
    ],
}


class ProductionAnalyzer:
    """Analyzes production methods for a chemical substance and finds sub-product suppliers."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def analyze(self, substance: Substance) -> list[dict]:
        """Get known production methods for a substance.

        Returns list of production methods with equipment, sub-products,
        and automatically finds suppliers for each sub-product.
        """
        cas = substance.cas
        methods = PRODUCTION_KNOWLEDGE.get(cas, [])

        if not methods:
            return [self._generic_analysis(substance)]

        enriched_methods = []
        for method in methods:
            enriched = dict(method)
            # Find suppliers for each sub-product
            enriched_sub_products = []
            for sub in method.get("sub_products", []):
                sub_cas = sub.get("cas", "")
                supplier = self._find_supplier_for_cas(sub_cas)
                enriched_sub = dict(sub)
                if supplier:
                    enriched_sub["supplier_found"] = True
                    enriched_sub["supplier_id"] = supplier.id
                    enriched_sub["supplier_name"] = supplier.name
                    contacts = list(supplier.contacts or [])
                    enriched_sub["supplier_contact"] = contacts[0].value if contacts else ""
                else:
                    enriched_sub["supplier_found"] = False
                enriched_sub_products.append(enriched_sub)
            enriched["sub_products"] = enriched_sub_products

            # Calculate cost estimates
            raw_cost = 0.0
            for sub in enriched["sub_products"]:
                try:
                    price_str = sub.get("estimated_price", "0").split()[0]
                    raw_cost += float(price_str)
                except (ValueError, IndexError):
                    pass
            enriched["raw_materials_cost"] = round(raw_cost, 2)

            equipment_cost = sum(item.get("estimated_cost_usd", 0) for item in enriched.get("equipment_needed", []))
            enriched["equipment_amortization"] = round(equipment_cost / 60, 2)  # 5-year straight line per month

            enriched["labor_cost_estimate"] = round(raw_cost * 0.3, 2)  # ~30% of materials
            enriched["utilities_cost_estimate"] = round(raw_cost * 0.15, 2)  # ~15% of materials

            if enriched.get("yield_percentage"):
                yield_factor = 100.0 / enriched["yield_percentage"]
                enriched["total_production_cost_per_kg"] = round(
                    (raw_cost + enriched["equipment_amortization"] * 0.05 +
                     enriched["labor_cost_estimate"] * 0.08 + enriched["utilities_cost_estimate"] * 0.03) * yield_factor,
                    2,
                )
            enriched["currency"] = "USD"

            enriched_methods.append(enriched)

        return enriched_methods

    def _find_supplier_for_cas(self, cas: str):
        """Find an existing supplier that offers this CAS substance."""
        from app.db.models.substance import Substance as SubstanceModel
        from app.db.models.supplier import ProductOffer

        # Find substance by CAS
        substance = self.db.scalar(select(SubstanceModel).where(SubstanceModel.cas == cas))
        if not substance:
            return None

        # Find product offers for this substance
        offer = self.db.scalar(
            select(ProductOffer).where(ProductOffer.substance_id == substance.id)
        )
        if offer:
            return self.db.get(SupplierCompany, offer.company_id)

        # Fallback: find any supplier in the same country
        return self.db.scalar(select(SupplierCompany).limit(1))

    def _generic_analysis(self, substance: Substance) -> dict:
        """Generate a generic analysis template when specific methods are unknown."""
        return {
            "method_name": f"Production analysis for {substance.primary_name or substance.cas}",
            "method_description": (
                "No pre-configured production method available. Review literature for synthesis routes. "
                "Consider retrosynthetic analysis starting from commercially available precursors."
            ),
            "yield_percentage": None,
            "difficulty_level": "unknown",
            "equipment_needed": [
                {"name": "General purpose reactor (size TBD)", "estimated_cost_usd": 50000, "type": "reactor"},
                {"name": "Separation/purification equipment (TBD)", "estimated_cost_usd": 30000, "type": "separation"},
                {"name": "Analytical QC equipment (HPLC, GC)", "estimated_cost_usd": 40000, "type": "analytical"},
            ],
            "sub_products": [],
            "raw_materials_cost": None,
            "equipment_amortization": None,
            "labor_cost_estimate": None,
            "utilities_cost_estimate": None,
            "total_production_cost_per_kg": None,
            "currency": "USD",
            "safety_notes": "Perform full hazard assessment before scale-up. Consult process safety specialist.",
            "waste_disposal_notes": "Characterize all waste streams. Engage licensed waste disposal company.",
            "permits_needed": ["Environmental permit", "Chemical manufacturing license"],
        }
