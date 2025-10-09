#!/usr/bin/env python3
"""
create_analysis_visualizations.py - create comprehensive analysis visualizations
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Modern professional color palette
MODEL_COLORS = {
    'anthropic/claude-opus-4.1': '#8B5CF6',
    'anthropic/claude-sonnet-4.5': '#A78BFA',
    'anthropic/claude-sonnet-4': '#C4B5FD',
    'openai/gpt-5': '#10B981',
    'openai/o3': '#34D399',
    'google/gemini-2.5-pro': '#F59E0B',
    'deepseek/deepseek-chat-v3.1': '#3B82F6',
    'x-ai/grok-4-fast': '#EC4899',
    'x-ai/grok-code-fast-1': '#F472B6',
}

def setup_modern_style():
    """Setup modern, clean chart styling"""
    sns.set_style("whitegrid")
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
        'font.size': 11,
        'axes.titlesize': 16,
        'axes.titleweight': 'bold',
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'axes.edgecolor': '#E5E7EB',
        'axes.linewidth': 1.5,
        'grid.color': '#E5E7EB',
        'grid.alpha': 0.5,
        'grid.linewidth': 0.8,
    })

def create_cost_efficiency_plot(df):
    """Cost per question visualization"""
    setup_modern_style()

    model_costs = df.groupby('model')['cost_usd'].mean().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(14, 8))
    colors = [MODEL_COLORS.get(m, '#6B7280') for m in model_costs.index]

    bars = ax.barh(model_costs.index, model_costs.values, color=colors, alpha=0.85, edgecolor='white', linewidth=2)

    # Add cost labels
    for bar, cost in zip(bars, model_costs.values):
        label = "FREE" if cost == 0 else f"${cost:.3f}"
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
                label, va='center', ha='left', fontweight='bold', fontsize=11)

    ax.set_xlabel('Average Cost per Question (USD)', fontsize=13, fontweight='600')
    ax.set_title('Model Cost Efficiency\nAverage Cost per Question',
                 fontsize=18, fontweight='bold', pad=20)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig('plots/cost_efficiency.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created plots/cost_efficiency.png")

def create_speed_comparison_plot(df):
    """Execution time comparison"""
    setup_modern_style()

    model_times = df.groupby('model')['time_s'].mean().sort_values()

    fig, ax = plt.subplots(figsize=(14, 8))
    colors = [MODEL_COLORS.get(m, '#6B7280') for m in model_times.index]

    bars = ax.barh(model_times.index, model_times.values, color=colors, alpha=0.85, edgecolor='white', linewidth=2)

    # Add time labels
    for bar, time_s in zip(bars, model_times.values):
        minutes = int(time_s // 60)
        seconds = int(time_s % 60)
        label = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
        ax.text(bar.get_width() + 10, bar.get_y() + bar.get_height()/2,
                label, va='center', ha='left', fontweight='bold', fontsize=11)

    ax.set_xlabel('Average Execution Time (seconds)', fontsize=13, fontweight='600')
    ax.set_title('Model Speed Comparison\nAverage Time per Question',
                 fontsize=18, fontweight='bold', pad=20)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig('plots/speed_comparison.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created plots/speed_comparison.png")

def create_token_usage_plot(df):
    """Token usage comparison with breakdown"""
    setup_modern_style()

    # Group by model and calculate averages
    token_data = df.groupby('model').agg({
        'prompt_tokens': 'mean',
        'completion_tokens': 'mean',
        'reasoning_tokens': 'mean'
    }).sort_values('prompt_tokens', ascending=True)

    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(14, 8))

    models = token_data.index
    y_pos = np.arange(len(models))

    # Stack: prompt, completion, reasoning
    prompt_tokens = token_data['prompt_tokens'].values
    completion_tokens = token_data['completion_tokens'].values
    reasoning_tokens = token_data['reasoning_tokens'].values

    # Plot stacked bars
    bars1 = ax.barh(y_pos, prompt_tokens, color='#93C5FD', alpha=0.85, label='Input (Prompt)', edgecolor='white', linewidth=1)
    bars2 = ax.barh(y_pos, completion_tokens, left=prompt_tokens, color='#34D399', alpha=0.85, label='Output (Completion)', edgecolor='white', linewidth=1)
    bars3 = ax.barh(y_pos, reasoning_tokens, left=prompt_tokens + completion_tokens, color='#FBBF24', alpha=0.85, label='Reasoning', edgecolor='white', linewidth=1)

    # Add total labels
    for i, model in enumerate(models):
        total = prompt_tokens[i] + completion_tokens[i] + reasoning_tokens[i]
        ax.text(total + 5000, i, f"{total/1000:.0f}K", va='center', ha='left', fontweight='bold', fontsize=10)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(models)
    ax.set_xlabel('Average Tokens per Question', fontsize=13, fontweight='600')
    ax.set_title('Model Token Usage Breakdown\nInput vs Output vs Reasoning Tokens',
                 fontsize=18, fontweight='bold', pad=20)
    ax.legend(loc='lower right', fontsize=11, framealpha=0.95)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig('plots/token_usage.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created plots/token_usage.png")

def create_tool_usage_plot(df):
    """Tool usage comparison"""
    setup_modern_style()

    model_tools = df.groupby('model')['tool_calls'].mean().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(14, 8))
    colors = [MODEL_COLORS.get(m, '#6B7280') for m in model_tools.index]

    bars = ax.barh(model_tools.index, model_tools.values, color=colors, alpha=0.85, edgecolor='white', linewidth=2)

    # Add tool count labels
    for bar, tools in zip(bars, model_tools.values):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                f"{tools:.1f}", va='center', ha='left', fontweight='bold', fontsize=11)

    ax.set_xlabel('Average Tool Calls per Question', fontsize=13, fontweight='600')
    ax.set_title('Tool Usage Patterns\nAverage Tool Calls per Question',
                 fontsize=18, fontweight='bold', pad=20)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig('plots/tool_usage.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created plots/tool_usage.png")

def create_o3_paradox_plot(df, eval_df):
    """Visualize the o3 paradox: fast, cheap, low tools BUT low scores"""
    setup_modern_style()

    # Get o3 stats
    o3_data = df[df['model'] == 'openai/o3']
    o3_eval = eval_df[eval_df['model'] == 'openai/o3']

    # Get average stats for comparison
    avg_time = df['time_s'].mean()
    avg_tokens = df['total_tokens'].mean()
    avg_tools = df['tool_calls'].mean()
    avg_cost = df['cost_usd'].mean()

    o3_time = o3_data['time_s'].mean()
    o3_tokens = o3_data['total_tokens'].mean()
    o3_tools = o3_data['tool_calls'].mean()
    o3_cost = o3_data['cost_usd'].mean()

    # Normalize to percentages (o3 as % of average)
    metrics = ['Speed\n(lower=better)', 'Tokens\n(lower=better)', 'Tool Calls', 'Cost\n(lower=better)']
    o3_pcts = [
        (o3_time / avg_time) * 100,
        (o3_tokens / avg_tokens) * 100,
        (o3_tools / avg_tools) * 100,
        (o3_cost / avg_cost) * 100
    ]

    fig, ax = plt.subplots(figsize=(12, 8))

    x = np.arange(len(metrics))
    bars = ax.bar(x, o3_pcts, color='#34D399', alpha=0.85, edgecolor='white', linewidth=2)

    # Add 100% reference line
    ax.axhline(y=100, color='#6B7280', linestyle='--', linewidth=2, alpha=0.5, label='Average (100%)')

    # Add percentage labels
    for bar, pct in zip(bars, o3_pcts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                f"{pct:.0f}%", ha='center', va='bottom', fontweight='bold', fontsize=12)

    ax.set_ylabel('o3 as % of Average', fontsize=13, fontweight='600')
    ax.set_title('The o3 Paradox\no3 is Fast & Cheap But Scores Low',
                 fontsize=18, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=11)
    ax.legend(fontsize=11)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig('plots/o3_paradox.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created plots/o3_paradox.png")

def create_efficiency_scatter(df):
    """Scatter: cost vs performance (from leaderboard)"""
    setup_modern_style()

    # Load leaderboard for performance scores
    leaderboard = pd.read_csv('leaderboard/leaderboard_overall.csv')

    # Merge with cost data
    avg_cost = df.groupby('model')['cost_usd'].mean()

    plot_data = []
    for _, row in leaderboard.iterrows():
        model = row['model']
        if model in avg_cost.index:
            plot_data.append({
                'model': model,
                'weighted_score': row['weighted_score'],
                'avg_cost': avg_cost[model]
            })

    plot_df = pd.DataFrame(plot_data)

    fig, ax = plt.subplots(figsize=(12, 8))

    for _, row in plot_df.iterrows():
        ax.scatter(row['avg_cost'], row['weighted_score'],
                  s=200, color=MODEL_COLORS.get(row['model'], '#6B7280'),
                  alpha=0.7, edgecolor='white', linewidth=2)

        # Add model labels
        ax.text(row['avg_cost'] + 0.1, row['weighted_score'],
               row['model'].split('/')[-1], fontsize=9, va='center')

    ax.set_xlabel('Average Cost per Question (USD)', fontsize=13, fontweight='600')
    ax.set_ylabel('Weighted Performance Score (%)', fontsize=13, fontweight='600')
    ax.set_title('Cost vs Performance\nHigher & Left = Better Value',
                 fontsize=18, fontweight='bold', pad=20)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('plots/cost_vs_performance.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created plots/cost_vs_performance.png")

if __name__ == "__main__":
    print("🎨 Creating analysis visualizations...")

    # Load data
    df = pd.read_csv('analysis/all_log_data.csv')
    print(f"📊 Loaded {len(df)} log entries")

    # Load evaluations for scores
    import glob
    import json
    from collections import defaultdict

    evals = []
    for eval_file in glob.glob("evaluations/*/json/*_evaluation.json"):
        try:
            with open(eval_file) as f:
                data = json.load(f)
            model = data.get('model', 'unknown')
            # Normalize model name
            model = model.replace(':free', '').replace('_free', '')
            evals.append({
                'model': model,
                'question': data.get('question_id'),
                'total_score': data.get('total_score', 0)
            })
        except:
            pass

    eval_df = pd.DataFrame(evals)

    # Create visualizations
    os.makedirs('plots', exist_ok=True)

    create_cost_efficiency_plot(df)
    create_speed_comparison_plot(df)
    create_token_usage_plot(df)
    create_tool_usage_plot(df)
    create_o3_paradox_plot(df, eval_df)
    create_efficiency_scatter(df)

    print("\n✅ All visualizations created!")
