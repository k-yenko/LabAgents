# LLM-as-a-Judge Evaluation System

This system uses an LLM judge to evaluate model responses according to a standardized rubric and generate score.json files for each question.

## Files

- `evaluation_rubric.md` - The evaluation criteria and instructions for the judge
- `expected_values.json` - Expected value ranges for each question
- `evaluate_responses.py` - Main evaluation script
- `tier*/response.jsonl` - Model responses to evaluate
- `tier*/score.json` - Generated evaluation results

## Usage

### 1. Basic Evaluation
```bash
python evaluate_responses.py
```
This will evaluate all `tier*/response.jsonl` files and generate corresponding `score.json` files.

### 2. Custom Configuration
```python
from evaluate_responses import ResponseEvaluator

# Initialize with custom settings
evaluator = ResponseEvaluator(
    rubric_path="evaluation_rubric.md",
    expected_values_path="expected_values.json", 
    judge_model="gpt-4"  # or your preferred model
)

# Evaluate a specific folder
evaluator.evaluate_question_folder("tier2_002")

# Or evaluate all questions
evaluator.evaluate_all_questions()
```

### 3. Setting up your LLM Client
Edit the `_call_judge_llm` method in `evaluate_responses.py` to use your LLM client:

```python
def _call_judge_llm(self, prompt: str) -> str:
    # Example for OpenAI
    client = openai.OpenAI(api_key="your-key")
    response = client.chat.completions.create(
        model=self.judge_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content
```

## Output Format

Each `score.json` file contains:
```json
{
  "tier2_002_scores": {
    "model_name": {
      "correct": true/false,
      "score": 1/0,
      "notes": "Evaluation reasoning"
    }
  },
  "evaluation_criteria": {
    "scoring_method": "llm_judge_binary",
    "rubric_file": "evaluation_rubric.md",
    "judge_model": "gpt-4"
  },
  "summary": {
    "total_models": 8,
    "correct_answers": 6,
    "incorrect_answers": 2,
    "success_rate": "75%"
  }
}
```

## Adding New Questions

1. Add expected values to `expected_values.json`:
```json
{
  "tier2_004": {
    "description": "Your question description with expected values",
    "pKa_range": [4.0, 6.0],
    "logP_range": [2.0, 4.0]
  }
}
```

2. Create the question folder with `response.jsonl`
3. Run the evaluation script

## Evaluation Criteria

The judge evaluates responses based on:
- **Numerical accuracy** within specified ranges
- **Structural/chemical accuracy** 
- **Key chemical insights** identification

See `evaluation_rubric.md` for complete criteria.
