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
    plt.savefig('plots/efficiency/cost_efficiency.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created plots/efficiency/cost_efficiency.png")

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
    plt.savefig('plots/efficiency/speed_comparison.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created plots/efficiency/speed_comparison.png")

def create_token_usage_plot(df):
    """Token usage comparison with breakdown - styled to match overall_performance.png"""
    from matplotlib.offsetbox import OffsetImage, AnnotationBbox
    from PIL import Image
    
    # Modern font stack matching overall_performance.png
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Inter', 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', 'Arial', 'DejaVu Sans'],
        'font.size': 11,
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'figure.dpi': 200,
        'savefig.dpi': 400,
    })

    # Group by model and calculate averages
    token_data = df.groupby('model').agg({
        'prompt_tokens': 'mean',
        'completion_tokens': 'mean',
        'reasoning_tokens': 'mean'
    })
    
    # Calculate total and sort by total descending (highest at top)
    token_data['total'] = token_data['prompt_tokens'] + token_data['completion_tokens'] + token_data['reasoning_tokens']
    token_data = token_data.sort_values('total', ascending=False)

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))

    models = token_data.index
    
    # Clean model names
    clean_names = [m.split('/')[-1].replace(':free', '') if '/' in m else m.replace(':free', '') for m in models]
    
    # Stack: prompt, completion, reasoning
    prompt_tokens = token_data['prompt_tokens'].values
    completion_tokens = token_data['completion_tokens'].values
    reasoning_tokens = token_data['reasoning_tokens'].values

    # Plot stacked bars
    bars1 = ax.barh(clean_names, prompt_tokens, color='#93C5FD', alpha=0.85, label='Input', edgecolor='white', linewidth=2)
    bars2 = ax.barh(clean_names, completion_tokens, left=prompt_tokens, color='#34D399', alpha=0.85, label='Output', edgecolor='white', linewidth=2)
    bars3 = ax.barh(clean_names, reasoning_tokens, left=prompt_tokens + completion_tokens, color='#FBBF24', alpha=0.85, label='Reasoning', edgecolor='white', linewidth=2)
    
    # Invert y-axis so highest is at top
    ax.invert_yaxis()
    
    # Add individual data points (no jitter - all in center)
    # Create a mapping of model to y-position
    model_to_y = {model: i for i, model in enumerate(models)}
    
    # Calculate total tokens for each individual data point
    df_copy = df.copy()
    df_copy['total_tokens_calc'] = df_copy['prompt_tokens'] + df_copy['completion_tokens'] + df_copy['reasoning_tokens']
    
    # Plot individual points in center of each bar
    for model in models:
        model_data = df_copy[df_copy['model'] == model]
        if len(model_data) > 0:
            y_pos = model_to_y[model]
            
            # All points at the center y position
            y_positions = np.full(len(model_data), y_pos)
            
            # Plot points with modern styling
            ax.scatter(model_data['total_tokens_calc'], y_positions, 
                      color='#6366F1', alpha=0.6, s=25, zorder=10, 
                      edgecolor='white', linewidth=0.5)
    
    # Use log scale for x-axis to show outliers without compression
    ax.set_xscale('log')
    
    # Logo mapping
    model_to_logo = {
        'claude-sonnet-4': 'logos/claude-icon.png',
        'claude-sonnet-4.5': 'logos/claude-icon.png',
        'claude-opus-4.1': 'logos/claude-icon.png',
        'gpt-5': 'logos/openai.webp',
        'o3': 'logos/openai.webp',
        'gemini-2.5-pro': 'logos/gemini-2.5.webp',
        'deepseek-chat-v3.1': 'logos/deepseek.png',
        'grok-4-fast': 'logos/xai-logo-hd.webp',
        'grok-code-fast-1': 'logos/xai-logo-hd.webp',
    }
    
    def load_logo_hd(filepath, target_size=32):
        try:
            img = Image.open(filepath)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            w, h = img.size
            if min(w, h) > target_size * 4:
                if w > h:
                    nw = target_size * 2
                    nh = int(nw * h / w)
                else:
                    nh = target_size * 2
                    nw = int(nh * w / h)
                img = img.resize((nw, nh), Image.Resampling.LANCZOS)
            return np.array(img)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return None
    
    # Add logos and total labels
    # For log scale, use multiplicative offset
    for i, (model, clean_name) in enumerate(zip(models, clean_names)):
        total = prompt_tokens[i] + completion_tokens[i] + reasoning_tokens[i]
        
        # Position logo at end of bar with multiplicative offset for log scale
        logo_x = total * 1.15  # 15% beyond bar end
        logo_y = i
        
        logo_path = model_to_logo.get(clean_name)
        if logo_path and os.path.exists(logo_path):
            logo_img = load_logo_hd(logo_path, target_size=28)
            if logo_img is not None:
                try:
                    imagebox = OffsetImage(logo_img, zoom=0.5, interpolation='none', resample=False)
                    ab = AnnotationBbox(imagebox, (logo_x, logo_y), 
                                      xycoords='data',
                                      box_alignment=(0.5, 0.5),
                                      frameon=False,
                                      clip_on=False)
                    ax.add_artist(ab)
                except Exception as e:
                    print(f"Error adding logo for {clean_name}: {e}")
        
        # Add total label after logo
        label_x = total * 1.35  # Further beyond for label
        ax.text(label_x, i, f"{total/1000:.0f}K", va='center', ha='left', fontweight='bold', fontsize=11)

    ax.set_xlabel('Tokens per Question (log scale)', fontsize=13, fontweight='600')
    
    # Title and subtitle matching overall_performance.png
    main_title = 'Model Token Usage Breakdown'
    subtitle = 'Bars = averages, dots = individual questions'
    plt.subplots_adjust(top=0.84)
    fig.suptitle(main_title, fontsize=22, fontweight='bold', y=0.975)
    fig.text(0.5, 0.932, subtitle, ha='center', va='top', fontsize=14, color='#444444')
    
    ax.legend(loc='lower right', fontsize=11, framealpha=0.95)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig('plots/token_analysis/token_usage.png', dpi=400, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created plots/token_analysis/token_usage.png")

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
    plt.savefig('plots/efficiency/tool_usage.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created plots/efficiency/tool_usage.png")

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
    plt.savefig('plots/efficiency/o3_paradox.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created plots/efficiency/o3_paradox.png")

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
    plt.savefig('plots/efficiency/cost_vs_performance.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Created plots/efficiency/cost_vs_performance.png")

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
    for eval_file in glob.glob("evaluations_sonnet4/*/json/*_evaluation.json"):
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
