#!/usr/bin/env python3
"""
create_weighted_score_plot.py - generates weighted score visualization
"""

import json
import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
from pathlib import Path

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
        'axes.labelweight': 'normal',
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

def normalize_model_name(filename):
    """Extract and normalize model name from filename"""
    # Remove _evaluation suffix
    name = filename.replace('_evaluation', '')

    # Replace first underscore with /
    parts = name.split('_', 1)
    if len(parts) == 2:
        model_name = parts[0] + '/' + parts[1]
    else:
        model_name = name

    # Remove :free or _free suffix for consistency
    model_name = model_name.replace(':free', '').replace('_free', '')

    return model_name

def load_evaluations():
    """Load all evaluation results"""
    evaluations = defaultdict(lambda: defaultdict(list))

    eval_files = glob.glob("evaluations/*/json/*_evaluation.json")

    for eval_file in eval_files:
        try:
            with open(eval_file, 'r') as f:
                data = json.load(f)

            question_id = data.get('question_id')
            filename = Path(eval_file).stem
            model_name = normalize_model_name(filename)

            # Determine tier
            tier = question_id.split('_')[0] if '_' in question_id else 'tier1'

            evaluations[model_name][question_id] = {
                'total_score': data.get('total_score', 0),
                'tier': tier,
                'passed': data.get('overall_assessment', 'fail') == 'pass'
            }
        except Exception as e:
            print(f"Error loading {eval_file}: {e}")

    return evaluations

def calculate_weighted_score(eval_dict):
    """Calculate weighted score with tier1=1x, tier2=2x, tier3=4x"""
    tier_weights = {'tier1': 1.0, 'tier2': 2.0, 'tier3': 4.0}

    weighted_total = 0
    weight_sum = 0

    for question_id, scores in eval_dict.items():
        tier = scores.get('tier', 'tier1')
        weight = tier_weights.get(tier, 1.0)
        score_normalized = scores['total_score'] / 6.0 * 100

        weighted_total += score_normalized * weight
        weight_sum += weight

    return weighted_total / weight_sum if weight_sum > 0 else 0

def create_weighted_score_chart(evaluations):
    """Create weighted score chart"""
    setup_modern_style()

    # Calculate weighted scores for each model
    model_data = []
    for model_name, eval_dict in evaluations.items():
        weighted_score = calculate_weighted_score(eval_dict)
        total_evals = len(eval_dict)

        model_data.append({
            'model': model_name,
            'weighted_score': weighted_score,
            'total_evals': total_evals
        })

    # Sort by weighted score descending
    model_data.sort(key=lambda x: x['weighted_score'], reverse=True)

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))

    models = [d['model'] for d in model_data]
    scores = [d['weighted_score'] for d in model_data]
    colors = [MODEL_COLORS.get(m, '#6B7280') for m in models]

    bars = ax.barh(models, scores, color=colors, alpha=0.85, edgecolor='white', linewidth=2)

    # Add score labels
    for i, (bar, data) in enumerate(zip(bars, model_data)):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f"{data['weighted_score']:.1f}% ({data['total_evals']} evals)",
                va='center', ha='left', fontweight='bold', fontsize=11)

    ax.set_xlabel('Weighted Score (%)', fontsize=13, fontweight='600')
    ax.set_title('Model Performance on Chemistry Benchmark\nWeighted Score (Tier 1=1x, Tier 2=2x, Tier 3=4x)',
                 fontsize=18, fontweight='bold', pad=20)
    ax.set_xlim(0, 100)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig('plots/weighted_score_performance.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print("✅ Created plots/weighted_score_performance.png")

if __name__ == "__main__":
    print("🎨 Generating weighted score plot...")
    evaluations = load_evaluations()
    print(f"📊 Loaded evaluations for {len(evaluations)} models")

    create_weighted_score_chart(evaluations)
    print("✅ Plot created successfully!")
