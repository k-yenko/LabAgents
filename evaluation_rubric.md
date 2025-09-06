# LLM-as-a-Judge Evaluation Rubric

## Instructions for Evaluation

Given a QUESTION and RESPONSE, evaluate if the response is correct based on the following criteria:

## Correct Response Criteria

Consider correct if:
- Numerical values fall within typical literature ranges OR are properly justified
- Chemical reasoning is sound (e.g., correct protonation state at pH 7.4)
- Key insights are captured (e.g., identifies reactive sites correctly)

Do NOT penalize for:
- Using different but valid literature sources
- Reasonable variation in computational methods
- Minor numerical differences within expected uncertainty

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
