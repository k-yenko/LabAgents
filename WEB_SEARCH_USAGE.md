# Web Search Judge - Usage Guide

## Overview

The LLM judge now supports **web search** via OpenRouter, enabling real literature validation for chemistry evaluations. The judge can search for experimental values, PubChem data, and computational benchmarks to objectively score agent correctness.

## Key Changes

1. **Web search enabled by default** - Judge automatically searches for literature values
2. **Real citations** - Evaluations include actual URLs from web search results
3. **Easy model switching** - Can use Claude, GPT, or any OpenRouter model
4. **Flexible control** - Can enable/disable web search per evaluation

## Usage Examples

### Single Evaluation with Web Search (default)

```bash
# Claude Sonnet 4 with web search (default)
python llm_judge_evaluator.py tier1_001 --single logs/tier1_001/anthropic_claude-sonnet-4/log.json

# GPT-4 with web search
python llm_judge_evaluator.py --single logs/tier1_001/... --judge openai/gpt-4

# Disable web search
python llm_judge_evaluator.py --single logs/tier1_001/... --no-web-search
```

### Batch Evaluation

```bash
# Evaluate all missing with Claude Sonnet 4 + web search
python scripts/run_all_missing_evals.py

# Use GPT-4o as judge with web search
python scripts/run_all_missing_evals.py --judge openai/gpt-4o

# Use different output directory
python scripts/run_all_missing_evals.py --output-dir evaluations_gpt4 --judge openai/gpt-4o

# Disable web search for all evaluations
python scripts/run_all_missing_evals.py --no-web-search
```

## Model Options

**Claude models (recommended for chemistry):**
- `anthropic/claude-sonnet-4` (default)
- `anthropic/claude-opus-4`
- `anthropic/claude-sonnet-3.5`

**OpenAI models:**
- `openai/gpt-4o`
- `openai/gpt-4-turbo`
- `openai/gpt-4`

**Any OpenRouter model works!**

## Web Search Behavior

When web search is enabled (`:online` suffix):

1. **Judge receives search results** automatically based on query context
2. **Citations extracted** from response annotations
3. **Saved in evaluation** JSON and markdown reports
4. **Used for scoring** - judge validates answers against literature

### Example Search Queries the Judge Makes:

- "acetic acid pKa experimental value"
- "PubChem aspirin"
- "DFT pKa calculation benchmark"
- "computational chemistry logP prediction accuracy"

## Pricing

### OpenRouter Web Search Pricing

**Exa search (default for most models):**
- **$4 per 1000 results**
- Default: 5 results per request = **$0.02 per evaluation**
- For 200 evaluations: **~$4.00**

**Native search (Claude/OpenAI/Perplexity):**
- Uses provider's built-in search
- Pricing varies by provider (see OpenRouter docs)
- Generally similar or slightly higher cost

### Total Cost Example (200 evaluations)

- Base LLM costs: ~$0.50-1.00 (depends on model)
- Web search: ~$4.00
- **Total: ~$5 for complete dataset**

## Output Format

### JSON Evaluation includes:

```json
{
  "completion_score": 2,
  "correctness_score": 2,
  "tool_use_score": 2,
  "total_score": 6,
  "overall_assessment": "pass",
  "web_citations": [
    {
      "url": "https://pubchem.ncbi.nlm.nih.gov/compound/acetic-acid",
      "title": "Acetic Acid | PubChem",
      "content": "pKa: 4.76 at 25°C"
    }
  ]
}
```

### Markdown Report includes:

```markdown
### Web Search Citations:
1. [Acetic Acid | PubChem](https://pubchem.ncbi.nlm.nih.gov/compound/acetic-acid)
2. [ChemSpider | Acetic Acid](https://chemspider.com/...)
```

## Benefits

✅ **Real validation** - Judge checks against actual literature, not just guesses
✅ **Defendable scores** - Every correctness score backed by citations
✅ **Reduced bias** - Objective comparison to published values
✅ **Better feedback** - Agents learn what correct answers look like

## Comparison: Before vs After

### Before (no web search):
- Judge guesses if values are reasonable
- No citations
- High variance in scoring
- Same-family bias (Claude favors Claude)

### After (with web search):
- Judge validates against PubChem/literature
- Real URLs cited
- Consistent scoring based on literature
- Objective correctness measurement

## Next Steps

1. **Test on single evaluation** to verify web search works
2. **Run batch on subset** (e.g., tier1 only) to test at scale
3. **Compare with previous evaluations** to measure improvement
4. **Run full dataset** once confident

## Troubleshooting

**If web search not working:**
- Check that model name includes `:online` suffix (auto-added by code)
- Verify OPENROUTER_API_KEY is set
- Check OpenRouter API credits

**If citations not appearing:**
- Some models may not return annotations
- Try different judge model
- Check evaluation JSON for `web_citations` field

**If costs higher than expected:**
- Use `--no-web-search` to disable
- Reduce number of evaluations
- Check OpenRouter usage dashboard
