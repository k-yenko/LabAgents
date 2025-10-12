"""
Create judge comparison visualizations with consistent styling
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

def create_bland_altman_plot(df):
    """Bland-Altman plot showing agreement between judges"""
    setup_modern_style()

    fig, ax = plt.subplots(figsize=(14, 8))

    # Calculate mean and difference
    df['mean_score'] = (df['claude_total'] + df['qwen_total']) / 2
    df['diff'] = df['claude_total'] - df['qwen_total']

    # Calculate statistics
    mean_diff = df['diff'].mean()
    std_diff = df['diff'].std()
    upper_loa = mean_diff + 1.96 * std_diff  # 95% limits of agreement
    lower_loa = mean_diff - 1.96 * std_diff

    # Scatter plot
    ax.scatter(df['mean_score'], df['diff'], alpha=0.6, s=80,
              color='#7B68EE', edgecolors='white', linewidth=1.5)

    # Reference line (perfect agreement)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=2, alpha=0.3, label='Perfect Agreement')

    # Mean difference line
    ax.axhline(y=mean_diff, color='#FF6347', linestyle='--', linewidth=2.5,
              label=f'Mean Difference = {mean_diff:.2f}')

    # Limits of agreement
    ax.axhline(y=upper_loa, color='#FFD700', linestyle='--', linewidth=2,
              label=f'Upper LoA = {upper_loa:.2f}')
    ax.axhline(y=lower_loa, color='#FFD700', linestyle='--', linewidth=2,
              label=f'Lower LoA = {lower_loa:.2f}')

    # Fill between limits
    ax.fill_between([df['mean_score'].min(), df['mean_score'].max()],
                    lower_loa, upper_loa, alpha=0.1, color='yellow')

    ax.set_xlabel('Average Score (Claude + Qwen) / 2', fontsize=13, fontweight='bold')
    ax.set_ylabel('Difference (Claude - Qwen)', fontsize=13, fontweight='bold')
    ax.set_title('Bland-Altman Plot: Inter-Judge Agreement\n(98% of differences within ±2 points)',
                fontsize=15, fontweight='bold', pad=20)
    ax.legend(loc='best', frameon=True, shadow=True, fancybox=True)
    ax.grid(True, alpha=0.3)

    # Add interpretation text
    agreement_98 = (abs(df['diff']) <= 2).sum() / len(df) * 100
    ax.text(0.02, 0.98,
           f'Agreement Statistics:\n'
           f'• Within ±2 points: {agreement_98:.1f}%\n'
           f'• Mean bias: {mean_diff:.2f} (Qwen scores {abs(mean_diff):.2f} higher)\n'
           f'• Std deviation: {std_diff:.2f}',
           transform=ax.transAxes, fontsize=11, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))

    plt.tight_layout()
    plt.savefig('plots/judge_comparison/judge_bland_altman.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created plots/judge_comparison/judge_bland_altman.png")

def create_model_disagreement_chart(df):
    """Bar chart showing disagreement by model"""
    setup_modern_style()

    fig, ax = plt.subplots(figsize=(14, 8))

    # Calculate mean absolute difference per model
    model_disagreement = df.groupby('model').agg({
        'diff': ['mean', lambda x: abs(x).mean(), 'std'],
        'claude_total': 'mean'
    }).round(2)
    model_disagreement.columns = ['mean_diff', 'mean_abs_diff', 'std_diff', 'claude_mean']
    model_disagreement = model_disagreement.sort_values('mean_abs_diff', ascending=False)

    # Create color map based on disagreement level
    colors = []
    for diff in model_disagreement['mean_abs_diff']:
        if diff < 0.5:
            colors.append('#90EE90')  # Light green - high agreement
        elif diff < 1.0:
            colors.append('#FFD700')  # Gold - moderate agreement
        else:
            colors.append('#FF6347')  # Tomato - low agreement

    # Create horizontal bar chart
    y_pos = np.arange(len(model_disagreement))
    bars = ax.barh(y_pos, model_disagreement['mean_abs_diff'],
                   color=colors, edgecolor='white', linewidth=1.5, alpha=0.85)

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, model_disagreement['mean_abs_diff'])):
        ax.text(val + 0.05, bar.get_y() + bar.get_height()/2,
               f'{val:.2f}', va='center', fontsize=10, fontweight='bold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(model_disagreement.index)
    ax.set_xlabel('Mean Absolute Difference (|Claude - Qwen|)', fontsize=13, fontweight='bold')
    ax.set_title('Judge Disagreement by Model\n(Lower = Higher Agreement)',
                fontsize=15, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, axis='x')

    # Add interpretation boxes
    ax.axvline(x=0.5, color='green', linestyle='--', alpha=0.3, linewidth=2)
    ax.axvline(x=1.0, color='orange', linestyle='--', alpha=0.3, linewidth=2)

    ax.text(0.25, len(model_disagreement) - 0.5, 'High\nAgreement',
           ha='center', fontsize=9, color='darkgreen', fontweight='bold',
           bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    ax.text(0.75, len(model_disagreement) - 0.5, 'Moderate',
           ha='center', fontsize=9, color='darkorange', fontweight='bold',
           bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))

    plt.tight_layout()
    plt.savefig('plots/judge_comparison/judge_disagreement_by_model.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created plots/judge_comparison/judge_disagreement_by_model.png")

def create_dimension_agreement_heatmap(df):
    """Heatmap showing agreement metrics by dimension"""
    setup_modern_style()

    fig, ax = plt.subplots(figsize=(12, 6))

    dimensions = ['completion', 'correctness', 'tool_use', 'total']
    metrics = []

    for dim in dimensions:
        claude_col = f'claude_{dim}'
        qwen_col = f'qwen_{dim}'

        # Calculate metrics
        within_1 = (abs(df[claude_col] - df[qwen_col]) <= 1).sum() / len(df) * 100
        pearson_r, _ = pearsonr(df[claude_col], df[qwen_col])
        spearman_r, _ = spearmanr(df[claude_col], df[qwen_col])

        metrics.append([within_1, pearson_r * 100, spearman_r * 100])

    metrics_df = pd.DataFrame(metrics,
                             columns=['Within ±1 %', 'Pearson r (×100)', 'Spearman ρ (×100)'],
                             index=['Completion', 'Correctness', 'Tool Use', 'Total Score'])

    # Create heatmap
    sns.heatmap(metrics_df, annot=True, fmt='.1f', cmap='RdYlGn',
               vmin=0, vmax=100, cbar_kws={'label': 'Agreement Strength'},
               linewidths=2, linecolor='white', ax=ax,
               annot_kws={'fontsize': 11, 'fontweight': 'bold'})

    ax.set_title('Judge Agreement by Evaluation Dimension\n(Higher = Better Agreement)',
                fontsize=15, fontweight='bold', pad=20)
    ax.set_xlabel('Agreement Metric', fontsize=13, fontweight='bold')
    ax.set_ylabel('Evaluation Dimension', fontsize=13, fontweight='bold')

    plt.tight_layout()
    plt.savefig('plots/judge_comparison/judge_agreement_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created plots/judge_comparison/judge_agreement_heatmap.png")

def create_agreement_by_tier(df):
    """Agreement rates by question tier"""
    setup_modern_style()

    fig, ax = plt.subplots(figsize=(12, 7))

    # Extract tier from question
    df['tier'] = df['question'].str.extract(r'(tier\d)')[0]

    tiers = ['tier1', 'tier2', 'tier3']
    agreement_data = []

    for tier in tiers:
        tier_df = df[df['tier'] == tier]
        exact = (tier_df['claude_total'] == tier_df['qwen_total']).sum() / len(tier_df) * 100
        within_1 = (abs(tier_df['claude_total'] - tier_df['qwen_total']) <= 1).sum() / len(tier_df) * 100
        within_2 = (abs(tier_df['claude_total'] - tier_df['qwen_total']) <= 2).sum() / len(tier_df) * 100
        agreement_data.append([exact, within_1, within_2])

    agreement_df = pd.DataFrame(agreement_data,
                               columns=['Exact Match', 'Within ±1', 'Within ±2'],
                               index=['Tier 1\n(Basic)', 'Tier 2\n(Multi-tool)', 'Tier 3\n(Complex)'])

    # Create grouped bar chart
    x = np.arange(len(agreement_df))
    width = 0.25

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

    for i, (col, color) in enumerate(zip(agreement_df.columns, colors)):
        offset = (i - 1) * width
        bars = ax.bar(x + offset, agreement_df[col], width, label=col,
                     color=color, edgecolor='white', linewidth=1.5, alpha=0.85)

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{height:.1f}%', ha='center', va='bottom',
                   fontsize=10, fontweight='bold')

    ax.set_ylabel('Agreement Rate (%)', fontsize=13, fontweight='bold')
    ax.set_xlabel('Question Difficulty Tier', fontsize=13, fontweight='bold')
    ax.set_title('Judge Agreement by Question Difficulty\n(Does complexity reduce agreement?)',
                fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(agreement_df.index)
    ax.legend(frameon=True, shadow=True, fancybox=True)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, 110)

    plt.tight_layout()
    plt.savefig('plots/judge_comparison/judge_agreement_by_tier.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created plots/judge_comparison/judge_agreement_by_tier.png")

def create_bias_analysis(df):
    """Visualize systematic bias between judges"""
    setup_modern_style()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # Left: Distribution of differences
    diff_data = df['diff']

    # Histogram
    ax1.hist(diff_data, bins=range(-6, 7), color='#7B68EE', alpha=0.7,
            edgecolor='white', linewidth=1.5)

    mean_diff = diff_data.mean()
    ax1.axvline(x=mean_diff, color='red', linestyle='--', linewidth=2.5,
               label=f'Mean = {mean_diff:.2f}')
    ax1.axvline(x=0, color='black', linestyle='-', linewidth=2, alpha=0.3,
               label='Perfect Agreement')

    ax1.set_xlabel('Score Difference (Claude - Qwen)', fontsize=13, fontweight='bold')
    ax1.set_ylabel('Frequency', fontsize=13, fontweight='bold')
    ax1.set_title('Distribution of Judge Disagreements\n(Negative = Qwen more generous)',
                 fontsize=14, fontweight='bold', pad=15)
    ax1.legend(frameon=True, shadow=True)
    ax1.grid(True, alpha=0.3, axis='y')

    # Add statistics box
    ax1.text(0.98, 0.98,
            f'Statistics:\n'
            f'• Mean: {mean_diff:.2f}\n'
            f'• Median: {diff_data.median():.2f}\n'
            f'• Std: {diff_data.std():.2f}\n'
            f'• Min: {diff_data.min():.0f}\n'
            f'• Max: {diff_data.max():.0f}',
            transform=ax1.transAxes, fontsize=10, verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))

    # Right: Who scores higher per model?
    model_bias = df.groupby('model')['diff'].agg(['mean', 'count']).sort_values('mean')

    colors_bias = ['#90EE90' if x > 0 else '#FF6347' for x in model_bias['mean']]

    y_pos = np.arange(len(model_bias))
    bars = ax2.barh(y_pos, model_bias['mean'], color=colors_bias,
                   edgecolor='white', linewidth=1.5, alpha=0.85)

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, model_bias['mean'])):
        x_pos = val + (0.1 if val > 0 else -0.1)
        ha = 'left' if val > 0 else 'right'
        ax2.text(x_pos, bar.get_y() + bar.get_height()/2,
                f'{val:.2f}', va='center', ha=ha, fontsize=9, fontweight='bold')

    ax2.axvline(x=0, color='black', linestyle='-', linewidth=2, alpha=0.5)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(model_bias.index)
    ax2.set_xlabel('Mean Difference (Claude - Qwen)', fontsize=13, fontweight='bold')
    ax2.set_title('Systematic Bias by Model\n(Green = Claude harsher, Red = Qwen harsher)',
                 fontsize=14, fontweight='bold', pad=15)
    ax2.grid(True, alpha=0.3, axis='x')

    # Add zones
    ax2.text(-2.5, len(model_bias) - 0.5, 'Qwen More\nGenerous',
            ha='center', fontsize=9, color='darkred', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#FFB6B6', alpha=0.3))
    ax2.text(1.5, len(model_bias) - 0.5, 'Claude More\nGenerous',
            ha='center', fontsize=9, color='darkgreen', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#B6FFB6', alpha=0.3))

    plt.tight_layout()
    plt.savefig('plots/judge_comparison/judge_bias_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created plots/judge_comparison/judge_bias_analysis.png")

if __name__ == "__main__":
    print("🎨 Creating judge comparison visualizations...\n")

    # Load data
    print("📊 Loading judge comparison data...")
    df = pd.read_csv('analysis/judge_comparison.csv')
    print(f"   Loaded {len(df)} evaluations\n")

    # Create all plots
    print("📈 Generating plots...\n")

    create_bland_altman_plot(df)
    create_model_disagreement_chart(df)
    create_dimension_agreement_heatmap(df)
    create_agreement_by_tier(df)
    create_bias_analysis(df)

    print(f"\n✅ All judge comparison plots created in plots/")
    print("\n📊 Plot Summary:")
    print("   1. judge_bland_altman.png - Gold standard agreement plot")
    print("   2. judge_disagreement_by_model.png - Which models are hardest to judge?")
    print("   3. judge_agreement_heatmap.png - Agreement by evaluation dimension")
    print("   4. judge_agreement_by_tier.png - Does difficulty affect agreement?")
    print("   5. judge_bias_analysis.png - Systematic bias patterns")
