#!/usr/bin/env python3
"""
Run all missing evaluations using GPT-5 as judge
Output: evaluations_gpt5/
"""

import asyncio
import glob
import os
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_judge_evaluator import evaluate_single_log

async def find_missing_evaluations(logs_dir="logs", eval_dir="evaluations_gpt5"):
    """Find logs that don't have evaluations yet"""

    # Find all successful log files (exclude api_error files)
    all_logs = glob.glob(f"{logs_dir}/*/*/*.json")
    all_logs = [l for l in all_logs if 'api_error' not in l]

    # Group by question and model, keep only most recent per combination
    log_groups = {}
    for log_file in all_logs:
        parts = log_file.split('/')
        question_id = parts[-3]
        model_name = parts[-2]

        key = (question_id, model_name)

        # Keep the most recent log (by filename timestamp)
        if key not in log_groups or log_file > log_groups[key]:
            log_groups[key] = log_file

    # Filter out logs that already have evaluations
    missing = []
    for (question_id, model_name), log_file in log_groups.items():
        # Check if evaluation exists
        eval_file = f"{eval_dir}/{question_id}/json/{model_name.replace('/', '_')}_evaluation.json"

        if not os.path.exists(eval_file):
            missing.append((question_id, model_name, log_file))

    return missing

async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run all missing evaluations with GPT-5 judge")
    parser.add_argument("--logs-dir", default="/Users/katherineyenko/Desktop/sandbox/labagents/logs",
                       help="Directory containing agent logs")
    parser.add_argument("--output-dir", default="evaluations_gpt5",
                       help="Output directory for evaluations")
    parser.add_argument("--judge", default="openai/gpt-5",
                       help="Judge model to use (default: openai/gpt-5)")
    parser.add_argument("--no-web-search", action="store_true",
                       help="Disable web search for judge")

    args = parser.parse_args()

    print("=" * 80)
    print("🎯 Finding logs without evaluations")
    print("=" * 80)
    print(f"📁 Logs directory: {args.logs_dir}")
    print(f"📁 Output directory: {args.output_dir}")
    print(f"⚖️  Judge model: {args.judge}")
    print(f"🔍 Web search: {'disabled' if args.no_web_search else 'enabled'}")
    print("=" * 80)

    missing = await find_missing_evaluations(args.logs_dir, args.output_dir)

    if not missing:
        print("\n✅ All logs have been evaluated!")
        return

    print(f"\n📊 Found {len(missing)} logs without evaluations\n")

    # Evaluate each missing log
    successes = 0
    failures = []

    for i, (question_id, model_name, log_file) in enumerate(missing, 1):
        print(f"[{i}/{len(missing)}] Evaluating {model_name} on {question_id}...")

        try:
            result = await evaluate_single_log(
                log_file,
                output_dir=args.output_dir,
                judge_model=args.judge,
                enable_web_search=not args.no_web_search
            )

            if result:
                successes += 1
                status = result.get('overall_assessment', 'unknown')
                score = result.get('total_score', 0)
                print(f"  ✅ {status} ({score}/6)")
            else:
                failures.append((model_name, question_id, "No result returned"))
                print(f"  ❌ Failed: No result")

        except Exception as e:
            failures.append((model_name, question_id, str(e)))
            print(f"  ❌ Failed: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    print(f"✅ Successes: {successes}")
    print(f"❌ Failures: {len(failures)}")

    if failures:
        print(f"\n❌ Failed evaluations:")
        for model, question, error in failures:
            print(f"  - {model} on {question}: {error}")

if __name__ == "__main__":
    asyncio.run(main())
