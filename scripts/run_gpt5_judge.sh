#!/bin/bash
# Run LLM judge evaluations with GPT-5 as the judge
# Results will be saved to evaluations_gpt5/ directory

python scripts/run_all_missing_evals.py \
    --output-dir evaluations_gpt5 \
    --judge openai/gpt-5
