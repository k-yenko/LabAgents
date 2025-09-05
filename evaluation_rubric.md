# LLM-as-a-Judge Evaluation Rubric

## Instructions for Evaluation

Given a QUESTION and RESPONSE, evaluate if the response is correct based on the following criteria:

## Correct Response Criteria

Correct responses must include:

### Numerical Accuracy
- **pKa values**: ±1.0 units from expected values
- **LogP/logP values**: ±0.5 units from expected values  
- **Dipole moments**: ±0.5 Debye from expected values
- **Solubility**: Same order of magnitude (e.g., 2.2 mg/mL can be 1.5-3.0 mg/mL)
- **Redox potentials**: ±0.1 V from expected values
- **Binding energies/affinities**: Same order of magnitude

### Structural/Chemical Accuracy
- Correct identification of dominant tautomers/conformers (matching general description, exact counts may vary)
- Correct reactive sites for Fukui indices (primary sites must be identified)
- Correct metabolic pathways (glucuronidation, sulfation sites)
- Correct protonation states at specified pH

### Key Chemical Insights
- Must identify the most important finding (e.g., "dominant form at pH 7.4", "primary reactive site", "lowest energy conformer characteristics")
- Must provide relevant context (e.g., "99% protein bound", "poor BBB permeability due to P-gp")

## Incorrect Response Criteria

A response is INCORRECT if it:
- Provides values outside acceptable ranges without justification
- Misidentifies chemical structures or reactive sites
- Gives contradictory information
- Misses the key chemical insight requested

## Output Format

For each model response, return a JSON object with:
```json
{
  "model_name": {
    "correct": true or false,
    "score": 1 or 0,
    "notes": "Brief explanation of why the response is correct/incorrect, including specific values found"
  }
}
```

Example:
```json
{
  "claude-4-sonnet": {
    "correct": true,
    "score": 1,
    "notes": "Provided accurate results: logP=3.073 (within range), pKa=5.692 (within range)"
  }
}
```
