#!/usr/bin/env python3
"""
run_sonnet45_all.py - batch runner for sonnet 4.5 on all tier1, tier2, tier3 questions
"""

import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path to import questions
sys.path.append(str(Path(__file__).parent.parent))
from scripts.questions import ALL_QUESTIONS

# Sonnet 4.5 model options (all auto-route to Anthropic API)
SONNET_45_MODELS = [
    "anthropic/claude-sonnet-4.5",  # Auto-routes to claude-sonnet-4-5-20250929
]

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
    print("🎯 Running Sonnet 4.5 on ALL questions")
    print(f"📊 Total questions: {len(ALL_QUESTIONS)}")
    print(f"🤖 Models: {SONNET_45_MODELS}")
    print()

    # Use first model (OpenRouter) by default, or specify via command line
    model = sys.argv[1] if len(sys.argv) > 1 else SONNET_45_MODELS[0]

    print(f"Using model: {model}")
    print("=" * 50)

    successes = 0
    failures = 0

    for question_id in sorted(ALL_QUESTIONS.keys()):
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

if __name__ == "__main__":
    main()