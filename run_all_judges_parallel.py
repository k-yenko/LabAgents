#!/usr/bin/env python3
"""
Run multiple judges in parallel for final report
Runs: GPT-5, Gemini, Qwen, Claude Sonnet 4
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from llm_judge_evaluator import JudgeEvaluator
import glob
import os

async def find_missing_evaluations(logs_dir, eval_dir):
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

async def evaluate_with_judge(judge_name, judge_model, output_dir, logs_dir, enable_web_search=True):
    """Run evaluations with a specific judge"""

    print(f"\n{'='*80}")
    print(f"🎯 Starting {judge_name} evaluations")
    print(f"{'='*80}")
    print(f"  Judge model: {judge_model}")
    print(f"  Output: {output_dir}/")
    print(f"  Web search: {'enabled' if enable_web_search else 'disabled'}")

    # Find missing evaluations
    missing = await find_missing_evaluations(logs_dir, output_dir)

    if not missing:
        print(f"  ✅ All logs already evaluated!")
        return {'judge': judge_name, 'total': 0, 'successes': 0, 'failures': 0}

    print(f"  📊 Found {len(missing)} logs to evaluate\n")

    # Create evaluator
    evaluator = JudgeEvaluator(judge_model=judge_model, enable_web_search=enable_web_search)

    successes = 0
    failures = []

    for i, (question_id, model_name, log_file) in enumerate(missing, 1):
        print(f"  [{judge_name}] [{i}/{len(missing)}] {model_name} on {question_id}...")

        try:
            result = await evaluator.evaluate_log(log_file, output_dir)

            if result:
                successes += 1
                status = result.get('overall_assessment', 'unknown')
                score = result.get('total_score', 0)
                print(f"    ✅ {status} ({score}/6)")
            else:
                failures.append((model_name, question_id, "No result returned"))
                print(f"    ❌ Failed: No result")

        except Exception as e:
            failures.append((model_name, question_id, str(e)))
            print(f"    ❌ Failed: {e}")

    print(f"\n  {'='*80}")
    print(f"  {judge_name} Summary: {successes} successes, {len(failures)} failures")
    print(f"  {'='*80}\n")

    return {
        'judge': judge_name,
        'total': len(missing),
        'successes': successes,
        'failures': failures
    }

async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run multiple judges in parallel")
    parser.add_argument("--logs-dir", default="/Users/katherineyenko/Desktop/sandbox/labagents/logs",
                       help="Directory containing agent logs")
    parser.add_argument("--judges", nargs='+',
                       default=["gpt5", "gemini"],
                       choices=["gpt5", "gemini", "qwen", "claude"],
                       help="Which judges to run (default: gpt5 gemini)")
    parser.add_argument("--no-web-search", action="store_true",
                       help="Disable web search for all judges")

    args = parser.parse_args()

    # Judge configurations
    judge_configs = {
        "gpt5": {
            "name": "GPT-5",
            "model": "openai/gpt-5",
            "output_dir": "evaluations_gpt5"
        },
        "gemini": {
            "name": "Gemini 2.5 Pro",
            "model": "google/gemini-2.5-pro",
            "output_dir": "evaluations_gemini"
        },
        "qwen": {
            "name": "Qwen",
            "model": "qwen/qwen3-max",
            "output_dir": "evaluations_qwen"
        },
        "claude": {
            "name": "Claude Sonnet 4",
            "model": "anthropic/claude-sonnet-4",
            "output_dir": "evaluations"
        }
    }

    print("\n" + "="*80)
    print("🚀 PARALLEL JUDGE EVALUATION")
    print("="*80)
    print(f"Running {len(args.judges)} judges in parallel:")
    for judge_key in args.judges:
        config = judge_configs[judge_key]
        print(f"  - {config['name']} ({config['model']}) → {config['output_dir']}/")
    print("="*80 + "\n")

    # Create tasks for parallel execution
    tasks = []
    for judge_key in args.judges:
        config = judge_configs[judge_key]
        task = evaluate_with_judge(
            judge_name=config['name'],
            judge_model=config['model'],
            output_dir=config['output_dir'],
            logs_dir=args.logs_dir,
            enable_web_search=not args.no_web_search
        )
        tasks.append(task)

    # Run all judges in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Print final summary
    print("\n" + "="*80)
    print("🏁 FINAL SUMMARY - ALL JUDGES")
    print("="*80)

    total_successes = 0
    total_failures = 0

    for result in results:
        if isinstance(result, Exception):
            print(f"❌ Judge failed with exception: {result}")
        else:
            total_successes += result['successes']
            total_failures += len(result['failures'])

            print(f"\n{result['judge']}:")
            print(f"  Total evaluations: {result['total']}")
            print(f"  ✅ Successes: {result['successes']}")
            print(f"  ❌ Failures: {len(result['failures'])}")

            if result['failures']:
                print(f"  Failed on:")
                for model, question, error in result['failures'][:5]:  # Show first 5
                    print(f"    - {model} on {question}: {error}")
                if len(result['failures']) > 5:
                    print(f"    ... and {len(result['failures']) - 5} more")

    print("\n" + "="*80)
    print(f"GRAND TOTAL: {total_successes} successes, {total_failures} failures")
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
