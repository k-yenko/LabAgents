#!/usr/bin/env python3
"""
Quick judge comparison - evaluate same logs with different judges
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import glob

# Load env
load_dotenv()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_judge_evaluator import evaluate_single_log

async def compare_judges_on_samples():
    """Compare Claude vs Qwen judge on same logs"""

    # Pick diverse sample of logs (different models, different questions)
    # Find actual log files
    sample_patterns = [
        "logs/tier1_001/anthropic_claude-sonnet-4/*.json",
        "logs/tier1_001/openai_o3/*.json",
        "logs/tier1_002/anthropic_claude-sonnet-4/*.json",
        "logs/tier1_002/google_gemini-2.5-pro/*.json",
        "logs/tier1_003/anthropic_claude-opus-4.1/*.json",
    ]

    samples = []
    for pattern in sample_patterns:
        files = glob.glob(pattern)
        if files:
            # Get most recent
            files = [f for f in files if 'api_error' not in f]
            if files:
                samples.append(sorted(files)[-1])

    judges = [
        ("Claude", "anthropic/claude-sonnet-4", "evaluations"),
        ("Qwen", "qwen/qwen-2.5-72b-instruct", "evaluations_qwen"),
    ]

    results = []

    for log_file in samples:
        if not os.path.exists(log_file):
            print(f"⚠️  Skipping {log_file} - not found")
            continue

        print(f"\n{'='*80}")
        print(f"Evaluating: {log_file}")
        print(f"{'='*80}")

        log_results = {'log_file': log_file}

        for judge_name, judge_model, output_dir in judges:
            print(f"\n🤖 {judge_name} judge...")

            try:
                eval_result = await evaluate_single_log(
                    log_file,
                    output_dir=output_dir,
                    judge_model=judge_model,
                    enable_web_search=True
                )

                log_results[judge_name] = {
                    'completion': eval_result.completion_score,
                    'correctness': eval_result.correctness_score,
                    'tool_use': eval_result.tool_use_score,
                    'total': eval_result.total_score,
                    'assessment': eval_result.overall_assessment
                }

                print(f"  Score: {eval_result.total_score}/6 ({eval_result.overall_assessment})")

            except Exception as e:
                print(f"  ❌ Error: {e}")
                log_results[judge_name] = {'error': str(e)}

        results.append(log_results)

    # Summary
    print(f"\n{'='*80}")
    print("COMPARISON SUMMARY")
    print(f"{'='*80}\n")

    for result in results:
        log_file = result['log_file']
        question = log_file.split('/')[1]
        model = log_file.split('/')[2]

        print(f"\n{question} - {model}:")

        if 'Claude' in result and 'Qwen' in result:
            claude = result['Claude']
            qwen = result['Qwen']

            if 'error' not in claude and 'error' not in qwen:
                print(f"  Claude: {claude['total']}/6 (Completion: {claude['completion']}, Correctness: {claude['correctness']}, Tool: {claude['tool_use']})")
                print(f"  Qwen:   {qwen['total']}/6 (Completion: {qwen['completion']}, Correctness: {qwen['correctness']}, Tool: {qwen['tool_use']})")

                # Check disagreements
                if claude['total'] != qwen['total']:
                    diff = claude['total'] - qwen['total']
                    print(f"  ⚠️  DISAGREEMENT: {abs(diff)} point difference")

                    # Check if it affects pass/fail
                    claude_pass = claude['total'] >= 4
                    qwen_pass = qwen['total'] >= 4

                    if claude_pass != qwen_pass:
                        print(f"  🚨 DIFFERENT VERDICT: Claude={claude['assessment']}, Qwen={qwen['assessment']}")

    return results

if __name__ == '__main__':
    asyncio.run(compare_judges_on_samples())
