#!/usr/bin/env python3
"""
Create comprehensive judge comparison visualizations.
Compares Sonnet-4, Qwen, GPT-5, and Gemini judges across all evaluated models.
"""

import json
import os
import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from collections import defaultdict
from pathlib import Path
from scipy.stats import pearsonr
from matplotlib.patches import Rectangle

# Modern color palette
JUDGE_COLORS = {
    'Claude Sonnet-4': '#8B5CF6',
    'Qwen': '#F59E0B',
    'GPT-5': '#10B981',
    'Gemini': '#EC4899'
}

MODEL_COLORS = {
    'claude-opus-4.1': '#8B5CF6',
    'claude-sonnet-4.5': '#A78BFA',
    'claude-sonnet-4': '#C4B5FD',
    'gpt-5': '#10B981',
    'o3': '#34D399',
    'gemini-2.5-pro': '#F59E0B',
    'deepseek-chat-v3.1': '#6B7280',
    'grok-4-fast': '#6B7280',
    'grok-code-fast-1': '#EC4899',
}

def setup_style():
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Inter', 'SF Pro Display', 'Helvetica Neue', 'Arial'],
        'font.size': 11,
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
    })

def calculate_weighted_score(evaluations_list):
    """Calculate weighted score with tier1=1x, tier2=2x, tier3=4x."""
    tier_weights = {'tier1': 1.0, 'tier2': 2.0, 'tier3': 4.0}
    weighted_total = 0
    weight_sum = 0
    for eval_data in evaluations_list:
        tier = eval_data.get('tier', 'tier1')
        weight = tier_weights.get(tier, 1.0)
        score_normalized = eval_data['total_score'] / 6.0 * 100
        weighted_total += score_normalized * weight
        weight_sum += weight
    return weighted_total / weight_sum if weight_sum > 0 else 0

def load_judge_data(judge_name, eval_dir):
    """Load evaluation data for a specific judge."""
    evaluations = defaultdict(dict)
    eval_pattern = f"{eval_dir}/*/json/*_evaluation.json"
    eval_files = glob.glob(eval_pattern)
    
    for eval_file in eval_files:
        try:
            with open(eval_file, 'r') as f:
                data = json.load(f)
            question_id = data.get('question_id')
            filename = Path(eval_file).stem
            model_name = filename.replace('_evaluation', '').replace('_', '/', 1)
            
            if 'deepseek' in model_name:
                model_name = model_name.replace('_', ':', 1)
            if 'grok' in model_name and 'free' in model_name:
                model_name = model_name.replace('_free', ':free')
            
            tier = question_id.split('_')[0] if '_' in question_id else 'tier1'
            
            evaluations[question_id][model_name] = {
                'completion_score': data.get('completion_score', 0),
                'correctness_score': data.get('correctness_score', 0),
                'tool_use_score': data.get('tool_use_score', 0),
                'total_score': data.get('total_score', 0),
                'overall_assessment': data.get('overall_assessment', 'fail'),
                'passed': data.get('overall_assessment', 'fail') == 'pass',
                'tier': tier
            }
        except Exception as e:
            print(f"Error loading {eval_file}: {e}")
    
    return evaluations

def aggregate_model_scores(evaluations):
    """Aggregate weighted scores by model."""
    model_data = {}
    for model_name in set(m for models in evaluations.values() for m in models.keys()):
        model_evals = []
        for _, models in evaluations.items():
            if model_name in models:
                model_evals.append(models[model_name])
        if model_evals:
            weighted_score = calculate_weighted_score(model_evals)
            # Clean model name - remove company prefix and :free suffix
            clean_name = model_name.split('/')[-1] if '/' in model_name else model_name
            clean_name = clean_name.replace(':free', '')  # Remove :free suffix
            model_data[clean_name] = weighted_score
    return model_data

def load_all_judges():
    """Load data from all four judges."""
    base_dir = "/Users/katherineyenko/Desktop/sandbox/labagents"
    judges = {
        'Claude Sonnet-4': f"{base_dir}/evaluations_sonnet4",
        'Qwen': f"{base_dir}/evaluations_qwen",
        'GPT-5': f"{base_dir}/evaluations_gpt5",
        'Gemini': f"{base_dir}/evaluations_gemini",
    }
    
    all_data = {}
    for judge_name, eval_dir in judges.items():
        if os.path.exists(eval_dir):
            print(f"Loading {judge_name} evaluations from {eval_dir}")
            evals = load_judge_data(judge_name, eval_dir)
            scores = aggregate_model_scores(evals)
            all_data[judge_name] = scores
        else:
            print(f"⚠️  Directory not found: {eval_dir}")
    
    return all_data

def create_heatmap(data, output_dir):
    """Create judge agreement heatmap showing scores for each model-judge pair."""
    setup_style()
    
    # Convert to DataFrame
    df = pd.DataFrame(data).T  # Transpose so models are columns, judges are rows
    df = df.fillna(0)
    
    # Sort models by average score
    df = df[df.mean().sort_values(ascending=False).index]
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Create heatmap
    sns.heatmap(df, annot=True, fmt='.1f', cmap='RdYlGn', center=50, 
                vmin=0, vmax=100, cbar_kws={'label': 'Weighted Score (%)'},
                linewidths=0.5, linecolor='white', ax=ax)
    
    ax.set_title('Judge Agreement Heatmap: Model Scores Across Judges', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Model', fontsize=12, fontweight='600')
    ax.set_ylabel('Judge', fontsize=12, fontweight='600')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/judge_heatmap.png", dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created judge_heatmap.png")

def create_correlation_matrix(data, output_dir):
    """Create correlation matrix between judges."""
    setup_style()
    
    df = pd.DataFrame(data)
    df = df.fillna(0)
    
    # Calculate correlation
    corr = df.corr()
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Create heatmap
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(corr, annot=True, fmt='.3f', cmap='coolwarm', center=0, 
                vmin=-1, vmax=1, square=True, mask=mask,
                cbar_kws={'label': 'Pearson Correlation'},
                linewidths=1, linecolor='white', ax=ax)
    
    ax.set_title('Judge Correlation Matrix\nHow Similarly Do Judges Score Models?', 
                 fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/judge_correlation.png", dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created judge_correlation.png")

def create_bias_plot(data, output_dir):
    """Create score delta plot showing judge bias."""
    setup_style()
    
    df = pd.DataFrame(data)
    df = df.fillna(0)
    
    # Calculate mean across judges and delta from mean
    df['mean'] = df.mean(axis=1)
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    x = np.arange(len(df))
    width = 0.2
    
    for i, judge in enumerate([col for col in df.columns if col != 'mean']):
        delta = df[judge] - df['mean']
        offset = width * (i - 1.5)
        ax.bar(x + offset, delta, width, label=judge, 
               color=JUDGE_COLORS.get(judge, '#6B7280'), alpha=0.8)
    
    ax.axhline(0, color='black', linewidth=1, linestyle='--', alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(df.index, rotation=45, ha='right')
    ax.set_ylabel('Score Delta from Mean (%)', fontsize=12, fontweight='600')
    ax.set_title('Judge Bias Analysis: Score Deviation from Consensus\nPositive = More Lenient, Negative = More Harsh', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='upper right', framealpha=0.95)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/judge_bias_delta.png", dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created judge_bias_delta.png")

def create_rank_consistency(data, output_dir):
    """Create model rank consistency chart."""
    setup_style()
    
    df = pd.DataFrame(data)
    df = df.fillna(0)
    
    # Get ranks for each judge (1 = best)
    ranks = df.rank(ascending=False, method='min')
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    models = ranks.index
    y_pos = np.arange(len(models))
    
    for i, model in enumerate(models):
        model_ranks = ranks.loc[model].values
        min_rank = model_ranks.min()
        max_rank = model_ranks.max()
        mean_rank = model_ranks.mean()
        
        # Draw range bar
        ax.barh(i, max_rank - min_rank, left=min_rank, height=0.4, 
                color=MODEL_COLORS.get(model, '#6B7280'), alpha=0.3)
        
        # Draw mean marker
        ax.scatter(mean_rank, i, color=MODEL_COLORS.get(model, '#6B7280'), 
                  s=100, zorder=10, edgecolors='white', linewidths=2)
        
        # Draw individual judge ranks
        for rank in model_ranks:
            ax.scatter(rank, i, color='white', s=30, zorder=9, 
                      edgecolors=MODEL_COLORS.get(model, '#6B7280'), linewidths=1.5)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(models)
    ax.set_xlabel('Rank (1 = Best)', fontsize=12, fontweight='600')
    ax.set_title('Model Rank Consistency Across Judges\nDots = Individual Judge Ranks, Circle = Mean Rank, Bar = Range', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.invert_xaxis()
    ax.grid(axis='x', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/rank_consistency.png", dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created rank_consistency.png")

def create_disagreement_chart(data, output_dir):
    """Create chart showing judge disagreement by model."""
    setup_style()
    
    df = pd.DataFrame(data)
    df = df.fillna(0)
    
    # Calculate standard deviation (disagreement) for each model
    disagreement = df.std(axis=1).sort_values(ascending=True)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    y_pos = np.arange(len(disagreement))
    colors = [MODEL_COLORS.get(model, '#6B7280') for model in disagreement.index]
    
    bars = ax.barh(y_pos, disagreement.values, color=colors, alpha=0.8)
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, disagreement.values)):
        ax.text(val + 0.2, i, f'{val:.1f}', va='center', fontweight='bold', fontsize=10)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(disagreement.index)
    ax.set_xlabel('Standard Deviation of Scores (%)', fontsize=12, fontweight='600')
    ax.set_title('Judge Disagreement by Model\nHigher = More Controversial Evaluations', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/judge_disagreement.png", dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created judge_disagreement.png")

def create_scatter_matrix(data, output_dir):
    """Create pairwise scatter matrix for judge comparisons."""
    setup_style()
    
    df = pd.DataFrame(data)
    df = df.fillna(0)
    
    judges = df.columns.tolist()
    n = len(judges)
    
    fig, axes = plt.subplots(n, n, figsize=(16, 16))
    fig.suptitle('Judge Pairwise Score Comparison Matrix\nEach Model is a Point', 
                 fontsize=18, fontweight='bold', y=0.995)
    
    for i, judge_y in enumerate(judges):
        for j, judge_x in enumerate(judges):
            ax = axes[i, j]
            
            if i == j:
                # Diagonal: histogram
                ax.hist(df[judge_x], bins=10, color=JUDGE_COLORS.get(judge_x, '#6B7280'), 
                       alpha=0.7, edgecolor='white')
                ax.set_ylabel('')
                ax.set_yticks([])
            else:
                # Off-diagonal: scatter
                ax.scatter(df[judge_x], df[judge_y], 
                          c=[MODEL_COLORS.get(m, '#6B7280') for m in df.index],
                          s=80, alpha=0.7, edgecolors='white', linewidths=1)
                
                # Add diagonal line
                lims = [0, 100]
                ax.plot(lims, lims, 'k--', alpha=0.3, linewidth=1)
                
                # Calculate and show correlation
                if len(df) > 1:
                    corr, _ = pearsonr(df[judge_x], df[judge_y])
                    ax.text(0.05, 0.95, f'r={corr:.2f}', transform=ax.transAxes, 
                           fontsize=9, va='top', bbox=dict(boxstyle='round', 
                           facecolor='white', alpha=0.8))
            
            # Labels
            if i == n - 1:
                ax.set_xlabel(judge_x, fontsize=10)
            if j == 0:
                ax.set_ylabel(judge_y, fontsize=10)
            
            ax.set_xlim(0, 100)
            ax.set_ylim(0, 100)
            ax.grid(alpha=0.2)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/scatter_matrix.png", dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created scatter_matrix.png")

def create_severity_index(data, output_dir):
    """Create judge severity index chart."""
    setup_style()
    
    df = pd.DataFrame(data)
    df = df.fillna(0)
    
    # Calculate mean and std for each judge
    judge_means = df.mean()
    global_mean = df.values.flatten().mean()
    global_std = df.values.flatten().std()
    
    # Severity index: (judge_mean - global_mean) / global_std
    severity = (judge_means - global_mean) / global_std
    severity = severity.sort_values()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = [JUDGE_COLORS.get(judge, '#6B7280') for judge in severity.index]
    bars = ax.barh(severity.index, severity.values, color=colors, alpha=0.8)
    
    # Add labels
    for i, (bar, val) in enumerate(zip(bars, severity.values)):
        ax.text(val + 0.05 if val > 0 else val - 0.05, i, f'{val:.2f}', 
               va='center', ha='left' if val > 0 else 'right', fontweight='bold')
    
    ax.axvline(0, color='black', linewidth=1.5, linestyle='-')
    ax.set_xlabel('Severity Index (σ)', fontsize=12, fontweight='600')
    ax.set_title('Judge Severity Index\nNegative = Harsh, Positive = Lenient', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/severity_index.png", dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created severity_index.png")

def create_summary_table(data, output_dir):
    """Create summary statistics table."""
    df = pd.DataFrame(data)
    df = df.fillna(0)
    
    summary = {
        'Judge': [],
        'Mean Score': [],
        'Std Dev': [],
        'Min Score': [],
        'Max Score': [],
        'Range': []
    }
    
    for judge in df.columns:
        summary['Judge'].append(judge)
        summary['Mean Score'].append(f"{df[judge].mean():.1f}")
        summary['Std Dev'].append(f"{df[judge].std():.1f}")
        summary['Min Score'].append(f"{df[judge].min():.1f}")
        summary['Max Score'].append(f"{df[judge].max():.1f}")
        summary['Range'].append(f"{df[judge].max() - df[judge].min():.1f}")
    
    summary_df = pd.DataFrame(summary)
    
    # Save to file
    with open(f"{output_dir}/judge_summary.txt", 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("JUDGE COMPARISON SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        f.write(summary_df.to_string(index=False))
        f.write("\n\n")
        
        # Add correlation summary
        corr = df.corr()
        f.write("JUDGE CORRELATIONS:\n")
        f.write("-" * 80 + "\n")
        f.write(corr.to_string())
        f.write("\n")
    
    print("✅ Created judge_summary.txt")

def main():
    print("\n🎨 Creating judge comparison analysis...\n")
    
    # Load all judge data
    all_data = load_all_judges()
    
    if len(all_data) < 2:
        print("❌ Need at least 2 judges to compare")
        return
    
    print(f"\n✅ Loaded {len(all_data)} judges\n")
    
    # Create output directory
    output_dir = "/Users/katherineyenko/Desktop/sandbox/labagents/plots/judge_comparison"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate all visualizations
    print("📊 Generating visualizations...\n")
    create_heatmap(all_data, output_dir)
    create_correlation_matrix(all_data, output_dir)
    create_bias_plot(all_data, output_dir)
    create_rank_consistency(all_data, output_dir)
    create_disagreement_chart(all_data, output_dir)
    create_scatter_matrix(all_data, output_dir)
    create_severity_index(all_data, output_dir)
    create_summary_table(all_data, output_dir)
    
    print(f"\n✅ All judge comparison plots created in {output_dir}!\n")

if __name__ == "__main__":
    main()

