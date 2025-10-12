#!/usr/bin/env python3
"""
Create judge comparison visualizations for three judges: Claude, Qwen, Gemini
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.stats import pearsonr, spearmanr

def setup_modern_style():
    """Match the style from overall_performance.png"""
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    plt.rcParams['font.size'] = 11
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.titleweight'] = 'bold'
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 10
    plt.rcParams['axes.grid'] = True
    plt.rcParams['grid.alpha'] = 0.3
    plt.rcParams['axes.edgecolor'] = '#333333'
    plt.rcParams['axes.linewidth'] = 1.2

def create_three_judge_bias_delta(df):
    """Bar chart showing mean differences between all three judges"""
    setup_modern_style()

    fig, ax = plt.subplots(figsize=(12, 7))

    # Calculate mean differences per model
    model_stats = df.groupby('model').agg({
        'diff_claude_qwen': 'mean',
        'diff_claude_gemini': 'mean',
        'diff_qwen_gemini': 'mean'
    }).round(2)

    # Sort by average absolute difference
    model_stats['avg_abs'] = (abs(model_stats['diff_claude_qwen']) +
                               abs(model_stats['diff_claude_gemini']) +
                               abs(model_stats['diff_qwen_gemini'])) / 3
    model_stats = model_stats.sort_values('avg_abs', ascending=False)

    # Create grouped bar chart
    x = np.arange(len(model_stats))
    width = 0.25

    bars1 = ax.bar(x - width, model_stats['diff_claude_qwen'], width,
                   label='Claude - Qwen', color='#8B5CF6', alpha=0.85)
    bars2 = ax.bar(x, model_stats['diff_claude_gemini'], width,
                   label='Claude - Gemini', color='#10B981', alpha=0.85)
    bars3 = ax.bar(x + width, model_stats['diff_qwen_gemini'], width,
                   label='Qwen - Gemini', color='#F59E0B', alpha=0.85)

    # Add horizontal line at y=0
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1.5, alpha=0.3)

    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if abs(height) > 0.1:  # Only label if significant
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:+.2f}', ha='center',
                       va='bottom' if height > 0 else 'top',
                       fontsize=8, fontweight='bold')

    ax.set_xlabel('Model', fontsize=13, fontweight='bold')
    ax.set_ylabel('Mean Score Difference', fontsize=13, fontweight='bold')
    ax.set_title('Judge Bias by Model\n(Positive = First judge more lenient)',
                fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(model_stats.index, rotation=45, ha='right')
    ax.legend(loc='best', frameon=True, shadow=True, fancybox=True)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('plots/judge_comparison/judge_bias_delta.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created plots/judge_comparison/judge_bias_delta.png")

def create_three_judge_agreement_heatmap(df):
    """Heatmap showing pairwise agreement between all three judges"""
    setup_modern_style()

    fig, ax = plt.subplots(figsize=(10, 6))

    # Calculate agreement metrics for each pair
    pairs = [
        ('claude_total', 'qwen_total', 'Claude vs Qwen'),
        ('claude_total', 'gemini_total', 'Claude vs Gemini'),
        ('qwen_total', 'gemini_total', 'Qwen vs Gemini')
    ]

    metrics = []
    for col1, col2, label in pairs:
        within_1 = (abs(df[col1] - df[col2]) <= 1).sum() / len(df) * 100
        within_2 = (abs(df[col1] - df[col2]) <= 2).sum() / len(df) * 100
        pearson_r, _ = pearsonr(df[col1], df[col2])
        spearman_r, _ = spearmanr(df[col1], df[col2])

        metrics.append([within_1, within_2, pearson_r * 100, spearman_r * 100])

    metrics_df = pd.DataFrame(metrics,
                             columns=['Within ±1 %', 'Within ±2 %', 'Pearson r (×100)', 'Spearman ρ (×100)'],
                             index=[p[2] for p in pairs])

    # Create heatmap
    sns.heatmap(metrics_df, annot=True, fmt='.1f', cmap='RdYlGn',
               vmin=0, vmax=100, cbar_kws={'label': 'Agreement Strength'},
               linewidths=2, linecolor='white', ax=ax,
               annot_kws={'fontsize': 11, 'fontweight': 'bold'})

    ax.set_title('Three-Judge Agreement Metrics\n(Higher = Better Agreement)',
                fontsize=15, fontweight='bold', pad=20)
    ax.set_xlabel('Agreement Metric', fontsize=13, fontweight='bold')
    ax.set_ylabel('Judge Pair', fontsize=13, fontweight='bold')

    plt.tight_layout()
    plt.savefig('plots/judge_comparison/three_judge_agreement_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created plots/judge_comparison/three_judge_agreement_heatmap.png")

def create_model_disagreement_by_judge_pair(df):
    """Show which models have most disagreement for each judge pair"""
    setup_modern_style()

    fig, axes = plt.subplots(3, 1, figsize=(14, 12))

    pairs = [
        ('abs_diff_claude_qwen', 'Claude vs Qwen', '#8B5CF6'),
        ('abs_diff_claude_gemini', 'Claude vs Gemini', '#10B981'),
        ('abs_diff_qwen_gemini', 'Qwen vs Gemini', '#F59E0B')
    ]

    for ax, (col, title, color) in zip(axes, pairs):
        # Calculate mean absolute difference per model
        model_disagreement = df.groupby('model')[col].mean().sort_values(ascending=False)

        # Create horizontal bar chart
        y_pos = np.arange(len(model_disagreement))
        bars = ax.barh(y_pos, model_disagreement.values,
                       color=color, edgecolor='white', linewidth=1.5, alpha=0.85)

        # Add value labels
        for i, (bar, val) in enumerate(zip(bars, model_disagreement.values)):
            ax.text(val + 0.05, bar.get_y() + bar.get_height()/2,
                   f'{val:.2f}', va='center', fontsize=10, fontweight='bold')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(model_disagreement.index)
        ax.set_xlabel('Mean Absolute Difference', fontsize=12, fontweight='600')
        ax.set_title(f'{title} Disagreement by Model',
                    fontsize=13, fontweight='bold', pad=10)
        ax.grid(True, alpha=0.3, axis='x')
        ax.set_xlim(0, max(model_disagreement.values) * 1.15)

    plt.tight_layout()
    plt.savefig('plots/judge_comparison/three_judge_disagreement_by_model.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created plots/judge_comparison/three_judge_disagreement_by_model.png")

def create_dimension_comparison(df):
    """Compare agreement across evaluation dimensions for each judge pair"""
    setup_modern_style()

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    dimensions = ['completion', 'correctness', 'tool_use']
    pairs = [
        ('claude', 'qwen', 'Claude vs Qwen', '#8B5CF6'),
        ('claude', 'gemini', 'Claude vs Gemini', '#10B981'),
        ('qwen', 'gemini', 'Qwen vs Gemini', '#F59E0B')
    ]

    for ax, (judge1, judge2, title, color) in zip(axes, pairs):
        agreement_rates = []

        for dim in dimensions:
            col1 = f'{judge1}_{dim}'
            col2 = f'{judge2}_{dim}'
            within_1 = (abs(df[col1] - df[col2]) <= 1).sum() / len(df) * 100
            agreement_rates.append(within_1)

        # Create bar chart
        x = np.arange(len(dimensions))
        bars = ax.bar(x, agreement_rates, color=color, alpha=0.85,
                     edgecolor='white', linewidth=2)

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{height:.1f}%', ha='center', va='bottom',
                   fontsize=11, fontweight='bold')

        ax.set_xticks(x)
        ax.set_xticklabels([d.title() for d in dimensions])
        ax.set_ylabel('Agreement Within ±1 (%)', fontsize=12, fontweight='600')
        ax.set_title(title, fontsize=13, fontweight='bold', pad=10)
        ax.set_ylim(0, 110)
        ax.grid(True, alpha=0.3, axis='y')

    plt.suptitle('Agreement by Evaluation Dimension Across Judge Pairs',
                fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('plots/judge_comparison/three_judge_dimension_agreement.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created plots/judge_comparison/three_judge_dimension_agreement.png")

if __name__ == "__main__":
    print("🎨 Creating three-judge comparison visualizations...\n")

    # Load data
    print("📊 Loading three-judge comparison data...")
    df = pd.read_csv('analysis/three_judge_comparison.csv')
    print(f"   Loaded {len(df)} evaluations\n")

    # Create all plots
    print("📈 Generating plots...\n")

    create_three_judge_bias_delta(df)
    create_three_judge_agreement_heatmap(df)
    create_model_disagreement_by_judge_pair(df)
    create_dimension_comparison(df)

    print(f"\n✅ All three-judge comparison plots created in plots/judge_comparison/")
