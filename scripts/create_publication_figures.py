"""
Create publication-quality figures analyzing LLM agent performance patterns
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Modern styling
def setup_publication_style():
    plt.style.use('seaborn-v0_8-darkgrid')
    sns.set_palette("husl")
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = '#f8f9fa'
    plt.rcParams['font.size'] = 11
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 10

def load_data():
    """Load and merge all analysis data"""
    leaderboard = pd.read_csv('leaderboard/leaderboard_overall.csv')
    efficiency = pd.read_csv('analysis/model_efficiency_stats.csv')
    tool_stats = pd.read_csv('analysis/tool_use_stats.csv')

    # Merge datasets
    df = leaderboard.merge(efficiency, on='model')
    df = df.merge(tool_stats, on='model')

    # Add reasoning tokens from logs
    reasoning_data = {
        'openai/gpt-5': 6112.0,
        'x-ai/grok-code-fast-1': 2788.2,
        'google/gemini-2.5-pro': 2418.6,
        'x-ai/grok-4-fast': 1655.6,
        'openai/o3': 1058.9,
        'anthropic/claude-opus-4.1': 0.0,
        'anthropic/claude-sonnet-4': 0.0,
        'anthropic/claude-sonnet-4.5': 0.0,
        'deepseek/deepseek-chat-v3.1': 0.0
    }
    df['reasoning_tokens'] = df['model'].map(reasoning_data)

    # Calculate derived metrics
    df['score_per_token'] = (df['weighted_score'] / df['total_tokens_mean']) * 1000  # per 1K tokens
    df['score_per_dollar'] = df['weighted_score'] / (df['cost_usd_mean'] + 0.0001)  # avoid div by 0
    df['score_per_tool'] = df['weighted_score'] / df['avg_tool_calls']

    # Add model family
    def get_family(model):
        if 'anthropic' in model:
            return 'Anthropic'
        elif 'openai' in model:
            return 'OpenAI'
        elif 'google' in model:
            return 'Google'
        elif 'x-ai' in model:
            return 'X.AI'
        elif 'deepseek' in model:
            return 'DeepSeek'
        return 'Other'

    df['family'] = df['model'].apply(get_family)

    # Clean model names for display
    df['model_display'] = df['model'].str.replace('anthropic/', '').str.replace('openai/', '').str.replace('google/', '').str.replace('x-ai/', '').str.replace('deepseek/', '')

    return df

def figure1_reasoning_paradox(df):
    """Reasoning tokens vs performance - shows negative correlation"""
    setup_publication_style()
    fig, ax = plt.subplots(figsize=(12, 8))

    # Create scatter plot
    colors = {'Anthropic': '#FF6B35', 'OpenAI': '#004E89', 'Google': '#34A853', 'X.AI': '#8B5CF6', 'DeepSeek': '#059669'}

    for family in df['family'].unique():
        data = df[df['family'] == family]
        ax.scatter(data['reasoning_tokens'], data['weighted_score'],
                  s=200, alpha=0.7, label=family, color=colors.get(family, '#gray'),
                  edgecolors='white', linewidth=2)

    # Add labels for key models
    for _, row in df.iterrows():
        if row['model_display'] in ['claude-sonnet-4', 'gpt-5', 'o3']:
            ax.annotate(row['model_display'],
                       xy=(row['reasoning_tokens'], row['weighted_score']),
                       xytext=(10, 10), textcoords='offset points',
                       fontsize=10, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.3))

    # Add trend line
    z = np.polyfit(df['reasoning_tokens'], df['weighted_score'], 1)
    p = np.poly1d(z)
    x_trend = np.linspace(df['reasoning_tokens'].min(), df['reasoning_tokens'].max(), 100)
    ax.plot(x_trend, p(x_trend), "--", color='red', alpha=0.5, linewidth=2, label=f'Trend (slope={z[0]:.4f})')

    ax.set_xlabel('Reasoning Tokens per Question', fontsize=14, fontweight='bold')
    ax.set_ylabel('Weighted Performance Score (%)', fontsize=14, fontweight='bold')
    ax.set_title('The Reasoning Token Paradox:\nMore "Thinking" Does Not Improve Chemistry Task Performance',
                 fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='best', frameon=True, shadow=True)
    ax.grid(True, alpha=0.3)

    # Add insight text
    ax.text(0.98, 0.02, 'Key Finding: Claude (0 reasoning tokens) outperforms GPT-5 (6,112 tokens)\nSuggests reasoning tokens may introduce confusion in complex scientific tasks',
            transform=ax.transAxes, fontsize=10, verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig('plots/publication_figures/1_reasoning_paradox.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created 1_reasoning_paradox.png")

def figure2_tool_efficiency_curve(df):
    """Tool calls vs performance - shows inverted U"""
    setup_publication_style()
    fig, ax = plt.subplots(figsize=(12, 8))

    colors = {'Anthropic': '#FF6B35', 'OpenAI': '#004E89', 'Google': '#34A853', 'X.AI': '#8B5CF6', 'DeepSeek': '#059669'}

    for family in df['family'].unique():
        data = df[df['family'] == family]
        ax.scatter(data['avg_tool_calls'], data['weighted_score'],
                  s=200, alpha=0.7, label=family, color=colors.get(family, '#gray'),
                  edgecolors='white', linewidth=2)

    # Add labels for all models
    for _, row in df.iterrows():
        ax.annotate(row['model_display'],
                   xy=(row['avg_tool_calls'], row['weighted_score']),
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=9, alpha=0.8)

    # Highlight optimal range
    ax.axvspan(10, 13, alpha=0.1, color='green', label='Optimal Range (10-13 tools)')

    # Add quadratic trend line
    z = np.polyfit(df['avg_tool_calls'], df['weighted_score'], 2)
    p = np.poly1d(z)
    x_trend = np.linspace(df['avg_tool_calls'].min(), df['avg_tool_calls'].max(), 100)
    ax.plot(x_trend, p(x_trend), "--", color='red', alpha=0.5, linewidth=2, label='Quadratic Trend')

    ax.set_xlabel('Average Tool Calls per Question', fontsize=14, fontweight='bold')
    ax.set_ylabel('Weighted Performance Score (%)', fontsize=14, fontweight='bold')
    ax.set_title('Tool Call Efficiency Curve:\nSweet Spot at 10-13 Tools per Question',
                 fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='best', frameon=True, shadow=True)
    ax.grid(True, alpha=0.3)

    # Add insight zones
    ax.text(4.5, 35, 'Too Few\n(Incomplete)', fontsize=11, ha='center', color='red', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    ax.text(11.5, 90, 'Optimal\n(Strategic)', fontsize=11, ha='center', color='green', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    ax.text(22, 71, 'Too Many\n(Confused)', fontsize=11, ha='center', color='orange', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

    plt.tight_layout()
    plt.savefig('plots/publication_figures/2_tool_efficiency_curve.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created 2_tool_efficiency_curve.png")

def figure3_speed_quality_cost(df):
    """3D trade-off: speed, quality, cost"""
    setup_publication_style()
    fig, ax = plt.subplots(figsize=(14, 10))

    colors = {'Anthropic': '#FF6B35', 'OpenAI': '#004E89', 'Google': '#34A853', 'X.AI': '#8B5CF6', 'DeepSeek': '#059669'}

    # Bubble size = median time (normalized)
    sizes = (df['time_s_median'] / df['time_s_median'].max()) * 2000 + 100

    for family in df['family'].unique():
        data = df[df['family'] == family]
        bubble_sizes = (data['time_s_median'] / df['time_s_median'].max()) * 2000 + 100
        ax.scatter(data['cost_usd_mean'], data['weighted_score'],
                  s=bubble_sizes, alpha=0.6, label=family, color=colors.get(family, '#gray'),
                  edgecolors='white', linewidth=2)

    # Add labels
    for _, row in df.iterrows():
        ax.annotate(row['model_display'],
                   xy=(row['cost_usd_mean'], row['weighted_score']),
                   xytext=(8, 8), textcoords='offset points',
                   fontsize=9, fontweight='bold')

    # Pareto frontier (models not dominated on both axes)
    pareto_models = []
    for i, row1 in df.iterrows():
        dominated = False
        for j, row2 in df.iterrows():
            if i != j:
                # row2 dominates row1 if it's both cheaper AND better
                if row2['cost_usd_mean'] <= row1['cost_usd_mean'] and row2['weighted_score'] >= row1['weighted_score']:
                    if row2['cost_usd_mean'] < row1['cost_usd_mean'] or row2['weighted_score'] > row1['weighted_score']:
                        dominated = True
                        break
        if not dominated:
            pareto_models.append(row1)

    if pareto_models:
        pareto_df = pd.DataFrame(pareto_models).sort_values('cost_usd_mean')
        ax.plot(pareto_df['cost_usd_mean'], pareto_df['weighted_score'],
               'r--', linewidth=2, alpha=0.5, label='Pareto Frontier', zorder=1)

    ax.set_xlabel('Average Cost per Question (USD)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Weighted Performance Score (%)', fontsize=14, fontweight='bold')
    ax.set_title('Speed-Quality-Cost Triangle\n(Bubble Size = Median Completion Time)',
                 fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='upper left', frameon=True, shadow=True, fontsize=10)
    ax.grid(True, alpha=0.3)

    # Log scale for cost if range is large
    if df['cost_usd_mean'].max() / (df['cost_usd_mean'][df['cost_usd_mean'] > 0].min() + 0.001) > 100:
        ax.set_xscale('log')

    # Add size legend
    legend_sizes = [100, 500, 1000]
    legend_times = [50, 250, 500]
    for size, time in zip(legend_sizes, legend_times):
        ax.scatter([], [], s=size, c='gray', alpha=0.5, edgecolors='white', linewidth=2, label=f'{time}s')
    ax.legend(loc='upper left', frameon=True, shadow=True, fontsize=9, title='Median Time')

    plt.tight_layout()
    plt.savefig('plots/publication_figures/3_speed_quality_cost.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created 3_speed_quality_cost.png")

def figure4_completion_vs_correctness(df):
    """Completion rate vs pass rate gap"""
    setup_publication_style()
    fig, ax = plt.subplots(figsize=(12, 8))

    x = np.arange(len(df))
    width = 0.35

    # Sort by pass_rate
    df_sorted = df.sort_values('pass_rate', ascending=False)

    bars1 = ax.bar(x - width/2, df_sorted['completion_rate'] * 100, width,
                   label='Completion Rate', color='#3498db', alpha=0.8, edgecolor='white', linewidth=1.5)
    bars2 = ax.bar(x + width/2, df_sorted['pass_rate'], width,
                   label='Pass Rate (Correct)', color='#2ecc71', alpha=0.8, edgecolor='white', linewidth=1.5)

    # Calculate and show gap
    gaps = (df_sorted['completion_rate'] * 100 - df_sorted['pass_rate']).abs()
    for i, (bar1, bar2, gap) in enumerate(zip(bars1, bars2, gaps)):
        if gap > 5:  # Only show significant gaps
            height = max(bar1.get_height(), bar2.get_height())
            ax.plot([i - width/2, i + width/2], [height + 3, height + 3], 'r-', linewidth=2)
            ax.text(i, height + 5, f'{gap:.0f}%', ha='center', fontsize=9, color='red', fontweight='bold')

    ax.set_xlabel('Model', fontsize=14, fontweight='bold')
    ax.set_ylabel('Rate (%)', fontsize=14, fontweight='bold')
    ax.set_title('Completion vs Correctness Gap:\n"Finishing" ≠ "Correct Answer"',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(df_sorted['model_display'], rotation=45, ha='right')
    ax.legend(frameon=True, shadow=True)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, 110)

    # Highlight o3 case
    o3_idx = df_sorted[df_sorted['model_display'] == 'o3'].index[0]
    o3_pos = df_sorted.index.get_loc(o3_idx)
    ax.annotate('100% complete,\nonly 13.6% correct!',
               xy=(o3_pos, 50), xytext=(o3_pos + 2, 70),
               arrowprops=dict(arrowstyle='->', color='red', lw=2),
               fontsize=10, fontweight='bold', color='red',
               bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

    plt.tight_layout()
    plt.savefig('plots/publication_figures/4_completion_vs_correctness.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created 4_completion_vs_correctness.png")

def figure5_performance_per_dollar(df):
    """ROI analysis"""
    setup_publication_style()
    fig, ax = plt.subplots(figsize=(12, 8))

    df_sorted = df.sort_values('score_per_dollar', ascending=True)

    # Handle infinite values for free models
    df_plot = df_sorted.copy()
    df_plot.loc[df_plot['cost_usd_mean'] == 0, 'score_per_dollar'] = df_plot[df_plot['cost_usd_mean'] > 0]['score_per_dollar'].max() * 2

    colors = ['#e74c3c' if x < 100 else '#f39c12' if x < 200 else '#2ecc71' for x in df_plot['score_per_dollar']]

    bars = ax.barh(range(len(df_plot)), df_plot['score_per_dollar'], color=colors, alpha=0.8, edgecolor='white', linewidth=1.5)

    ax.set_yticks(range(len(df_plot)))
    ax.set_yticklabels(df_plot['model_display'])
    ax.set_xlabel('Performance Points per Dollar (Weighted Score / Cost)', fontsize=14, fontweight='bold')
    ax.set_title('Return on Investment:\nPerformance per Dollar Spent',
                 fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, axis='x')

    # Add value labels
    for i, (bar, row) in enumerate(zip(bars, df_plot.iterrows())):
        width = bar.get_width()
        if row[1]['cost_usd_mean'] == 0:
            label = 'FREE (∞ ROI)'
        else:
            label = f'{width:.0f}'
        ax.text(width + max(df_plot['score_per_dollar']) * 0.02, bar.get_y() + bar.get_height()/2,
               label, ha='left', va='center', fontsize=9, fontweight='bold')

    # Add cost annotations
    for i, row in df_plot.iterrows():
        if row['cost_usd_mean'] > 0:
            ax.text(5, i, f'${row["cost_usd_mean"]:.2f}',
                   ha='left', va='center', fontsize=8, color='white', fontweight='bold')

    plt.tight_layout()
    plt.savefig('plots/publication_figures/5_performance_per_dollar.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created 5_performance_per_dollar.png")

def figure6_token_efficiency(df):
    """Token usage vs performance"""
    setup_publication_style()
    fig, ax = plt.subplots(figsize=(12, 8))

    colors = {'Anthropic': '#FF6B35', 'OpenAI': '#004E89', 'Google': '#34A853', 'X.AI': '#8B5CF6', 'DeepSeek': '#059669'}

    for family in df['family'].unique():
        data = df[df['family'] == family]
        ax.scatter(data['total_tokens_mean']/1000, data['weighted_score'],
                  s=200, alpha=0.7, label=family, color=colors.get(family, '#gray'),
                  edgecolors='white', linewidth=2)

    # Add efficiency diagonal lines
    for efficiency in [0.1, 0.2, 0.3, 0.4]:
        x_line = np.linspace(50, 600, 100)
        y_line = x_line * efficiency
        ax.plot(x_line, y_line, '--', alpha=0.2, color='gray', linewidth=1)
        ax.text(x_line[-1], y_line[-1], f'{efficiency:.1f} pts/1K tok',
               fontsize=8, alpha=0.5, rotation=20)

    # Add labels for key models
    for _, row in df.iterrows():
        ax.annotate(f"{row['model_display']}\n{row['score_per_token']:.2f} pts/1K",
                   xy=(row['total_tokens_mean']/1000, row['weighted_score']),
                   xytext=(10, 10), textcoords='offset points',
                   fontsize=8, alpha=0.8)

    ax.set_xlabel('Average Total Tokens per Question (thousands)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Weighted Performance Score (%)', fontsize=14, fontweight='bold')
    ax.set_title('Token Efficiency Paradox:\nMore Tokens ≠ Better Performance',
                 fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='best', frameon=True, shadow=True)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('plots/publication_figures/6_token_efficiency.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created 6_token_efficiency.png")

def figure7_cost_breakdown_by_model(df):
    """Show cost components: input, output, reasoning tokens"""
    setup_publication_style()
    fig, ax = plt.subplots(figsize=(14, 8))

    # Sort by total cost
    df_sorted = df.sort_values('cost_usd_mean', ascending=False)

    # Approximate breakdown (would need actual data for precise values)
    # For now, use reasoning token proportion as proxy
    df_sorted['cost_reasoning'] = (df_sorted['reasoning_tokens'] / df_sorted['total_tokens_mean']) * df_sorted['cost_usd_mean']
    df_sorted['cost_other'] = df_sorted['cost_usd_mean'] - df_sorted['cost_reasoning']

    x = range(len(df_sorted))
    width = 0.6

    bars1 = ax.bar(x, df_sorted['cost_other'], width, label='Input/Output Tokens',
                   color='#3498db', alpha=0.8, edgecolor='white', linewidth=1.5)
    bars2 = ax.bar(x, df_sorted['cost_reasoning'], width, bottom=df_sorted['cost_other'],
                   label='Reasoning Tokens', color='#e74c3c', alpha=0.8, edgecolor='white', linewidth=1.5)

    ax.set_ylabel('Average Cost per Question (USD)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Model', fontsize=14, fontweight='bold')
    ax.set_title('Cost Breakdown by Model:\nReasoning Token Overhead',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(df_sorted['model_display'], rotation=45, ha='right')
    ax.legend(frameon=True, shadow=True)
    ax.grid(True, alpha=0.3, axis='y')

    # Add total cost labels
    for i, (bar, cost, score) in enumerate(zip(bars2, df_sorted['cost_usd_mean'], df_sorted['weighted_score'])):
        if cost > 0.01:
            ax.text(i, bar.get_height() + bar.get_y() + 0.1,
                   f'${cost:.2f}\n({score:.1f}%)',
                   ha='center', va='bottom', fontsize=8, fontweight='bold')

    plt.tight_layout()
    plt.savefig('plots/publication_figures/7_cost_breakdown.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created 7_cost_breakdown.png")

def figure8_multidimensional_comparison(df):
    """Radar/spider chart showing multiple dimensions"""
    setup_publication_style()

    # Select top 5 models by weighted score
    top_models = df.nlargest(5, 'weighted_score')

    # Normalize metrics to 0-100 scale
    metrics = ['weighted_score', 'score_per_dollar', 'score_per_token', 'score_per_tool', 'completion_rate']
    metric_labels = ['Performance', 'ROI', 'Token Efficiency', 'Tool Efficiency', 'Completion Rate']

    normalized = top_models.copy()
    for metric in metrics:
        if metric == 'weighted_score' or metric == 'completion_rate':
            # Already in percentage
            normalized[metric + '_norm'] = normalized[metric]
        else:
            # Normalize to 0-100
            max_val = df[metric].max()
            min_val = df[metric].min()
            if max_val > min_val:
                normalized[metric + '_norm'] = ((normalized[metric] - min_val) / (max_val - min_val)) * 100
            else:
                normalized[metric + '_norm'] = 50

    # Create radar chart
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]  # Complete the circle

    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(projection='polar'))

    colors_list = ['#FF6B35', '#004E89', '#34A853', '#8B5CF6', '#059669']

    for idx, (i, row) in enumerate(normalized.iterrows()):
        values = [row[metric + '_norm'] for metric in metrics]
        values += values[:1]  # Complete the circle

        ax.plot(angles, values, 'o-', linewidth=2, label=row['model_display'],
               color=colors_list[idx % len(colors_list)])
        ax.fill(angles, values, alpha=0.15, color=colors_list[idx % len(colors_list)])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metric_labels, fontsize=12)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=10)
    ax.set_title('Multidimensional Model Comparison\n(Top 5 Models)',
                fontsize=16, fontweight='bold', pad=30)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), frameon=True, shadow=True)
    ax.grid(True)

    plt.tight_layout()
    plt.savefig('plots/publication_figures/8_multidimensional_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created 8_multidimensional_comparison.png")

def figure9_time_distribution(df):
    """Distribution of completion times by model"""
    setup_publication_style()
    fig, ax = plt.subplots(figsize=(14, 8))

    df_sorted = df.sort_values('time_s_median')

    # Create box plot effect with bars and error ranges
    x = range(len(df_sorted))
    colors = ['#2ecc71' if t < 200 else '#f39c12' if t < 500 else '#e74c3c'
             for t in df_sorted['time_s_median']]

    bars = ax.bar(x, df_sorted['time_s_median'], color=colors, alpha=0.7,
                 edgecolor='white', linewidth=1.5, label='Median Time')

    # Add mean as a line
    ax.scatter(x, df_sorted['time_s_mean'], color='red', s=100, zorder=5,
              marker='D', label='Mean Time', edgecolor='white', linewidth=1)

    ax.set_xticks(x)
    ax.set_xticklabels(df_sorted['model_display'], rotation=45, ha='right')
    ax.set_ylabel('Completion Time (seconds)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Model', fontsize=14, fontweight='bold')
    ax.set_title('Completion Time Distribution:\nSpeed vs Quality Trade-off',
                 fontsize=16, fontweight='bold', pad=20)
    ax.legend(frameon=True, shadow=True)
    ax.grid(True, alpha=0.3, axis='y')

    # Add performance score as text
    for i, (bar, score) in enumerate(zip(bars, df_sorted['weighted_score'])):
        ax.text(i, bar.get_height() + 20, f'{score:.1f}%',
               ha='center', va='bottom', fontsize=9, fontweight='bold', rotation=0)

    # Add speed categories
    ax.axhline(y=200, color='green', linestyle='--', alpha=0.3, linewidth=2)
    ax.axhline(y=500, color='orange', linestyle='--', alpha=0.3, linewidth=2)
    ax.text(len(x) - 0.5, 100, 'Fast', fontsize=10, color='green', fontweight='bold', ha='right')
    ax.text(len(x) - 0.5, 350, 'Medium', fontsize=10, color='orange', fontweight='bold', ha='right')
    ax.text(len(x) - 0.5, 700, 'Slow', fontsize=10, color='red', fontweight='bold', ha='right')

    plt.tight_layout()
    plt.savefig('plots/publication_figures/9_time_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Created 9_time_distribution.png")

if __name__ == "__main__":
    print("🎨 Creating publication-quality figures...\n")

    # Load data
    print("📊 Loading data...")
    df = load_data()
    print(f"   Loaded {len(df)} models\n")

    # Generate all figures
    print("📈 Generating figures...\n")

    figure1_reasoning_paradox(df)
    figure2_tool_efficiency_curve(df)
    figure3_speed_quality_cost(df)
    figure4_completion_vs_correctness(df)
    figure5_performance_per_dollar(df)
    figure6_token_efficiency(df)
    figure7_cost_breakdown_by_model(df)
    figure8_multidimensional_comparison(df)
    figure9_time_distribution(df)

    print(f"\n✅ All publication figures created in plots/publication_figures/")
    print("\n📊 Figure Summary:")
    print("   1. Reasoning Token Paradox - More thinking ≠ better results")
    print("   2. Tool Efficiency Curve - Optimal range at 10-13 tools")
    print("   3. Speed-Quality-Cost Triangle - Can't optimize all three")
    print("   4. Completion vs Correctness - Finishing ≠ correct")
    print("   5. Performance per Dollar - ROI analysis")
    print("   6. Token Efficiency - More tokens ≠ better performance")
    print("   7. Cost Breakdown - Reasoning token overhead")
    print("   8. Multidimensional Comparison - Radar chart of top 5")
    print("   9. Time Distribution - Speed categories")
