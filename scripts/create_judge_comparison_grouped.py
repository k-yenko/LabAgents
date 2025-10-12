#!/usr/bin/env python3
"""
Create grouped bar chart comparing Claude Sonnet 4 vs Qwen judge scores
"""

import json
import glob
import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path
from collections import defaultdict
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image

# Modern professional color palette (matching overall_performance.png)
MODEL_COLORS = {
    'anthropic/claude-opus-4.1': '#8B5CF6',
    'anthropic/claude-sonnet-4.5': '#A78BFA',
    'anthropic/claude-sonnet-4': '#C4B5FD',
    'openai/gpt-5': '#10B981',
    'openai/o3': '#34D399',
    'google/gemini-2.5-pro': '#F59E0B',
    'deepseek/deepseek-chat-v3.1:free': '#3B82F6',
    'x-ai/grok-4-fast': '#EC4899',
    'x-ai/grok-code-fast-1': '#F472B6',
}

company_logos = {
    'anthropic': 'logos/claude-icon.png',
    'openai': 'logos/openai.svg',
    'google': 'logos/gemini-2.5.webp',
    'x-ai': 'logos/xai-logo-hd.webp',
    'deepseek': 'logos/deepseek.png'
}

def setup_modern_style():
    """Setup modern, clean chart styling"""
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

def load_evaluations(eval_dir):
    """Load all evaluation results from a directory"""
    evaluations = defaultdict(dict)

    eval_pattern = f"{eval_dir}/*/json/*_evaluation.json"
    eval_files = glob.glob(eval_pattern)

    for eval_file in eval_files:
        try:
            with open(eval_file, 'r') as f:
                data = json.load(f)

            question_id = data.get('question_id')

            # Extract model name from filename
            filename = Path(eval_file).stem
            model_name = filename.replace('_evaluation', '').replace('_', '/', 1)

            # Handle special cases
            if 'deepseek' in model_name:
                model_name = model_name.replace('_', ':', 1)
            if 'grok' in model_name and 'free' in model_name:
                model_name = model_name.replace('_free', ':free')

            tier = question_id.split('_')[0] if '_' in question_id else 'tier1'

            evaluations[question_id][model_name] = {
                'total_score': data.get('total_score', 0),
                'tier': tier
            }
        except Exception as e:
            print(f"Error loading {eval_file}: {e}")

    return evaluations

def calculate_weighted_scores(evaluations):
    """Calculate weighted scores for each model"""
    tier_weights = {'tier1': 1, 'tier2': 2, 'tier3': 4}
    model_scores = defaultdict(lambda: {'weighted_sum': 0, 'weight_sum': 0})

    for question_id, models in evaluations.items():
        tier = list(models.values())[0]['tier'] if models else 'tier1'
        weight = tier_weights.get(tier, 1)

        for model_name, data in models.items():
            score = data['total_score']
            model_scores[model_name]['weighted_sum'] += score * weight
            model_scores[model_name]['weight_sum'] += 6 * weight  # max score is 6

    # Calculate percentages
    results = {}
    for model_name, data in model_scores.items():
        if data['weight_sum'] > 0:
            results[model_name] = (data['weighted_sum'] / data['weight_sum']) * 100

    return results

def create_grouped_comparison():
    """Create grouped bar chart comparing judges"""
    setup_modern_style()

    # Load evaluations from both judges
    print("Loading Claude Sonnet 4 judge evaluations...")
    sonnet_evals = load_evaluations('evaluations_sonnet4')
    sonnet_scores = calculate_weighted_scores(sonnet_evals)

    print("Loading Qwen judge evaluations...")
    qwen_evals = load_evaluations('evaluations_qwen')
    qwen_scores = calculate_weighted_scores(qwen_evals)

    # Get all models (intersection of both judges)
    all_models = set(sonnet_scores.keys()) & set(qwen_scores.keys())

    # Sort by AVERAGE score (highest to lowest)
    models_sorted = sorted(all_models, key=lambda m: (sonnet_scores[m] + qwen_scores[m]) / 2, reverse=True)

    # Clean up model names (remove :free)
    model_display = [m.split('/')[-1].replace(':free', '') for m in models_sorted]

    # Prepare data
    sonnet_values = [sonnet_scores[m] for m in models_sorted]
    qwen_values = [qwen_scores[m] for m in models_sorted]

    # Get model colors
    colors = [MODEL_COLORS.get(m, '#6B7280') for m in models_sorted]

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))

    x = np.arange(len(models_sorted))
    width = 0.35

    # Set xlim before drawing bars to make room for logos
    ax.set_xlim(-8, 105)

    # Create grouped bars using model-specific colors
    bars1 = ax.barh(x - width/2, sonnet_values, width,
                    label='Claude Sonnet 4 Judge',
                    color=colors, alpha=0.85,
                    edgecolor='white', linewidth=2)
    bars2 = ax.barh(x + width/2, qwen_values, width,
                    label='Qwen Judge',
                    color=colors, alpha=0.5,  # Lighter for secondary
                    edgecolor='white', linewidth=2)

    # Add value labels (matching overall_performance.png label style)
    for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
        # Sonnet score
        width1 = bar1.get_width()
        ax.text(width1 + 1, bar1.get_y() + bar1.get_height()/2,
               f'{width1:.1f}%', va='center', ha='left', fontsize=11, fontweight='bold')

        # Qwen score
        width2 = bar2.get_width()
        ax.text(width2 + 1, bar2.get_y() + bar2.get_height()/2,
               f'{width2:.1f}%', va='center', ha='left', fontsize=11, fontweight='bold')

    # Add company logos to the left of y-axis labels
    for i, (model, y_pos) in enumerate(zip(models_sorted, range(len(models_sorted)))):
        company = model.split('/')[0] if '/' in model else ''
        logo_path = company_logos.get(company)

        if logo_path and os.path.exists(logo_path):
            try:
                if logo_path.endswith('.svg'):
                    ax.text(-4, y_pos, '○', va='center', ha='center', fontsize=14, color='gray')
                else:
                    img = Image.open(logo_path)
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    imagebox = OffsetImage(img, zoom=0.04)
                    ab = AnnotationBbox(imagebox, (-4, y_pos), frameon=False,
                                       xycoords='data', box_alignment=(0.5, 0.5),
                                       clip_on=False)
                    ax.add_artist(ab)
            except Exception as e:
                print(f"Warning: Could not load logo {logo_path}: {e}")
                ax.text(-4, y_pos, '○', va='center', ha='center', fontsize=14, color='gray')
        else:
            ax.text(-4, y_pos, '○', va='center', ha='center', fontsize=14, color='gray')

    # Customize (matching overall_performance.png style)
    ax.set_xlabel('Weighted Score (%)', fontsize=13, fontweight='600')
    ax.set_title('Comparing Foundational Models for Chemical Tool Use\n22 evaluations per model • weighted by task tier (1x/2x/4x)',
                fontsize=18, fontweight='bold', pad=20)
    ax.set_yticks(x)
    ax.set_yticklabels(model_display, fontsize=10)
    ax.set_xlim(0, 100)
    ax.legend(loc='lower right', fontsize=11, framealpha=0.9)

    # Hide top and right spines (matching overall_performance.png)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig('plots/judge_comparison/judge_grouped_comparison.png',
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print("\nGrouped comparison saved to: plots/judge_comparison/judge_grouped_comparison.png")

    # Print summary
    print("\n" + "="*70)
    print("JUDGE COMPARISON SUMMARY")
    print("="*70)
    for model, sonnet, qwen in zip(model_display, sonnet_values, qwen_values):
        diff = qwen - sonnet
        print(f"{model:20s} | Sonnet: {sonnet:5.1f}% | Qwen: {qwen:5.1f}% | Diff: {diff:+5.1f}")
    print("="*70)

if __name__ == "__main__":
    create_grouped_comparison()
