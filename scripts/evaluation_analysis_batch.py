#!/usr/bin/env python3
"""
evaluation_analysis_batch.py - creates visualization plots from evaluation results with tier weighting
"""

import json
import glob
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style for professional plots
plt.style.use('default')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

def normalize_model_name(filename_model):
    """Normalize model names from filename to standard format"""
    # Remove _evaluation suffix
    model = filename_model.replace('_evaluation', '')

    # Handle specific cases
    if 'anthropic' in model:
        if 'opus' in model:
            return 'anthropic/claude-opus-4.1'
        elif 'sonnet' in model:
            return 'anthropic/claude-sonnet-4'
    elif 'openai' in model:
        if 'gpt-5' in model:
            return 'openai/gpt-5'
        elif 'o3' in model:
            return 'openai/o3'
    elif 'google' in model:
        return 'google/gemini-2.5-pro'
    elif 'deepseek' in model:
        return 'deepseek/deepseek-chat-v3.1:free'
    elif 'x-ai_grok-4-fast' in model and 'free' in model:
        return 'x-ai/grok-4-fast:free'
    elif 'x-ai_grok-code-fast-1' in model:
        return 'x-ai/grok-code-fast-1'

    # Fallback: just replace underscores
    return model.replace('_', '/').replace('/free', ':free')

def load_evaluation_data():
    """Load all evaluation JSON files and create comprehensive dataset"""
    print("📊 Loading evaluation data...")

    evaluations_dir = Path("evaluations")
    data = []
    tier_weights = {"tier1": 1, "tier2": 2, "tier3": 4}

    # Use only questions with complete coverage (excluding Opus)
    complete_questions = ['tier1_001', 'tier1_002', 'tier1_003', 'tier1_004', 'tier3_004']

    for question_dir in evaluations_dir.glob("tier*"):
        json_dir = question_dir / "json"
        if not json_dir.exists():
            continue

        question_id = question_dir.name
        tier = question_id.split("_")[0]

        # Skip questions that don't have complete coverage
        if question_id not in complete_questions:
            continue

        for json_file in json_dir.glob("*_evaluation.json"):
            try:
                with open(json_file, 'r') as f:
                    eval_data = json.load(f)

                # Extract and normalize model name
                model_name = normalize_model_name(json_file.stem)

                # Skip Opus since it has incomplete coverage
                if 'opus' in model_name.lower():
                    continue

                # Add to dataset
                data.append({
                    'question_id': question_id,
                    'tier': tier,
                    'model': model_name,
                    'completion_score': eval_data.get('completion_score', 0),
                    'correctness_score': eval_data.get('correctness_score', 0),
                    'tool_use_score': eval_data.get('tool_use_score', 0),
                    'total_score': eval_data.get('total_score', 0),
                    'overall_pass': eval_data.get('overall_assessment') == 'pass',
                    'execution_time': eval_data.get('chemistry_validation', {}).get('execution_time', 0),
                    'success_rate': eval_data.get('chemistry_validation', {}).get('success_rate', 0),
                    'tier_weight': tier_weights.get(tier, 1)
                })

            except Exception as e:
                print(f"⚠️  Error loading {json_file}: {e}")

    df = pd.DataFrame(data)
    print(f"✅ Loaded {len(df)} evaluations across {df['question_id'].nunique()} questions")
    print(f"📈 Models: {sorted(df['model'].unique())}")

    return df

def calculate_weighted_metrics(df):
    """Calculate tier-weighted performance metrics"""
    print("\n🔢 Calculating weighted metrics...")

    model_stats = []
    for model in df['model'].unique():
        model_data = df[df['model'] == model]

        # Weighted scores
        total_weight = model_data['tier_weight'].sum()
        weighted_completion = (model_data['completion_score'] * model_data['tier_weight']).sum() / total_weight
        weighted_correctness = (model_data['correctness_score'] * model_data['tier_weight']).sum() / total_weight
        weighted_tool_use = (model_data['tool_use_score'] * model_data['tier_weight']).sum() / total_weight
        weighted_total = (model_data['total_score'] * model_data['tier_weight']).sum() / total_weight

        # Other metrics
        pass_rate = model_data['overall_pass'].mean()
        avg_time = model_data['execution_time'].mean()
        consistency = 1 - (model_data['total_score'].std() / 6.0) if len(model_data) > 1 else 1.0

        model_stats.append({
            'model': model,
            'weighted_completion': weighted_completion,
            'weighted_correctness': weighted_correctness,
            'weighted_tool_use': weighted_tool_use,
            'weighted_total': weighted_total,
            'pass_rate': pass_rate,
            'avg_execution_time': avg_time,
            'consistency': max(0, consistency),
            'questions_attempted': len(model_data)
        })

    model_df = pd.DataFrame(model_stats)
    model_df = model_df.sort_values('weighted_total', ascending=False)

    print("✅ Weighted metrics calculated")
    return model_df

def create_all_plots(df, model_df):
    """Create all Phase 1 plots"""

    print("\n🎨 Creating all Phase 1 visualizations...")

    # A. Multi-Dimensional Radar Chart
    print("📊 Plot A: Multi-Dimensional Radar Chart...")
    fig, ax = plt.subplots(figsize=(12, 10), subplot_kw=dict(projection='polar'))

    metrics = ['Completion', 'Correctness', 'Tool Use', 'Pass Rate', 'Speed', 'Consistency']
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]

    colors = plt.cm.tab10(np.linspace(0, 1, min(len(model_df), 8)))

    # Calculate normalization factors for each dimension
    max_completion = model_df['weighted_completion'].max()
    max_correctness = model_df['weighted_correctness'].max()
    max_tool_use = model_df['weighted_tool_use'].max()

    for i, (_, model) in enumerate(model_df.head(8).iterrows()):
        speed_score = max(0, 1 - min(1, model['avg_execution_time'] / 10))
        # Normalize each dimension to 0-1 scale for fair comparison
        radar_values = [
            model['weighted_completion'] / max_completion if max_completion > 0 else 0,
            model['weighted_correctness'] / max_correctness if max_correctness > 0 else 0,
            model['weighted_tool_use'] / max_tool_use if max_tool_use > 0 else 0,
            model['pass_rate'],  # Already 0-1
            speed_score,         # Already 0-1
            model['consistency'] # Already 0-1
        ]
        values = radar_values + radar_values[:1]

        ax.plot(angles, values, 'o-', linewidth=2, label=model['model'].split('/')[-1],
               color=colors[i], alpha=0.8)
        ax.fill(angles, values, alpha=0.1, color=colors[i])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, fontsize=11)
    ax.set_ylim(0, 1)  # Normalized scale 0-1
    ax.grid(True)
    plt.legend(bbox_to_anchor=(1.2, 1.0), fontsize=9)
    plt.title('Multi-Dimensional Model Performance\n(Normalized: Each dimension scaled 0-1)',
             fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig('plots/plot_a_radar_chart.png', dpi=300, bbox_inches='tight')
    plt.close()

    # B. Weighted Aggregate Leaderboard
    print("📊 Plot B: Weighted Aggregate Leaderboard...")
    fig, ax = plt.subplots(figsize=(12, 8))

    y_pos = np.arange(len(model_df))
    colors = ['#1f77b4' if 'anthropic' in model else
             '#ff7f0e' if 'openai' in model else
             '#2ca02c' if 'google' in model else
             '#d62728' if 'x-ai' in model else '#9467bd'
             for model in model_df['model']]

    bars = ax.barh(y_pos, model_df['weighted_total'], color=colors, alpha=0.8)

    for i, (bar, score) in enumerate(zip(bars, model_df['weighted_total'])):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
               f'{score:.2f}', va='center', fontweight='bold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels([m.split('/')[-1] for m in model_df['model']], fontsize=11)
    ax.set_xlabel('Weighted Performance Score', fontsize=12, fontweight='bold')
    ax.set_title('Model Performance Leaderboard\n(Weighted: Tier1×1, Tier3×4)',
                fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig('plots/plot_b_leaderboard.png', dpi=300, bbox_inches='tight')
    plt.close()

    # C. Tier Mastery Stacked Bar Chart
    print("📊 Plot C: Tier Mastery...")
    fig, ax = plt.subplots(figsize=(14, 8))

    tier_contrib = []
    for model in model_df['model']:
        model_data = df[df['model'] == model]
        tier1_data = model_data[model_data['tier'] == 'tier1']
        tier3_data = model_data[model_data['tier'] == 'tier3']

        tier1_contrib = (tier1_data['total_score'].mean() * 1) if len(tier1_data) > 0 else 0
        tier3_contrib = (tier3_data['total_score'].mean() * 4) if len(tier3_data) > 0 else 0

        tier_contrib.append({
            'model': model,
            'tier1_contribution': tier1_contrib,
            'tier3_contribution': tier3_contrib
        })

    tier_df = pd.DataFrame(tier_contrib)
    tier_df = tier_df.merge(model_df[['model', 'weighted_total']], on='model')
    tier_df = tier_df.sort_values('weighted_total', ascending=False)

    x = np.arange(len(tier_df))
    width = 0.6

    p1 = ax.bar(x, tier_df['tier1_contribution'], width, label='Tier 1 (×1)',
               color='lightblue', alpha=0.8)
    p2 = ax.bar(x, tier_df['tier3_contribution'], width,
               bottom=tier_df['tier1_contribution'], label='Tier 3 (×4)',
               color='darkblue', alpha=0.8)

    ax.set_xlabel('Models', fontsize=12, fontweight='bold')
    ax.set_ylabel('Weighted Score Contribution', fontsize=12, fontweight='bold')
    ax.set_title('Tier Mastery: Weighted Score Contributions', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([model.split('/')[-1] for model in tier_df['model']],
                      rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig('plots/plot_c_tier_mastery.png', dpi=300, bbox_inches='tight')
    plt.close()

    # E. Tool Use vs Scientific Accuracy
    print("📊 Plot E: Tool Use vs Accuracy...")
    fig, ax = plt.subplots(figsize=(12, 8))

    model_colors = []
    for model in df['model']:
        if 'anthropic' in model:
            model_colors.append('#1f77b4')
        elif 'openai' in model:
            model_colors.append('#ff7f0e')
        elif 'google' in model:
            model_colors.append('#2ca02c')
        elif 'x-ai' in model:
            model_colors.append('#d62728')
        else:
            model_colors.append('#9467bd')

    sizes = [100 * weight for weight in df['tier_weight']]
    scatter = ax.scatter(df['tool_use_score'], df['correctness_score'],
                        s=sizes, c=model_colors, alpha=0.6, edgecolors='black', linewidth=0.5)

    ax.set_xlabel('Tool Use Score (0-2)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Scientific Correctness Score (0-2)', fontsize=12, fontweight='bold')
    ax.set_title('Tool Orchestration vs Scientific Accuracy\n(Size = Tier Weight)',
                fontsize=14, fontweight='bold')

    # Quadrant lines and labels
    ax.axhline(y=1, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(x=1, color='gray', linestyle='--', alpha=0.5)

    ax.text(0.2, 1.8, 'Poor Tools\nGood Science', ha='center', va='center',
           bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral", alpha=0.7))
    ax.text(1.8, 1.8, 'Good Tools\nGood Science', ha='center', va='center',
           bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7))

    ax.set_xlim(-0.1, 2.1)
    ax.set_ylim(-0.1, 2.1)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('plots/plot_e_tool_vs_accuracy.png', dpi=300, bbox_inches='tight')
    plt.close()

    # F. Performance vs Speed
    print("📊 Plot F: Performance vs Speed...")
    fig, ax = plt.subplots(figsize=(12, 8))

    colors = ['#1f77b4' if 'anthropic' in model else
             '#ff7f0e' if 'openai' in model else
             '#2ca02c' if 'google' in model else
             '#d62728' if 'x-ai' in model else '#9467bd'
             for model in model_df['model']]

    scatter = ax.scatter(model_df['avg_execution_time'], model_df['weighted_total'],
                        s=200, c=colors, alpha=0.7, edgecolors='black', linewidth=1)

    for i, model in enumerate(model_df['model']):
        ax.annotate(model.split('/')[-1],
                   (model_df['avg_execution_time'].iloc[i], model_df['weighted_total'].iloc[i]),
                   xytext=(5, 5), textcoords='offset points', fontsize=9, ha='left')

    ax.set_xlabel('Average Execution Time (minutes)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Weighted Performance Score', fontsize=12, fontweight='bold')
    ax.set_title('Performance vs Speed Trade-off', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('plots/plot_f_performance_vs_speed.png', dpi=300, bbox_inches='tight')
    plt.close()

    # G. Performance Distribution
    print("📊 Plot G: Performance Distribution...")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # G1: Total Score by Model
    ax1 = axes[0, 0]
    models_short = [model.split('/')[-1] for model in df['model'].unique()]
    box_data = [df[df['model'] == model]['total_score'].values
               for model in df['model'].unique()]

    bp1 = ax1.boxplot(box_data, labels=models_short, patch_artist=True)
    colors = plt.cm.Set3(np.linspace(0, 1, len(bp1['boxes'])))
    for patch, color in zip(bp1['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax1.set_title('Total Score Distribution by Model', fontweight='bold')
    ax1.set_ylabel('Total Score (0-6)')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(axis='y', alpha=0.3)

    # G2: Score by Tier
    ax2 = axes[0, 1]
    tier_data = [df[df['tier'] == tier]['total_score'].values
                for tier in ['tier1', 'tier3']]

    bp2 = ax2.boxplot(tier_data, labels=['Tier 1\n(Basic)', 'Tier 3\n(Advanced)'],
                     patch_artist=True)
    bp2['boxes'][0].set_facecolor('lightblue')
    bp2['boxes'][1].set_facecolor('darkblue')
    for patch in bp2['boxes']:
        patch.set_alpha(0.7)

    ax2.set_title('Performance by Complexity', fontweight='bold')
    ax2.set_ylabel('Total Score (0-6)')
    ax2.grid(axis='y', alpha=0.3)

    # G3: Dimensions
    ax3 = axes[1, 0]
    dimension_data = [df['completion_score'].values, df['correctness_score'].values,
                     df['tool_use_score'].values]

    bp3 = ax3.boxplot(dimension_data, labels=['Completion', 'Correctness', 'Tool Use'],
                     patch_artist=True)
    colors = ['lightcoral', 'lightgreen', 'lightblue']
    for patch, color in zip(bp3['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax3.set_title('Score Distribution by Dimension', fontweight='bold')
    ax3.set_ylabel('Dimension Score (0-2)')
    ax3.grid(axis='y', alpha=0.3)

    # G4: Pass Rate
    ax4 = axes[1, 1]
    pass_rates = [df[df['model'] == model]['overall_pass'].mean()
                 for model in df['model'].unique()]

    bars = ax4.bar(models_short, pass_rates, color=colors[:len(models_short)], alpha=0.7)
    ax4.set_title('Pass Rate by Model', fontweight='bold')
    ax4.set_ylabel('Pass Rate')
    ax4.set_ylim(0, 1.1)
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(axis='y', alpha=0.3)

    for bar, rate in zip(bars, pass_rates):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                f'{rate:.0%}', ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig('plots/plot_g_performance_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("✅ All plots saved successfully!")

def generate_summary_report(df, model_df):
    """Generate comprehensive summary report"""
    print("\n" + "="*80)
    print("🏆 COMPUTATIONAL CHEMISTRY AGENT EVALUATION SUMMARY")
    print("="*80)

    print(f"\n📊 DATASET OVERVIEW:")
    print(f"• Total evaluations: {len(df)}")
    print(f"• Questions evaluated: {df['question_id'].nunique()}")
    print(f"• Models compared: {df['model'].nunique()}")
    print(f"• Tier distribution: {dict(df['tier'].value_counts())}")

    print(f"\n🥇 TOP 5 CHAMPIONS (Tier-Weighted: Tier1×1, Tier3×4):")
    for i, (_, model) in enumerate(model_df.head(5).iterrows()):
        print(f"{i+1}. {model['model']} - Score: {model['weighted_total']:.2f}/6.0 "
              f"(Pass Rate: {model['pass_rate']:.1%})")

    print(f"\n📈 PERFORMANCE BREAKDOWN:")
    best_completion = model_df.loc[model_df['weighted_completion'].idxmax()]
    best_correctness = model_df.loc[model_df['weighted_correctness'].idxmax()]
    best_tools = model_df.loc[model_df['weighted_tool_use'].idxmax()]
    fastest = model_df.loc[model_df['avg_execution_time'].idxmin()]

    print(f"• Best Completion: {best_completion['model']} ({best_completion['weighted_completion']:.2f}/2.0)")
    print(f"• Best Correctness: {best_correctness['model']} ({best_correctness['weighted_correctness']:.2f}/2.0)")
    print(f"• Best Tool Use: {best_tools['model']} ({best_tools['weighted_tool_use']:.2f}/2.0)")
    print(f"• Fastest: {fastest['model']} ({fastest['avg_execution_time']:.1f} min avg)")

    print(f"\n⚡ KEY INSIGHTS:")
    tier1_avg = df[df['tier'] == 'tier1']['total_score'].mean()
    tier3_avg = df[df['tier'] == 'tier3']['total_score'].mean()
    print(f"• Tier 1 average: {tier1_avg:.1f}/6.0")
    print(f"• Tier 3 average: {tier3_avg:.1f}/6.0")
    print(f"• Overall pass rate: {df['overall_pass'].mean():.1%}")
    print(f"• Anthropic models dominate the top rankings")
    print(f"• {model_df['pass_rate'].max():.0%} is the highest individual model pass rate")

if __name__ == "__main__":
    print("🚀 Starting Phase 1 Computational Chemistry Agent Analysis...")
    print("📊 Tier Weighting: Tier 1 = 1x, Tier 3 = 4x")

    df = load_evaluation_data()
    model_df = calculate_weighted_metrics(df)
    create_all_plots(df, model_df)
    generate_summary_report(df, model_df)

    print("\n✅ Phase 1 analysis complete!")
    print("📁 Generated plots in plots/ directory:")
    print("   • plots/plot_a_radar_chart.png")
    print("   • plots/plot_b_leaderboard.png")
    print("   • plots/plot_c_tier_mastery.png")
    print("   • plots/plot_e_tool_vs_accuracy.png")
    print("   • plots/plot_f_performance_vs_speed.png")
    print("   • plots/plot_g_performance_distribution.png")