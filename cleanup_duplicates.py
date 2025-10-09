#!/usr/bin/env python3
"""
Clean up duplicate logs and evaluations
Keep only the most recent file for each model-question combination
"""

import glob
import os
from collections import defaultdict
from pathlib import Path

def cleanup_logs():
    """Remove duplicate logs, keep most recent"""
    print("🧹 Cleaning up duplicate logs...")

    all_logs = glob.glob('logs/*/*/*.json')
    all_logs = [l for l in all_logs if 'api_error' not in l]

    # Group by question and model
    groups = defaultdict(list)

    for log_file in all_logs:
        parts = log_file.split('/')
        question_id = parts[1]
        model_dir = parts[2]

        key = (question_id, model_dir)
        groups[key].append(log_file)

    # Find and remove duplicates, keep most recent
    removed = 0
    for (question, model), files in groups.items():
        if len(files) > 1:
            # Sort by filename (timestamp in filename)
            files_sorted = sorted(files)
            most_recent = files_sorted[-1]

            print(f"\n{question}/{model}:")
            print(f"  Keeping: {most_recent}")

            for old_file in files_sorted[:-1]:
                print(f"  Removing: {old_file}")
                os.remove(old_file)
                removed += 1

    print(f"\n✅ Removed {removed} duplicate log files")

def cleanup_evaluations():
    """Remove evaluation files with ' 2.json' or '2.json' suffix"""
    print("\n🧹 Cleaning up duplicate evaluations...")

    # Find all files with "2.json" pattern
    patterns = [
        'evaluations/*/json/*_evaluation 2.json',
        'evaluations/*/json/*_evaluation_2.json',
        'evaluations/*/json/*2.json'
    ]

    removed = 0
    for pattern in patterns:
        files = glob.glob(pattern)
        for f in files:
            print(f"  Removing: {f}")
            os.remove(f)
            removed += 1

    # Also clean up corresponding .md files
    md_patterns = [
        'evaluations/*/md/*_evaluation 2.md',
        'evaluations/*/md/*_evaluation_2.md',
        'evaluations/*/md/*2.md'
    ]

    for pattern in md_patterns:
        files = glob.glob(pattern)
        for f in files:
            print(f"  Removing: {f}")
            os.remove(f)
            removed += 1

    print(f"\n✅ Removed {removed} duplicate evaluation files")

def verify_cleanup():
    """Verify no duplicates remain"""
    print("\n🔍 Verifying cleanup...")

    # Check logs
    all_logs = glob.glob('logs/*/*/*.json')
    all_logs = [l for l in all_logs if 'api_error' not in l]

    groups = defaultdict(list)
    for log_file in all_logs:
        parts = log_file.split('/')
        question_id = parts[1]
        model_dir = parts[2]
        key = (question_id, model_dir)
        groups[key].append(log_file)

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}

    if duplicates:
        print(f"❌ Still have {len(duplicates)} duplicate log groups")
        for k, v in duplicates.items():
            print(f"  {k}: {len(v)} files")
    else:
        print("✅ No duplicate logs")

    # Check evaluations
    dup_evals = glob.glob('evaluations/*/json/*2.json')
    if dup_evals:
        print(f"❌ Still have {len(dup_evals)} evaluation duplicates")
    else:
        print("✅ No duplicate evaluations")

if __name__ == "__main__":
    print("="*60)
    print("CLEANING UP DUPLICATES")
    print("="*60)

    cleanup_logs()
    cleanup_evaluations()
    verify_cleanup()

    print("\n" + "="*60)
    print("Now regenerate leaderboard with:")
    print("  python leaderboard/update_leaderboard.py")
    print("="*60)
