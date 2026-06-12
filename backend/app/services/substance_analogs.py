from app.schemas.documents import SubstanceAnalog, SubstanceAnalogsRequest, SubstanceAnalogsResponse


ANALOG_DATABASE: dict[str, list[dict]] = {
    "64-17-5": [
        {
            "cas": "67-63-0",
            "name": "Isopropanol",
            "iupac_name": "Propan-2-ol",
            "molecular_formula": "C3H8O",
            "structural_similarity": "Small alcohol with hydroxyl functional group; similar polarity and solvent profile.",
            "functional_similarity": "Cleaning, extraction, coatings, and disinfectant applications where ethanol is not specifically required.",
            "price_indication": "Often lower cost than ethanol, depending on region and grade.",
            "advantages": ["Widely available", "Lower excise complexity in some markets", "Good industrial solvent"],
            "disadvantages": ["Not suitable for food/beverage use", "Different odor and evaporation profile"],
            "similarity_basis": ["functional group", "solvent application", "common industrial substitution"],
        },
        {
            "cas": "71-23-8",
            "name": "n-Propanol",
            "iupac_name": "Propan-1-ol",
            "molecular_formula": "C3H8O",
            "structural_similarity": "Primary alcohol one carbon longer than ethanol.",
            "functional_similarity": "Industrial solvent and chemical intermediate where reactivity profile is acceptable.",
            "price_indication": "Comparable to isopropanol; market-dependent.",
            "advantages": ["Similar primary alcohol chemistry", "Useful for resin and coating systems"],
            "disadvantages": ["Less available than isopropanol", "Higher boiling point than ethanol"],
            "similarity_basis": ["homologous series", "primary alcohol", "solvent application"],
        },
        {
            "cas": "67-56-1",
            "name": "Methanol",
            "iupac_name": "Methanol",
            "molecular_formula": "CH4O",
            "structural_similarity": "Smallest alcohol; similar functional group but materially different toxicity profile.",
            "functional_similarity": "Industrial solvent and synthesis feedstock only where toxicity and regulations permit.",
            "price_indication": "Usually cheaper than ethanol.",
            "advantages": ["Low cost", "High availability", "Useful synthesis feedstock"],
            "disadvantages": ["Highly toxic", "Not acceptable for consumer, pharma, food, or many cleaning uses"],
            "similarity_basis": ["functional group", "commodity alcohol", "solvent/feedstock role"],
        },
    ],
    "67-64-1": [
        {
            "cas": "78-93-3",
            "name": "Methyl ethyl ketone",
            "iupac_name": "Butan-2-one",
            "molecular_formula": "C4H8O",
            "structural_similarity": "Aliphatic ketone with longer carbon chain than acetone.",
            "functional_similarity": "Paint, coating, resin, and adhesive solvent where slower evaporation is acceptable.",
            "price_indication": "Often higher than acetone but may reduce process losses.",
            "advantages": ["Stronger solvent power", "Longer working time"],
            "disadvantages": ["Different VOC/regulatory profile", "Higher cost in many markets"],
            "similarity_basis": ["ketone class", "coatings solvent", "industrial solvent substitution"],
        },
        {
            "cas": "141-78-6",
            "name": "Ethyl acetate",
            "iupac_name": "Ethyl acetate",
            "molecular_formula": "C4H8O2",
            "structural_similarity": "Ester, not ketone, but similar volatility and solvent use cases.",
            "functional_similarity": "Solvent for inks, coatings, adhesives, and selected extraction workflows.",
            "price_indication": "Often comparable to acetone.",
            "advantages": ["Commonly available", "Less aggressive odor", "Often accepted in consumer-facing formulations"],
            "disadvantages": ["Different solvency and hydrolysis behavior", "Not interchangeable in ketone-specific chemistry"],
            "similarity_basis": ["application analog", "volatility range", "solvent role"],
        },
    ],
    "108-88-3": [
        {
            "cas": "1330-20-7",
            "name": "Xylene, mixed isomers",
            "iupac_name": "Dimethylbenzene",
            "molecular_formula": "C8H10",
            "structural_similarity": "Aromatic hydrocarbon with methyl substitution, close solvent family to toluene.",
            "functional_similarity": "Paint, coating, adhesive, and extraction solvent where slower evaporation is acceptable.",
            "price_indication": "Often comparable to toluene.",
            "advantages": ["Higher boiling range", "Strong solvency for many resins"],
            "disadvantages": ["Similar safety controls", "Slower evaporation"],
            "similarity_basis": ["aromatic solvent", "structural analog", "coatings solvent"],
        },
        {
            "cas": "110-82-7",
            "name": "Cyclohexane",
            "iupac_name": "Cyclohexane",
            "molecular_formula": "C6H12",
            "structural_similarity": "Non-aromatic hydrocarbon; not structurally close but sometimes functional substitute.",
            "functional_similarity": "Non-polar solvent for extraction and cleaning where aromatic solvency is not required.",
            "price_indication": "May be cheaper than toluene depending on market.",
            "advantages": ["Non-aromatic solvent option", "Different regulatory profile"],
            "disadvantages": ["Different solubility parameters", "Not suitable for aromatic-specific reactions"],
            "similarity_basis": ["functional analog", "non-polar solvent", "cost-driven substitution"],
        },
    ],
}

DEFAULT_RECOMMENDATION = (
    "Treat analog suggestions as screening leads only. Validate process performance, purity, "
    "SDS/COA, transport class, REACH/CLP status, customs classification, and lawful end-use before sourcing."
)


class SubstanceAnalogsService:
    def find_analogs(self, request: SubstanceAnalogsRequest) -> SubstanceAnalogsResponse:
        analogs = [SubstanceAnalog(**item) for item in ANALOG_DATABASE.get(request.cas, [])]
        if not analogs:
            return SubstanceAnalogsResponse(
                source_cas=request.cas,
                source_name=request.primary_name or request.cas,
                analogs=[],
                recommendation=(
                    "No curated analogs found in the internal database. Use PubChem structural similarity, "
                    "supplier catalogs, and R&D validation before substituting. " + DEFAULT_RECOMMENDATION
                ),
            )

        cheaper = next((item for item in analogs if "cheaper" in item.price_indication.lower() or "lower cost" in item.price_indication.lower()), analogs[0])
        application_note = f" Target application: {request.target_application}." if request.target_application else ""
        return SubstanceAnalogsResponse(
            source_cas=request.cas,
            source_name=request.primary_name or request.cas,
            analogs=analogs,
            recommendation=(
                f"Start review with {cheaper.name} (CAS {cheaper.cas}) as the first cost/function candidate."
                f"{application_note} {DEFAULT_RECOMMENDATION}"
            ),
        )
