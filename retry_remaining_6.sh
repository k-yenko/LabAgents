#!/bin/bash
# Retry the 6 evaluations that failed in batch mode

echo "🔄 Retrying 6 remaining evaluations individually..."
echo "================================================================================"

python llm_judge_evaluator.py --single "logs/tier3_001/openai_o3/openai_o3_20250926_180832.json" --output-dir evaluations_gpt5 --judge "openai/gpt-5"
echo "✅ [1/6] tier3_001 o3 complete"

python llm_judge_evaluator.py --single "logs/tier3_002/openai_gpt-5/openai_gpt-5_20250926_203138.json" --output-dir evaluations_gpt5 --judge "openai/gpt-5"
echo "✅ [2/6] tier3_002 gpt-5 complete"

python llm_judge_evaluator.py --single "logs/tier3_003/openai_gpt-5/openai_gpt-5_20250926_222540.json" --output-dir evaluations_gpt5 --judge "openai/gpt-5"
echo "✅ [3/6] tier3_003 gpt-5 complete"

python llm_judge_evaluator.py --single "logs/tier3_004/openai_gpt-5/openai_gpt-5_20250922_113532.json" --output-dir evaluations_gpt5 --judge "openai/gpt-5"
echo "✅ [4/6] tier3_004 gpt-5 complete"

python llm_judge_evaluator.py --single "logs/tier3_004/anthropic_claude-sonnet-4/anthropic_claude-sonnet-4_20250922_104145.json" --output-dir evaluations_gpt5 --judge "openai/gpt-5"
echo "✅ [5/6] tier3_004 sonnet-4 complete"

python llm_judge_evaluator.py --single "logs/tier3_005/google_gemini-2.5-pro/google_gemini-2.5-pro_20251004_162327.json" --output-dir evaluations_gpt5 --judge "openai/gpt-5"
echo "✅ [6/6] tier3_005 gemini complete"

echo "================================================================================"
echo "✅ All 6 evaluations complete!"
echo "================================================================================"
