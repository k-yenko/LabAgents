#!/usr/bin/env python3
"""
Create judge comparison analysis including Claude Sonnet 4, Qwen, and Gemini judges
"""

import json
import glob
import pandas as pd
from pathlib import Path

def load_evaluations(eval_dir):
    """Load evaluations from a judge directory"""
    evaluations = {}

    eval_pattern = f"{eval_dir}/*/json/*_evaluation.json"
    eval_files = glob.glob(eval_pattern)

    for eval_file in eval_files:
        try:
            with open(eval_file, 'r') as f:
                data = json.load(f)

            question_id = data.get('question_id')

            # Extract model name from filename
            filename = Path(eval_file).stem
            model_name = filename.replace('_evaluation', '').replace('_', '/', 1)

            # Handle special cases
            if 'deepseek' in model_name:
                model_name = model_name.replace('_', ':', 1)
            if 'grok' in model_name and 'free' in model_name:
                model_name = model_name.replace('_free', ':free')

            key = f"{question_id}_{model_name}"
            evaluations[key] = {
                'question': question_id,
                'model': model_name,
                'total': data.get('total_score', 0),
                'completion': data.get('completion_score', 0),
                'correctness': data.get('correctness_score', 0),
                'tool_use': data.get('tool_use_score', 0)
            }
        except Exception as e:
            print(f"Error loading {eval_file}: {e}")

    return evaluations

def main():
    print("Loading evaluations from all three judges...")

    # Load evaluations from all three judges
    claude_evals = load_evaluations('evaluations_sonnet4')
    qwen_evals = load_evaluations('evaluations_qwen')
    gemini_evals = load_evaluations('evaluations_gemini')

    print(f"  Claude: {len(claude_evals)} evaluations")
    print(f"  Qwen: {len(qwen_evals)} evaluations")
    print(f"  Gemini: {len(gemini_evals)} evaluations")

    # Find common evaluations (intersection of all three)
    common_keys = set(claude_evals.keys()) & set(qwen_evals.keys()) & set(gemini_evals.keys())
    print(f"\nCommon evaluations: {len(common_keys)}")

    # Build comparison dataframe
    rows = []
    for key in sorted(common_keys):
        claude = claude_evals[key]
        qwen = qwen_evals[key]
        gemini = gemini_evals[key]

        rows.append({
            'question': claude['question'],
            'model': claude['model'],
            'claude_total': claude['total'],
            'claude_completion': claude['completion'],
            'claude_correctness': claude['correctness'],
            'claude_tool_use': claude['tool_use'],
            'qwen_total': qwen['total'],
            'qwen_completion': qwen['completion'],
            'qwen_correctness': qwen['correctness'],
            'qwen_tool_use': qwen['tool_use'],
            'gemini_total': gemini['total'],
            'gemini_completion': gemini['completion'],
            'gemini_correctness': gemini['correctness'],
            'gemini_tool_use': gemini['tool_use'],
            'diff_claude_qwen': claude['total'] - qwen['total'],
            'diff_claude_gemini': claude['total'] - gemini['total'],
            'diff_qwen_gemini': qwen['total'] - gemini['total'],
            'abs_diff_claude_qwen': abs(claude['total'] - qwen['total']),
            'abs_diff_claude_gemini': abs(claude['total'] - gemini['total']),
            'abs_diff_qwen_gemini': abs(qwen['total'] - gemini['total'])
        })

    df = pd.DataFrame(rows)

    # Save to CSV
    output_path = 'analysis/three_judge_comparison.csv'
    df.to_csv(output_path, index=False)
    print(f"\n✅ Saved to {output_path}")

    # Print summary statistics
    print("\n" + "="*70)
    print("THREE-JUDGE COMPARISON SUMMARY")
    print("="*70)
    print(f"\nTotal evaluations: {len(df)}")
    print(f"\nMean differences:")
    print(f"  Claude vs Qwen:   {df['diff_claude_qwen'].mean():+.3f} (Claude {'harsher' if df['diff_claude_qwen'].mean() < 0 else 'more lenient'})")
    print(f"  Claude vs Gemini: {df['diff_claude_gemini'].mean():+.3f} (Claude {'harsher' if df['diff_claude_gemini'].mean() < 0 else 'more lenient'})")
    print(f"  Qwen vs Gemini:   {df['diff_qwen_gemini'].mean():+.3f} (Qwen {'harsher' if df['diff_qwen_gemini'].mean() < 0 else 'more lenient'})")

    print(f"\nMean absolute differences:")
    print(f"  Claude vs Qwen:   {df['abs_diff_claude_qwen'].mean():.3f}")
    print(f"  Claude vs Gemini: {df['abs_diff_claude_gemini'].mean():.3f}")
    print(f"  Qwen vs Gemini:   {df['abs_diff_qwen_gemini'].mean():.3f}")

    print(f"\nAgreement within ±1 point:")
    print(f"  Claude vs Qwen:   {(df['abs_diff_claude_qwen'] <= 1).sum() / len(df) * 100:.1f}%")
    print(f"  Claude vs Gemini: {(df['abs_diff_claude_gemini'] <= 1).sum() / len(df) * 100:.1f}%")
    print(f"  Qwen vs Gemini:   {(df['abs_diff_qwen_gemini'] <= 1).sum() / len(df) * 100:.1f}%")

    print(f"\nAgreement within ±2 points:")
    print(f"  Claude vs Qwen:   {(df['abs_diff_claude_qwen'] <= 2).sum() / len(df) * 100:.1f}%")
    print(f"  Claude vs Gemini: {(df['abs_diff_claude_gemini'] <= 2).sum() / len(df) * 100:.1f}%")
    print(f"  Qwen vs Gemini:   {(df['abs_diff_qwen_gemini'] <= 2).sum() / len(df) * 100:.1f}%")
    print("="*70)

if __name__ == "__main__":
    main()
