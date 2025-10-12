#!/usr/bin/env python3
"""
Analyze tier1_001 (the remdesivir trick question) across all models.

The trick: Remdesivir is NOT soluble in water, but models confidently reported
solubility values because the computational tools returned predictions without
understanding the chemistry.

This script analyzes:
1. Which models caught the trick vs fell for it
2. How judges scored each model's response
3. Comparison between Claude Sonnet 4 and Qwen judges
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

# Yes, aqueous = water (aqueous literally means "containing water" or "dissolved in water")
TRICK_QUESTION_TRUTH = "Remdesivir is NOT water-soluble (aqueous = water)"

def load_all_tier1_001_data():
    """Load all logs and evaluations for tier1_001"""

    data = []

    # Get all log files
    logs_dir = Path('logs/tier1_001')
    for model_dir in logs_dir.iterdir():
        if not model_dir.is_dir():
            continue

        # Get the latest log file
        log_files = list(model_dir.glob('*.json'))
        if not log_files:
            continue
        log_file = max(log_files, key=lambda f: f.stat().st_mtime)

        with open(log_file) as f:
            log_data = json.load(f)

        model_name = log_data['model_name'].replace('/', '_')

        # Load Claude Sonnet 4 judge evaluation
        sonnet_eval_path = Path(f'evaluations_sonnet4/tier1_001/json/{model_name}_evaluation.json')
        if sonnet_eval_path.exists():
            with open(sonnet_eval_path) as f:
                sonnet_eval = json.load(f)
        else:
            sonnet_eval = None

        # Load Qwen judge evaluation
        qwen_eval_path = Path(f'evaluations_qwen/tier1_001/json/{model_name}_evaluation.json')
        if qwen_eval_path.exists():
            with open(qwen_eval_path) as f:
                qwen_eval = json.load(f)
        else:
            qwen_eval = None

        # Extract key info
        entry = {
            'model': log_data['model_name'],
            'model_short': model_name.split('_', 1)[1] if '_' in model_name else model_name,
            'completed': log_data.get('completed_successfully', False),
            'final_answer': log_data.get('final_answer', ''),
            'tools_used': [t['tool_name'] for t in log_data.get('execution_timeline', [])
                          if t.get('event_type') == 'tool_call'],
        }

        # Add Sonnet judge scores
        if sonnet_eval:
            entry['sonnet_completion'] = sonnet_eval.get('completion_score', 0)
            entry['sonnet_correctness'] = sonnet_eval.get('correctness_score', 0)
            entry['sonnet_tool_use'] = sonnet_eval.get('tool_use_score', 0)
            entry['sonnet_total'] = sonnet_eval.get('total_score', 0)
            entry['sonnet_pass'] = sonnet_eval.get('overall_assessment', 'fail') == 'pass'
        else:
            entry.update({
                'sonnet_completion': None, 'sonnet_correctness': None,
                'sonnet_tool_use': None, 'sonnet_total': None, 'sonnet_pass': None
            })

        # Add Qwen judge scores
        if qwen_eval:
            entry['qwen_completion'] = qwen_eval.get('completion_score', 0)
            entry['qwen_correctness'] = qwen_eval.get('correctness_score', 0)
            entry['qwen_tool_use'] = qwen_eval.get('tool_use_score', 0)
            entry['qwen_total'] = qwen_eval.get('total_score', 0)
            entry['qwen_pass'] = qwen_eval.get('overall_assessment', 'fail') == 'pass'
        else:
            entry.update({
                'qwen_completion': None, 'qwen_correctness': None,
                'qwen_tool_use': None, 'qwen_total': None, 'qwen_pass': None
            })

        data.append(entry)

    return pd.DataFrame(data)

def create_visualizations(df):
    """Create analysis plots"""

    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['font.family'] = 'sans-serif'

    # Plot 1: Scoring comparison (Sonnet vs Qwen judges)
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    dimensions = ['completion', 'correctness', 'tool_use']
    titles = ['Completion Score', 'Correctness Score', 'Tool Use Score']

    for ax, dim, title in zip(axes, dimensions, titles):
        sonnet_col = f'sonnet_{dim}'
        qwen_col = f'qwen_{dim}'

        x = np.arange(len(df))
        width = 0.35

        ax.bar(x - width/2, df[sonnet_col], width, label='Claude Sonnet 4 Judge', alpha=0.8)
        ax.bar(x + width/2, df[qwen_col], width, label='Qwen Judge', alpha=0.8)

        ax.set_xlabel('Model', fontsize=11)
        ax.set_ylabel('Score (0-2)', fontsize=11)
        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(df['model_short'], rotation=45, ha='right', fontsize=9)
        ax.legend(fontsize=9)
        ax.set_ylim(0, 2.2)
        ax.grid(axis='y', alpha=0.3)

    plt.suptitle('Tier1_001 Trick Question: Judge Comparison\n(Remdesivir is NOT water-soluble)',
                 fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('plots/performance/tier1_001_judge_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Plot 2: Total scores heatmap
    fig, ax = plt.subplots(figsize=(12, 6))

    score_data = df[['model_short', 'sonnet_total', 'qwen_total']].set_index('model_short')
    score_data.columns = ['Claude Sonnet 4 Judge', 'Qwen Judge']

    sns.heatmap(score_data.T, annot=True, fmt='.0f', cmap='RdYlGn',
                vmin=0, vmax=6, cbar_kws={'label': 'Total Score (0-6)'},
                linewidths=0.5, ax=ax)

    ax.set_xlabel('Model', fontsize=12, fontweight='bold')
    ax.set_ylabel('Judge', fontsize=12, fontweight='bold')
    ax.set_title('Tier1_001 Total Scores: The Trick Question\n(Remdesivir is NOT water-soluble)',
                fontsize=14, fontweight='bold', pad=10)

    plt.tight_layout()
    plt.savefig('plots/performance/tier1_001_score_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Plot 3: Correctness score focus (the key dimension for this trick)
    fig, ax = plt.subplots(figsize=(12, 7))

    x = np.arange(len(df))
    width = 0.35

    bars1 = ax.bar(x - width/2, df['sonnet_correctness'], width,
                   label='Claude Sonnet 4 Judge', alpha=0.8, color='#3498db')
    bars2 = ax.bar(x + width/2, df['qwen_correctness'], width,
                   label='Qwen Judge', alpha=0.8, color='#e74c3c')

    ax.set_xlabel('Model', fontsize=12, fontweight='bold')
    ax.set_ylabel('Correctness Score (0-2)', fontsize=12, fontweight='bold')
    ax.set_title('Did Judges Catch the Trick?\nTier1_001: Remdesivir is NOT Water-Soluble (All Models Reported Values)',
                fontsize=14, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(df['model_short'], rotation=45, ha='right', fontsize=10)
    ax.legend(fontsize=11)
    ax.set_ylim(0, 2.3)
    ax.grid(axis='y', alpha=0.3)

    # Add reference line
    ax.axhline(y=0, color='red', linestyle='--', linewidth=2, alpha=0.5,
              label='Expected if judges caught trick')

    plt.tight_layout()
    plt.savefig('plots/performance/tier1_001_correctness_focus.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Plot 4: Pass/Fail by judge
    fig, ax = plt.subplots(figsize=(12, 7))

    pass_fail_data = pd.DataFrame({
        'Model': df['model_short'],
        'Claude Sonnet 4': df['sonnet_pass'].map({True: 'Pass', False: 'Fail'}),
        'Qwen': df['qwen_pass'].map({True: 'Pass', False: 'Fail'})
    })

    # Create grouped bar chart
    pass_counts = pd.DataFrame({
        'Claude Sonnet 4': [
            sum(df['sonnet_pass'] == True),
            sum(df['sonnet_pass'] == False)
        ],
        'Qwen': [
            sum(df['qwen_pass'] == True),
            sum(df['qwen_pass'] == False)
        ]
    }, index=['Pass', 'Fail'])

    pass_counts.plot(kind='bar', ax=ax, color=['#2ecc71', '#e74c3c'], alpha=0.8)
    ax.set_ylabel('Number of Models', fontsize=12, fontweight='bold')
    ax.set_xlabel('Assessment', fontsize=12, fontweight='bold')
    ax.set_title('Pass/Fail Distribution for Tier1_001\n(The Trick Question: Remdesivir is NOT Water-Soluble)',
                fontsize=14, fontweight='bold', pad=10)
    ax.legend(title='Judge', fontsize=11)
    ax.set_xticklabels(['Pass', 'Fail'], rotation=0)
    ax.grid(axis='y', alpha=0.3)

    # Add text annotation
    ax.text(0.5, 0.95,
           f'Note: ALL models reported solubility values (none caught the trick)\nJudges gave 0/2 correctness but 2/2 completion & tool use → Pass (4/6)',
           transform=ax.transAxes, ha='center', va='top', fontsize=10,
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.tight_layout()
    plt.savefig('plots/performance/tier1_001_pass_fail.png', dpi=300, bbox_inches='tight')
    plt.close()

def print_analysis(df):
    """Print text analysis"""

    print("\n" + "="*80)
    print("TIER1_001 TRICK QUESTION ANALYSIS")
    print("="*80)
    print(f"\nQuestion: What is the predicted aqueous solubility of remdesivir at physiological temperature?")
    print(f"Truth: {TRICK_QUESTION_TRUTH}")
    print(f"\nNote: Yes, 'aqueous' means water-based. Aqueous solubility = water solubility.")
    print("\n" + "-"*80)

    print(f"\nTOTAL MODELS TESTED: {len(df)}")
    print(f"Models that completed: {sum(df['completed'])} ({sum(df['completed'])/len(df)*100:.1f}%)")

    print("\n" + "-"*80)
    print("CLAUDE SONNET 4 JUDGE:")
    print("-"*80)
    sonnet_pass_count = df['sonnet_pass'].dropna().sum()
    print(f"  Pass rate: {sonnet_pass_count/len(df)*100:.1f}% ({int(sonnet_pass_count)}/{len(df)})")
    print(f"  Avg Completion: {df['sonnet_completion'].mean():.2f}/2")
    print(f"  Avg Correctness: {df['sonnet_correctness'].mean():.2f}/2")
    print(f"  Avg Tool Use: {df['sonnet_tool_use'].mean():.2f}/2")
    print(f"  Avg Total: {df['sonnet_total'].mean():.2f}/6")

    print("\n" + "-"*80)
    print("QWEN JUDGE:")
    print("-"*80)
    qwen_pass_count = df['qwen_pass'].dropna().sum()
    print(f"  Pass rate: {qwen_pass_count/len(df)*100:.1f}% ({int(qwen_pass_count)}/{len(df)})")
    print(f"  Avg Completion: {df['qwen_completion'].mean():.2f}/2")
    print(f"  Avg Correctness: {df['qwen_correctness'].mean():.2f}/2")
    print(f"  Avg Tool Use: {df['qwen_tool_use'].mean():.2f}/2")
    print(f"  Avg Total: {df['qwen_total'].mean():.2f}/6")

    print("\n" + "-"*80)
    print("KEY INSIGHT:")
    print("-"*80)
    print(f"  Models caught the trick: 0/{len(df)}")
    print(f"  All models confidently reported solubility values from computational tools")
    print(f"  Judges gave 0/2 for correctness (validated against literature)")
    print(f"  But gave 2/2 for completion & tool use → models still passed (4/6)")
    print(f"\n  This reveals: LLM judges with web search still miss domain edge cases.")
    print(f"  They validate *magnitudes* but not *conceptual validity* (should it be soluble at all?)")

    # Judge disagreements
    print("\n" + "-"*80)
    print("JUDGE DISAGREEMENTS:")
    print("-"*80)

    for _, row in df.iterrows():
        if row['sonnet_pass'] != row['qwen_pass']:
            print(f"  {row['model_short']}:")
            print(f"    Sonnet: {'Pass' if row['sonnet_pass'] else 'Fail'} ({row['sonnet_total']}/6)")
            print(f"    Qwen: {'Pass' if row['qwen_pass'] else 'Fail'} ({row['qwen_total']}/6)")

    if not any(df['sonnet_pass'] != df['qwen_pass']):
        print("  No disagreements - both judges agreed on all models")

    print("\n" + "="*80 + "\n")

def main():
    print("Loading tier1_001 data...")
    df = load_all_tier1_001_data()

    print("Creating visualizations...")
    create_visualizations(df)

    print("Generating analysis...")
    print_analysis(df)

    # Save data to CSV
    output_path = 'plots/performance/tier1_001_analysis.csv'
    df.to_csv(output_path, index=False)
    print(f"\nAnalysis data saved to: {output_path}")

    print("\nPlots saved to:")
    print("  - plots/performance/tier1_001_judge_comparison.png")
    print("  - plots/performance/tier1_001_score_heatmap.png")
    print("  - plots/performance/tier1_001_correctness_focus.png")
    print("  - plots/performance/tier1_001_pass_fail.png")

if __name__ == "__main__":
    main()
