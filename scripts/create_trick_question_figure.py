#!/usr/bin/env python3
"""
Create a single comprehensive figure for the tier1_001 trick question analysis.

Shows:
1. All models confidently reported values
2. Judges caught the error (0 correctness)
3. But still passed some (raises evaluation design questions)
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import numpy as np

def load_tier1_001_data():
    """Load all logs and evaluations for tier1_001"""
    data = []
    logs_dir = Path('logs/tier1_001')

    for model_dir in logs_dir.iterdir():
        if not model_dir.is_dir():
            continue

        log_files = list(model_dir.glob('*.json'))
        if not log_files:
            continue
        log_file = max(log_files, key=lambda f: f.stat().st_mtime)

        with open(log_file) as f:
            log_data = json.load(f)

        model_name = log_data['model_name'].replace('/', '_')

        # Load evaluations
        sonnet_eval_path = Path(f'evaluations_sonnet4/tier1_001/json/{model_name}_evaluation.json')
        qwen_eval_path = Path(f'evaluations_qwen/tier1_001/json/{model_name}_evaluation.json')

        sonnet_eval = json.load(open(sonnet_eval_path)) if sonnet_eval_path.exists() else None
        qwen_eval = json.load(open(qwen_eval_path)) if qwen_eval_path.exists() else None

        # Get model display name
        model_display = log_data['model_name'].split('/')[-1]

        entry = {
            'model': model_display,
            'completed': log_data.get('completed_successfully', False),
            'sonnet_completion': sonnet_eval.get('completion_score', 0) if sonnet_eval else 0,
            'sonnet_correctness': sonnet_eval.get('correctness_score', 0) if sonnet_eval else 0,
            'sonnet_tool_use': sonnet_eval.get('tool_use_score', 0) if sonnet_eval else 0,
            'sonnet_total': sonnet_eval.get('total_score', 0) if sonnet_eval else 0,
            'sonnet_pass': sonnet_eval.get('overall_assessment', 'fail') == 'pass' if sonnet_eval else False,
            'qwen_completion': qwen_eval.get('completion_score', 0) if qwen_eval else 0,
            'qwen_correctness': qwen_eval.get('correctness_score', 0) if qwen_eval else 0,
            'qwen_tool_use': qwen_eval.get('tool_use_score', 0) if qwen_eval else 0,
            'qwen_total': qwen_eval.get('total_score', 0) if qwen_eval else 0,
            'qwen_pass': qwen_eval.get('overall_assessment', 'fail') == 'pass' if qwen_eval else False,
        }
        data.append(entry)

    return pd.DataFrame(data)

def create_figure(df):
    """Create comprehensive single figure"""

    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1.2, 0.8], hspace=0.35, wspace=0.3)

    # Colors
    color_completion = '#3498db'
    color_correctness = '#e74c3c'
    color_tool = '#2ecc71'
    color_pass = '#27ae60'
    color_fail = '#c0392b'

    models = df['model'].tolist()
    x = np.arange(len(models))

    # ============ Panel 1: All models reported values ============
    ax1 = fig.add_subplot(gs[0, :])

    completed_values = [1 if c else 0 for c in df['completed']]
    bars = ax1.barh(x, completed_values, color='#95a5a6', alpha=0.8)

    # Color completed ones green
    for i, (bar, completed) in enumerate(zip(bars, df['completed'])):
        if completed:
            bar.set_color('#27ae60')

    ax1.set_yticks(x)
    ax1.set_yticklabels(models, fontsize=10)
    ax1.set_xlim(0, 1.2)
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(['Did not complete', 'Reported solubility values'], fontsize=10)
    ax1.set_title('① All 9 Models Confidently Reported Solubility Values\n(But remdesivir is NOT water-soluble)',
                  fontsize=13, fontweight='bold', pad=15)
    ax1.invert_yaxis()

    # Add checkmarks
    for i, completed in enumerate(df['completed']):
        if completed:
            ax1.text(1.05, i, '✓', va='center', fontsize=16, color='#27ae60', fontweight='bold')

    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.grid(axis='x', alpha=0.3)

    # ============ Panel 2: Judges caught the error (breakdown) ============
    ax2 = fig.add_subplot(gs[1, :])

    width = 0.25
    x_pos = np.arange(len(models))

    # Claude Sonnet 4 Judge
    ax2.bar(x_pos - width, df['sonnet_completion'], width,
            label='Completion', color=color_completion, alpha=0.85)
    ax2.bar(x_pos, df['sonnet_correctness'], width,
            label='Correctness', color=color_correctness, alpha=0.85)
    ax2.bar(x_pos + width, df['sonnet_tool_use'], width,
            label='Tool Use', color=color_tool, alpha=0.85)

    ax2.set_ylabel('Score (0-2)', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Model', fontsize=11, fontweight='bold')
    ax2.set_title('② Judges Caught the Error: 0/2 Correctness (Claude Sonnet 4 Judge)',
                  fontsize=13, fontweight='bold', pad=15)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(models, rotation=45, ha='right', fontsize=9)
    ax2.set_ylim(0, 2.3)
    ax2.legend(loc='upper right', fontsize=10, ncol=3)
    ax2.grid(axis='y', alpha=0.3)

    # Add red box around correctness scores
    rect = mpatches.Rectangle((-0.5, -0.1), len(models), 0.2,
                             linewidth=3, edgecolor='red', facecolor='none',
                             linestyle='--', alpha=0.6)
    ax2.add_patch(rect)
    ax2.text(len(models)/2, -0.35, '← All got 0/2 correctness',
            ha='center', fontsize=11, color='red', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # ============ Panel 3: But still passed (the question) ============
    ax3_left = fig.add_subplot(gs[2, 0])

    pass_fail_counts = pd.DataFrame({
        'Sonnet': [df['sonnet_pass'].sum(), (~df['sonnet_pass']).sum()],
        'Qwen': [df['qwen_pass'].sum(), (~df['qwen_pass']).sum()]
    }, index=['Pass (≥4/6)', 'Fail (<4/6)'])

    pass_fail_counts.plot(kind='bar', ax=ax3_left,
                         color=[color_pass, '#e67e22'], alpha=0.85, width=0.7)
    ax3_left.set_ylabel('Number of Models', fontsize=11, fontweight='bold')
    ax3_left.set_xlabel('', fontsize=11)
    ax3_left.set_title('③ But Many Still Passed',
                      fontsize=13, fontweight='bold', pad=10)
    ax3_left.set_xticklabels(['Pass (≥4/6)', 'Fail (<4/6)'], rotation=0, fontsize=10)
    ax3_left.legend(title='Judge', fontsize=9, title_fontsize=10)
    ax3_left.grid(axis='y', alpha=0.3)
    ax3_left.set_ylim(0, 10)

    # ============ Panel 4: The evaluation design question ============
    ax3_right = fig.add_subplot(gs[2, 1])
    ax3_right.axis('off')

    question_text = """
The Evaluation Design Question:

Should a model PASS when:
  ✓ Completed the task (2/2)
  ✗ Got the answer wrong (0/2)
  ✓ Used tools correctly (2/2)

= 4/6 total = PASS

Is "correct tool use" sufficient for passing,
even when the answer is fundamentally wrong?

This raises important questions for eval design:
• Should correctness be weighted more heavily?
• Should certain dimensions be required minimums?
• Is binary pass/fail (≥4/6) the right threshold?
    """

    ax3_right.text(0.5, 0.5, question_text.strip(),
                  transform=ax3_right.transAxes,
                  fontsize=11, va='center', ha='center',
                  bbox=dict(boxstyle='round,pad=1', facecolor='#fff3cd',
                           alpha=0.9, edgecolor='#ff6b6b', linewidth=2),
                  family='monospace', linespacing=1.8)

    # ============ Overall title ============
    fig.suptitle('The Trick Question: Remdesivir Aqueous Solubility\n' +
                'All Models Fell For It, Judges Caught It, But Some Still Passed',
                fontsize=16, fontweight='bold', y=0.98)

    # Save
    plt.savefig('plots/performance/tier1_001_trick_question.png',
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print("\nFigure saved to: plots/performance/tier1_001_trick_question.png")

def main():
    print("Loading tier1_001 data...")
    df = load_tier1_001_data()

    print("Creating comprehensive figure...")
    create_figure(df)

    print("\n" + "="*70)
    print("SUMMARY STATS")
    print("="*70)
    print(f"Total models: {len(df)}")
    print(f"Completed task: {df['completed'].sum()}/{len(df)}")
    print(f"Avg correctness (Sonnet): {df['sonnet_correctness'].mean():.2f}/2")
    print(f"Avg correctness (Qwen): {df['qwen_correctness'].mean():.2f}/2")
    print(f"Passed anyway (Sonnet): {df['sonnet_pass'].sum()}/{len(df)} ({df['sonnet_pass'].sum()/len(df)*100:.0f}%)")
    print(f"Passed anyway (Qwen): {df['qwen_pass'].sum()}/{len(df)} ({df['qwen_pass'].sum()/len(df)*100:.0f}%)")
    print("="*70)

if __name__ == "__main__":
    main()
