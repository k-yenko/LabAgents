#!/usr/bin/env python3
"""
run_all_missing_evals.py - batch run LLM judge evaluations on logs that don't have evaluations yet

what this does:
- scans logs/ directory for all successful log files
- checks evaluations/ directory to see which logs already have evaluations
- finds logs missing evaluations
- runs llm_judge_evaluator.py on all missing ones
- displays progress and summary

use this when: you want to evaluate all logs that don't have evaluations yet
example: python scripts/run_all_missing_evals.py
"""

import os
import sys
import glob
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import llm_judge_evaluator
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_judge_evaluator import evaluate_single_log
from scripts.questions import ALL_QUESTIONS

def get_model_name_from_log(log_file: str) -> str:
    """Extract model name from log file"""
    import json
    try:
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        return log_data.get("model_name", "unknown")
    except:
        return "unknown"

def has_evaluation(question_id: str, model_name: str) -> bool:
    """Check if evaluation already exists for this question-model combination"""
    # Clean model name for filename
    clean_model = model_name.replace("/", "_").replace(":", "_")

    # Check if evaluation JSON exists
    eval_path = f"evaluations/{question_id}/json/{clean_model}_evaluation.json"
    return os.path.exists(eval_path)

def find_missing_evaluations():
    """Find all logs that don't have evaluations yet (only most recent log per model-question pair)"""
    missing = []

    # Scan all question directories in logs/
    for question_id in ALL_QUESTIONS.keys():
        question_dir = f"logs/{question_id}"
        if not os.path.exists(question_dir):
            continue

        # Find all log files in model subdirectories
        log_pattern = f"{question_dir}/*/*.json"
        log_files = glob.glob(log_pattern)

        # Group log files by model name and keep only the most recent
        logs_by_model = {}
        for log_file in log_files:
            # Skip API error logs
            if "api_error" in log_file:
                continue

            # Get model name from log
            model_name = get_model_name_from_log(log_file)

            # Get file modification time
            mtime = os.path.getmtime(log_file)

            # Keep only the most recent log for each model
            if model_name not in logs_by_model or mtime > logs_by_model[model_name]["mtime"]:
                logs_by_model[model_name] = {
                    "log_file": log_file,
                    "mtime": mtime
                }

        # Check which models are missing evaluations
        for model_name, log_info in logs_by_model.items():
            if not has_evaluation(question_id, model_name):
                missing.append({
                    "question_id": question_id,
                    "model_name": model_name,
                    "log_file": log_info["log_file"]
                })

    return missing

async def run_missing_evaluations(missing_evals):
    """Run evaluations for all missing logs"""
    total = len(missing_evals)
    successes = 0
    failures = []

    for i, eval_info in enumerate(missing_evals, 1):
        question_id = eval_info["question_id"]
        model_name = eval_info["model_name"]
        log_file = eval_info["log_file"]

        print(f"\n{'='*80}")
        print(f"🚀 Evaluating [{i}/{total}]: {model_name} on {question_id}")
        print(f"{'='*80}\n")

        try:
            await evaluate_single_log(log_file)
            successes += 1
            print(f"✅ Evaluation {i}/{total} completed successfully\n")
        except Exception as e:
            failures.append({
                "question_id": question_id,
                "model_name": model_name,
                "error": str(e)
            })
            print(f"❌ Evaluation {i}/{total} failed: {e}\n")

    return successes, failures

def main():
    print("🎯 Finding logs without evaluations")
    print("="*80)

    # Find missing evaluations
    missing = find_missing_evaluations()

    if not missing:
        print("✅ All logs have been evaluated!")
        return

    # Group by question for display
    by_question = {}
    for item in missing:
        qid = item["question_id"]
        if qid not in by_question:
            by_question[qid] = []
        by_question[qid].append(item["model_name"])

    print(f"\n📊 Total missing evaluations: {len(missing)}")
    print(f"📋 Questions with missing evaluations: {len(by_question)}\n")

    for question_id in sorted(by_question.keys()):
        models = by_question[question_id]
        print(f"{question_id}:")
        print(f"  Missing: {len(models)} evaluations")
        print(f"  Models: {', '.join(models)}\n")

    print("="*80)

    # Ask for confirmation
    response = input(f"\n⚠️  Run {len(missing)} missing evaluations? (y/N): ")

    if response.lower() != 'y':
        print("❌ Cancelled")
        return

    # Run evaluations
    print("\n🚀 Starting batch evaluation...\n")
    successes, failures = asyncio.run(run_missing_evaluations(missing))

    # Final summary
    print("\n" + "="*80)
    print("📊 FINAL SUMMARY")
    print("="*80)
    print(f"✅ Successes: {successes}")
    print(f"❌ Failures: {len(failures)}")

    if failures:
        print("\n❌ Failed evaluations:")
        for failure in failures:
            print(f"  - {failure['model_name']} on {failure['question_id']}: {failure['error']}")

if __name__ == "__main__":
    main()
