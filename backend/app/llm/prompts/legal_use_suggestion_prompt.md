# Legal Use Suggestion Prompt

Suggest lawful industrial, research, or commercial use descriptions for customs declaration purposes.

## Input
- CAS number: {{cas}}
- Substance name: {{substance_name}}
- Molecular formula: {{molecular_formula}}
- Destination country: {{destination_country}}
- HS code: {{hs_code}}

## Instructions
1. Suggest legitimate commercial, industrial, research, or manufacturing uses
2. Each use should be specific enough for customs declaration
3. Consider the destination country's common import classifications
4. Focus on lawful, well-documented applications
5. Provide confidence level for each suggestion

## Output Format (JSON only, no other text)
```json
{
  "uses": [
    {
      "description": "Used as intermediate in pharmaceutical manufacturing",
      "category": "pharmaceutical_intermediate",
      "confidence": 0.9
    },
    {
      "description": "Industrial solvent for coatings and adhesives",
      "category": "industrial_solvent",
      "confidence": 0.8
    }
  ]
}
```
