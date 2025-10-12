#!/usr/bin/env python3
"""
Run the 8 missing GPT-5 judge evaluations for tier2_005, tier2_006, and all tier3 questions.
"""

import asyncio
import glob
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_judge_evaluator import evaluate_single_log

load_dotenv()

MISSING_TIERS = [
    'tier2_005',
    'tier2_006',
    'tier3_001',
    'tier3_002',
    'tier3_003',
    'tier3_004',
    'tier3_005',
    'tier3_006'
]

async def find_logs_for_missing_tiers(logs_dir="logs"):
    """Find all log files for the missing tier evaluations."""
    missing_logs = []
    
    for tier in MISSING_TIERS:
        tier_pattern = f"{logs_dir}/{tier}/*/*.json"
        logs = glob.glob(tier_pattern)
        
        # Filter out error logs
        logs = [log for log in logs if 'api_error' not in log and 'error' not in log.lower()]
        
        if logs:
            print(f"  ✅ {tier}: found {len(logs)} logs")
            missing_logs.extend(logs)
        else:
            print(f"  ⚠️  {tier}: no logs found")
    
    return missing_logs

async def run_evaluation(log_file, judge_model="openai/gpt-5", output_dir="evaluations_gpt5"):
    """Run a single evaluation."""
    question_id = Path(log_file).parent.parent.name
    model_name = Path(log_file).parent.name
    
    try:
        await evaluate_single_log(
            log_file,
            output_dir=output_dir,
            judge_model=judge_model,
            enable_web_search=True
        )
        return True, None
    except Exception as e:
        return False, str(e)

async def main():
    print("="*80)
    print("🚀 Running Missing GPT-5 Judge Evaluations")
    print("="*80)
    print(f"\n📋 Missing tiers: {', '.join(MISSING_TIERS)}")
    print(f"⚖️  Judge model: openai/gpt-5")
    print(f"📁 Output directory: evaluations_gpt5")
    print(f"🔍 Web search: enabled\n")
    
    print("🔍 Finding log files for missing tiers...")
    missing_logs = await find_logs_for_missing_tiers()
    
    if not missing_logs:
        print("\n❌ No log files found for the missing tiers!")
        return
    
    print(f"\n✅ Found {len(missing_logs)} log files to evaluate\n")
    print("="*80)
    
    # Auto-confirm (no interactive prompt needed)
    print(f"\n🚀 Starting batch evaluation of {len(missing_logs)} logs...\n")
    print("="*80)
    
    successes = 0
    failures = 0
    failed_logs = []
    
    for i, log_file in enumerate(missing_logs, 1):
        question_id = Path(log_file).parent.parent.name
        model_name = Path(log_file).parent.name
        
        print(f"\n[{i}/{len(missing_logs)}] {question_id} - {model_name}")
        print(f"   📄 {log_file}")
        
        success, error = await run_evaluation(log_file)
        
        if success:
            print(f"   ✅ Success")
            successes += 1
        else:
            print(f"   ❌ Failed: {error}")
            failures += 1
            failed_logs.append((log_file, error))
    
    print("\n" + "="*80)
    print("📊 EVALUATION SUMMARY")
    print("="*80)
    print(f"✅ Successful: {successes}")
    print(f"❌ Failed: {failures}")
    print(f"📁 Output directory: evaluations_gpt5/")
    
    if failed_logs:
        print("\n⚠️  Failed evaluations:")
        for log_file, error in failed_logs:
            print(f"  - {log_file}")
            print(f"    Error: {error[:100]}")
    
    print("\n" + "="*80)
    print("✅ Batch evaluation complete!")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())

