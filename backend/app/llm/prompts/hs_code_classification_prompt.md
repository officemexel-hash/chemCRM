# HS Code Classification Prompt

Classify a chemical substance into a Harmonized System (HS) code.

## Input
- CAS number: {{cas}}
- Chemical name: {{chemical_name}}
- Molecular formula: {{molecular_formula}}
- IUPAC name: {{iupac_name}}
- Synonyms: {{synonyms}}

## Instructions
1. Identify the correct HS code based on the chemical structure and common trade classification
2. HS chapters 28-29 cover most organic/inorganic chemicals
3. Provide confidence level and alternatives

## Output Format (JSON only, no other text)
```json
{
  "hs_code": "2905.19.00",
  "chapter": "29",
  "heading": "2905",
  "subheading": "2905.19",
  "description": "Acyclic monoalcohols: Other: Other",
  "confidence": 0.85,
  "alternative_codes": [
    {"hs_code": "2905.19.10", "confidence": 0.7, "description": "Alternative classification"}
  ],
  "reasoning": "Brief explanation of the classification logic"
}
```
