#!/usr/bin/env python3
"""
run_all_missing.py - batch runner for all models on missing questions only
"""

import os
import sys
import subprocess
import glob
from pathlib import Path

# Add parent directory to path to import questions
sys.path.append(str(Path(__file__).parent.parent))
from scripts.questions import ALL_QUESTIONS

# All models to run
ALL_MODELS = [
    # Anthropic (via direct API)
    "anthropic/claude-opus-4.1",
    "anthropic/claude-sonnet-4.5",

    # OpenRouter models
    "openai/gpt-5",
    "openai/o3",
    "google/gemini-2.5-pro",
    "deepseek/deepseek-chat-v3.1:free",
    "x-ai/grok-4-fast:free",
    "x-ai/grok-code-fast-1"
]

def has_model_run(question_id: str, model: str) -> bool:
    """Check if a model has already been run on a question"""
    # Clean model name for directory structure
    clean_model = model.replace("/", "_").replace(":", "_")

    # For Sonnet 4.5, also check the old "sonnet-4" folder name
    model_dirs = [f"logs/{question_id}/{clean_model}"]
    if "sonnet-4.5" in clean_model or "sonnet-4-5" in clean_model:
        model_dirs.append(f"logs/{question_id}/anthropic_claude-sonnet-4")

    for model_dir in model_dirs:
        if not os.path.exists(model_dir):
            continue

        # Look for any non-error log files in the model directory
        log_files = glob.glob(f"{model_dir}/*.json")

        if log_files:
            # Check if any log file is not empty and not an error file
            for log_file in log_files:
                if "api_error" not in log_file and os.path.getsize(log_file) > 100:  # At least 100 bytes
                    return True

    return False

def get_missing_runs() -> dict:
    """Get dictionary of {model: [missing_questions]} for all models"""
    missing_by_model = {}

    for model in ALL_MODELS:
        missing = []
        for question_id in sorted(ALL_QUESTIONS.keys()):
            if not has_model_run(question_id, model):
                missing.append(question_id)

        if missing:
            missing_by_model[model] = missing

    return missing_by_model

def run_model_on_question(question_id: str, model: str):
    """Run a specific model on a specific question"""
    print(f"\n{'='*80}")
    print(f"🚀 Running {model} on {question_id}")
    print(f"{'='*80}\n")

    # Use sys.executable to get the same Python interpreter running this script
    cmd = [
        sys.executable, "agent_runner.py",
        question_id,
        "--model", model
    ]

    try:
        # Run without capturing output so we see real-time progress
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        if result.returncode == 0:
            print(f"\n✅ {model} on {question_id} completed successfully\n")
            return True
        else:
            print(f"\n❌ {model} on {question_id} failed with exit code {result.returncode}\n")
            return False
    except Exception as e:
        print(f"\n❌ Exception running {model} on {question_id}: {e}\n")
        return False

def main():
    print("🎯 Running ALL models on MISSING questions")
    print("=" * 80)

    # Get all missing runs
    missing_by_model = get_missing_runs()

    if not missing_by_model:
        print("🎉 All questions have been run with all models!")
        return

    # Display summary
    total_missing = sum(len(questions) for questions in missing_by_model.values())
    print(f"\n📊 Total missing runs: {total_missing}")
    print(f"📋 Total questions: {len(ALL_QUESTIONS)}")
    print(f"🤖 Total models: {len(ALL_MODELS)}\n")

    for model, questions in sorted(missing_by_model.items()):
        print(f"\n{model}:")
        print(f"  Missing: {len(questions)} questions")
        print(f"  Questions: {', '.join(questions)}")

    print("\n" + "=" * 80)

    # Confirm before running
    response = input(f"\n⚠️  Run {total_missing} missing model-question combinations? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cancelled")
        return

    # Run all missing combinations
    successes = 0
    failures = 0
    failed_runs = []

    for model, questions in sorted(missing_by_model.items()):
        print(f"\n{'#'*80}")
        print(f"# Starting {model} - {len(questions)} questions")
        print(f"{'#'*80}")

        for question_id in questions:
            if run_model_on_question(question_id, model):
                successes += 1
            else:
                failures += 1
                failed_runs.append((model, question_id))

    # Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    print(f"✅ Successes: {successes}")
    print(f"❌ Failures: {failures}")

    if failed_runs:
        print(f"\n❌ Failed runs:")
        for model, question_id in failed_runs:
            print(f"  - {model} on {question_id}")
    else:
        print("\n🎉 All runs completed successfully!")

if __name__ == "__main__":
    main()
