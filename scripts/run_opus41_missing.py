#!/usr/bin/env python3
"""
run_opus41_missing.py - batch runner for opus 4.1 on missing questions only
"""

import os
import sys
import subprocess
import glob
from pathlib import Path

# Add parent directory to path to import questions
sys.path.append(str(Path(__file__).parent.parent))
from scripts.questions import ALL_QUESTIONS

# Opus 4.1 model options (auto-routes to Anthropic API)
OPUS_41_MODELS = [
    "anthropic/claude-opus-4.1",  # Auto-routes to claude-opus-4-1-20250805
]

def has_model_run(question_id: str, model: str) -> bool:
    """Check if a model has already been run on a question"""
    # Clean model name for directory structure
    clean_model = model.replace("/", "_").replace(":", "_")

    # Check logs directory
    logs_pattern = f"logs/{question_id}/*{clean_model}*"
    log_files = glob.glob(logs_pattern)

    if log_files:
        # Check if any log file is not empty
        for log_file in log_files:
            if os.path.getsize(log_file) > 100:  # At least 100 bytes
                return True

    return False

def get_missing_questions(model: str) -> list:
    """Get list of questions that haven't been run with this model"""
    missing = []

    for question_id in ALL_QUESTIONS.keys():
        if not has_model_run(question_id, model):
            missing.append(question_id)

    return missing

def run_model_on_question(question_id: str, model: str):
    """Run a specific model on a specific question"""
    print(f"🚀 Running {model} on {question_id}")

    cmd = [
        "python", "agent_runner.py",
        question_id,
        "--model", model
    ]

    try:
        # Run without capturing output so we see real-time progress
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        if result.returncode == 0:
            print(f"✅ {model} on {question_id} completed successfully")
            return True
        else:
            print(f"❌ {model} on {question_id} failed with exit code {result.returncode}")
            return False
    except Exception as e:
        print(f"❌ Exception running {model} on {question_id}: {e}")
        return False

def main():
    print("🎯 Running Opus 4.1 on MISSING questions")

    # Use specified model or default
    model = sys.argv[1] if len(sys.argv) > 1 else OPUS_41_MODELS[0]

    print(f"🤖 Model: {model}")
    print(f"📊 Total questions: {len(ALL_QUESTIONS)}")

    # Check what's missing
    missing_questions = get_missing_questions(model)

    print(f"🔍 Missing questions: {len(missing_questions)}")

    if not missing_questions:
        print("🎉 All questions have already been run with this model!")
        return

    print(f"📝 Missing: {sorted(missing_questions)}")
    print("=" * 50)

    # Confirm before running (Opus is expensive!)
    response = input(f"⚠️  Run Opus 4.1 on {len(missing_questions)} questions? This will be expensive! (y/N): ")
    if response.lower() != 'y':
        print("❌ Cancelled")
        return

    successes = 0
    failures = 0

    for question_id in sorted(missing_questions):
        print(f"\n📝 Question: {question_id}")

        success = run_model_on_question(question_id, model)
        if success:
            successes += 1
        else:
            failures += 1

    print("\n" + "=" * 50)
    print(f"🏁 SUMMARY")
    print(f"✅ Successes: {successes}")
    print(f"❌ Failures: {failures}")
    print(f"📊 Success rate: {successes}/{successes + failures} ({successes/(successes + failures)*100:.1f}%)")

def check_status():
    """Just check what's missing without running anything"""
    print("🔍 CHECKING STATUS FOR ALL MODELS")
    print("=" * 50)

    models_to_check = [
        "anthropic/claude-opus-4.1",      # Auto-routes to claude-opus-4-1-20250805
        "anthropic/claude-sonnet-4",      # Auto-routes to claude-3-5-sonnet-20241022
        "anthropic/claude-sonnet-4.5",    # Auto-routes to claude-sonnet-4-5-20250929
        "openai/gpt-5",
        "openai/o3"
    ]

    for model in models_to_check:
        missing = get_missing_questions(model)
        completed = len(ALL_QUESTIONS) - len(missing)
        print(f"🤖 {model}:")
        print(f"   ✅ Completed: {completed}/{len(ALL_QUESTIONS)}")
        print(f"   ❌ Missing: {len(missing)}")
        if missing:
            print(f"   📝 Missing questions: {sorted(missing)}")
        print()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_status()
    else:
        main()