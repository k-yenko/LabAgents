# Parallel Judge Evaluation Guide

## Quick Start

### Run GPT-5 and Gemini in parallel (recommended):
```bash
cd /Users/katherineyenko/Desktop/sandbox/labagents_v2
.venv/bin/python run_all_judges_parallel.py
```

### Run all 4 judges in parallel:
```bash
.venv/bin/python run_all_judges_parallel.py --judges gpt5 gemini qwen claude
```

### Run specific judges:
```bash
# Just GPT-5
.venv/bin/python run_all_judges_parallel.py --judges gpt5

# GPT-5 and Qwen
.venv/bin/python run_all_judges_parallel.py --judges gpt5 qwen
```

### Run without web search:
```bash
.venv/bin/python run_all_judges_parallel.py --no-web-search
```

## Individual Judge Scripts

If you prefer to run judges separately:

```bash
# GPT-5 judge
.venv/bin/python scripts/run_all_evals_gpt5_judge.py

# Gemini judge
.venv/bin/python scripts/run_all_evals_gemini_judge.py
```

## Output Directories

Each judge writes to its own directory:
- `evaluations_gpt5/` - GPT-5 evaluations
- `evaluations_gemini/` - Gemini 2.5 Pro evaluations
- `evaluations_qwen/` - Qwen evaluations (already exists)
- `evaluations/` - Claude Sonnet 4 evaluations (already exists)

## Generating Plots

After running judges, generate plots for each:

```bash
# For GPT-5
.venv/bin/python create_plots_for_judge.py --judge gpt5 --input evaluations_gpt5 --output plots_gpt5

# For Gemini
.venv/bin/python create_plots_for_judge.py --judge gemini --input evaluations_gemini --output plots_gemini

# For comparisons (after all judges complete)
.venv/bin/python create_multi_judge_comparison.py --judges gpt5 gemini qwen claude
```

## Expected Runtime

- Each judge evaluates ~180-190 logs
- Parallel execution: All judges complete in the time of the slowest judge
- Estimated time: 30-60 minutes depending on API speed
- Cost estimate: ~$0.02 per evaluation × 180 logs × 2 judges = ~$7.20

## Monitoring Progress

The parallel script shows live progress for all judges. Example output:
```
[GPT-5] [45/182] anthropic/claude-opus-4.1 on tier1_003...
  ✅ pass (5/6)
[Gemini] [23/182] openai/gpt-5 on tier2_001...
  ✅ pass (6/6)
```

## Troubleshooting

### Script fails to import
Make sure you're in the correct directory:
```bash
cd /Users/katherineyenko/Desktop/sandbox/labagents_v2
```

### Missing dependencies
```bash
.venv/bin/python -m pip install openai anthropic
```

### Check what's already evaluated
```bash
# Count GPT-5 evaluations
find evaluations_gpt5 -name "*_evaluation.json" | wc -l

# Count Gemini evaluations
find evaluations_gemini -name "*_evaluation.json" | wc -l
```

### Resume failed evaluations
The scripts automatically skip already-evaluated logs, so just re-run the same command.

## For Final Report

1. Run all judges in parallel:
```bash
.venv/bin/python run_all_judges_parallel.py --judges gpt5 gemini qwen claude
```

2. Generate comparison plots:
```bash
# Create individual plots for each judge
.venv/bin/python create_qwen_plots.py  # Already done
# Create plots for GPT-5 and Gemini (modify create_qwen_plots.py)

# Create cross-judge comparison
.venv/bin/python create_judge_comparison_plots.py
```

3. Analyze bias patterns:
- Same-family bias: Do Claude judges favor Claude models?
- Score distributions: Which judges are most strict?
- Agreement rates: How often do judges agree on pass/fail?
