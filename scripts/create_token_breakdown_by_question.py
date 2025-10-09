#!/usr/bin/env python3
"""
create_token_breakdown_by_question.py - visualize token usage per question across models
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Modern color palette
MODEL_COLORS = {
    'anthropic/claude-sonnet-4': '#C4B5FD',
    'anthropic/claude-sonnet-4.5': '#A78BFA',
    'anthropic/claude-opus-4.1': '#8B5CF6',
    'openai/gpt-5': '#10B981',
    'openai/o3': '#34D399',
    'google/gemini-2.5-pro': '#F59E0B',
    'deepseek/deepseek-chat-v3.1': '#3B82F6',
    'x-ai/grok-4-fast': '#EC4899',
    'x-ai/grok-code-fast-1': '#F472B6',
}

def setup_style():
    """Setup plot style"""
    sns.set_style("whitegrid")
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': 10,
        'axes.titlesize': 14,
        'axes.titleweight': 'bold',
        'figure.facecolor': 'white',
    })

def create_grouped_bar_chart(df):
    """Create grouped bar chart: 22 questions, 9 models per question"""
    setup_style()

    # Get unique questions and models
    questions = sorted(df['question'].unique())
    models = sorted(df['model'].unique())

    # Create pivot table
    pivot = df.pivot(index='question', columns='model', values='prompt_tokens')

    # Create plot
    fig, ax = plt.subplots(figsize=(20, 10))

    # Position bars
    x = np.arange(len(questions))
    width = 0.08  # Width of each bar

    # Plot bars for each model
    for i, model in enumerate(models):
        offset = (i - len(models)/2) * width
        values = [pivot.loc[q, model] if model in pivot.columns and q in pivot.index else 0
                  for q in questions]

        ax.bar(x + offset, values, width,
               label=model.split('/')[-1],
               color=MODEL_COLORS.get(model, '#6B7280'),
               alpha=0.85)

    ax.set_xlabel('Question', fontsize=12, fontweight='600')
    ax.set_ylabel('Input Tokens (Prompt)', fontsize=12, fontweight='600')
    ax.set_title('Input Token Usage by Question\nAll Models Compared',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(questions, rotation=45, ha='right')
    ax.legend(loc='upper left', ncol=3, fontsize=9)
    ax.grid(True, axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig('plots/token_breakdown_by_question_grouped.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print("✅ Created plots/token_breakdown_by_question_grouped.png")

def create_heatmap(df):
    """Create heatmap: questions vs models, color = token usage"""
    setup_style()

    # Create pivot table
    pivot = df.pivot(index='model', columns='question', values='prompt_tokens')

    # Sort questions properly
    questions = sorted(pivot.columns)
    pivot = pivot[questions]

    # Create heatmap
    fig, ax = plt.subplots(figsize=(18, 8))

    sns.heatmap(pivot, annot=False, fmt='.0f', cmap='YlOrRd',
                cbar_kws={'label': 'Input Tokens'},
                linewidths=0.5, linecolor='white')

    ax.set_title('Input Token Usage Heatmap\nDarker = More Tokens',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Question', fontsize=12, fontweight='600')
    ax.set_ylabel('Model', fontsize=12, fontweight='600')

    plt.tight_layout()
    plt.savefig('plots/token_breakdown_heatmap.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print("✅ Created plots/token_breakdown_heatmap.png")

def create_tier_comparison(df):
    """Compare token usage by tier (cleaner view)"""
    setup_style()

    # Add tier info
    df['tier'] = df['question'].str.split('_').str[0]

    # Group by tier and model
    tier_data = df.groupby(['tier', 'model'])['prompt_tokens'].mean().reset_index()

    # Create plot
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)

    for i, tier in enumerate(['tier1', 'tier2', 'tier3']):
        tier_subset = tier_data[tier_data['tier'] == tier].sort_values('prompt_tokens')

        models = tier_subset['model'].values
        tokens = tier_subset['prompt_tokens'].values
        colors = [MODEL_COLORS.get(m, '#6B7280') for m in models]

        axes[i].barh(range(len(models)), tokens, color=colors, alpha=0.85)
        axes[i].set_yticks(range(len(models)))
        axes[i].set_yticklabels([m.split('/')[-1] for m in models])
        axes[i].set_xlabel('Avg Input Tokens', fontsize=11)
        axes[i].set_title(f'{tier.upper()}\n({"Basic" if tier == "tier1" else "Multi-tool" if tier == "tier2" else "Complex"})',
                         fontsize=12, fontweight='bold')
        axes[i].grid(True, axis='x', alpha=0.3)

        # Add value labels
        for j, (model, token) in enumerate(zip(models, tokens)):
            axes[i].text(token + 1000, j, f'{token/1000:.0f}K',
                        va='center', fontsize=9, fontweight='bold')

    plt.suptitle('Input Token Usage by Difficulty Tier\nAverage Across All Questions in Tier',
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('plots/token_breakdown_by_tier.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print("✅ Created plots/token_breakdown_by_tier.png")

def create_faceted_by_tier(df):
    """Create faceted plot showing questions within each tier"""
    setup_style()

    # Add tier info
    df['tier'] = df['question'].str.split('_').str[0]

    # Create subplots
    fig, axes = plt.subplots(3, 1, figsize=(16, 12))

    for i, tier in enumerate(['tier1', 'tier2', 'tier3']):
        tier_data = df[df['tier'] == tier]
        questions = sorted(tier_data['question'].unique())
        models = sorted(tier_data['model'].unique())

        pivot = tier_data.pivot(index='question', columns='model', values='prompt_tokens')

        x = np.arange(len(questions))
        width = 0.08

        for j, model in enumerate(models):
            offset = (j - len(models)/2) * width
            values = [pivot.loc[q, model] if model in pivot.columns and q in pivot.index else 0
                      for q in questions]

            axes[i].bar(x + offset, values, width,
                       label=model.split('/')[-1] if i == 0 else "",
                       color=MODEL_COLORS.get(model, '#6B7280'),
                       alpha=0.85)

        axes[i].set_ylabel('Input Tokens', fontsize=11)
        axes[i].set_title(f'{tier.upper()} Questions', fontsize=12, fontweight='bold')
        axes[i].set_xticks(x)
        axes[i].set_xticklabels(questions, rotation=45, ha='right')
        axes[i].grid(True, axis='y', alpha=0.3)

        if i == 0:
            axes[i].legend(loc='upper left', ncol=3, fontsize=9)

    axes[2].set_xlabel('Question', fontsize=11, fontweight='600')

    plt.suptitle('Input Token Usage by Question\nGrouped by Difficulty Tier',
                 fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig('plots/token_breakdown_faceted.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print("✅ Created plots/token_breakdown_faceted.png")

def main():
    print("🎨 Creating token breakdown visualizations...")

    # Load data
    df = pd.read_csv('analysis/all_log_data.csv')

    # Select only needed columns
    token_df = df[['model', 'question', 'prompt_tokens']].copy()

    print(f"📊 Loaded {len(token_df)} log entries")
    print(f"   {token_df['model'].nunique()} models")
    print(f"   {token_df['question'].nunique()} questions")

    # Create visualizations
    print("\n📈 Creating visualizations...")
    create_grouped_bar_chart(token_df)
    create_heatmap(token_df)
    create_tier_comparison(token_df)
    create_faceted_by_tier(token_df)

    print("\n✅ All token breakdown visualizations created!")
    print("\n💡 Visualization Summary:")
    print("   1. Grouped bar chart (all 22 questions, 9 models) - BUSY but complete")
    print("   2. Heatmap (cleaner, shows patterns) - RECOMMENDED")
    print("   3. By-tier comparison (cleaner, aggregated) - RECOMMENDED")
    print("   4. Faceted by tier (organized by difficulty) - RECOMMENDED")

if __name__ == "__main__":
    main()
