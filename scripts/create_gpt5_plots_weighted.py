#!/usr/bin/env python3
"""
Create GPT-5 judge plots with the same style as the main overall_performance chart.
Reads from: evaluations_gpt5/{question_id}/json/{model}_evaluation.json
Outputs: plots/gpt5_judge/overall_performance.png (and companion plots if needed)
"""

import json
import os
import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from collections import defaultdict
from pathlib import Path

# Modern professional color palette (same as other scripts)
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

def setup_modern_style():
    """Setup modern, clean chart styling."""
    sns.set_style("whitegrid")
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Inter', 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', 'Arial', 'DejaVu Sans'],
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

def load_all_evaluations():
    """Load all GPT-5 judge evaluation results."""
    evaluations = defaultdict(dict)

    eval_pattern = "/Users/katherineyenko/Desktop/sandbox/labagents/evaluations_gpt5/*/json/*_evaluation.json"
    eval_files = glob.glob(eval_pattern)

    for eval_file in eval_files:
        try:
            with open(eval_file, 'r') as f:
                data = json.load(f)

            question_id = data.get('question_id')

            # Extract model name from filename
            filename = Path(eval_file).stem
            model_name = filename.replace('_evaluation', '').replace('_', '/', 1)

            if 'deepseek' in model_name:
                model_name = model_name.replace('_', ':', 1)
            if 'grok' in model_name and 'free' in model_name:
                model_name = model_name.replace('_free', ':free')

            # Determine tier for weighting from question_id
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

def create_overall_performance_chart(evaluations):
    setup_modern_style()

    # Aggregate model scores
    model_data = []
    for model_name in set(m for models in evaluations.values() for m in models.keys()):
        model_evals = []
        for _, models in evaluations.items():
            if model_name in models:
                model_evals.append(models[model_name])
        weighted_score = calculate_weighted_score(model_evals)
        total_evals = len(model_evals)
        model_data.append({'model': model_name, 'weighted_score': weighted_score, 'total_evals': total_evals})

    # Sort best first
    model_data.sort(key=lambda x: x['weighted_score'], reverse=True)

    # Prepare plot
    fig, ax = plt.subplots(figsize=(14, 8))
    models = [d['model'] for d in model_data]
    clean_names = [m.split('/')[-1] if '/' in m else m for m in models]
    scores = [d['weighted_score'] for d in model_data]
    colors = [MODEL_COLORS.get(m, '#6B7280') for m in models]

    bars = ax.barh(clean_names, scores, color=colors, alpha=0.85, edgecolor='white', linewidth=2)
    ax.invert_yaxis()

    # HD logos at bar ends
    from matplotlib.offsetbox import OffsetImage, AnnotationBbox
    from PIL import Image

    def _load_logo_hd(path, target_size=28):
        img = Image.open(path)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
        return np.array(img)

    company_logos = {
        'anthropic': 'logos/claude-icon.png',
        'openai': 'logos/openai.webp',
        'google': 'logos/gemini-2.5.webp',
        'x-ai': 'logos/xai-logo-hd.webp',
        'deepseek': 'logos/deepseek.png'
    }

    for bar, model in zip(bars, models):
        x = bar.get_width() + 1.5
        y = bar.get_y() + bar.get_height() / 2
        company = model.split('/')[-2] if '/' in model else ''
        # Alternative extraction if above fails
        if company not in company_logos and '/' in model:
            company = model.split('/')[0]
        logo_path = company_logos.get(company)
        if logo_path and os.path.exists(logo_path):
            try:
                img = _load_logo_hd(logo_path, 28)
                ab = AnnotationBbox(OffsetImage(img, zoom=1.0, interpolation='none'), (x, y),
                                    xycoords='data', frameon=False, box_alignment=(0.5, 0.5), clip_on=False)
                ax.add_artist(ab)
            except Exception as e:
                print(f"Warning: could not add logo {logo_path}: {e}")
        ax.text(x + 2.5, y, f"{bar.get_width():.1f}%", va='center', ha='left', fontweight='bold', fontsize=11)

    # Axis and titles (matching main chart)
    ax.set_xlabel('Weighted Score (%)', fontsize=13, fontweight='600')
    ax.set_xlim(0, 100)

    total_evals = model_data[0]['total_evals'] if model_data else 0
    main_title = 'Comparing Foundational Models for Chemical Tool Use'
    subtitle = f'{total_evals} evaluations per model • weighted by task tier (1x/2x/4x)'
    plt.subplots_adjust(top=0.84)
    fig.suptitle(main_title, fontsize=22, fontweight='bold', y=0.975)
    fig.text(0.5, 0.932, subtitle, ha='center', va='top', fontsize=14, color='#444444')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    out_dir = '/Users/katherineyenko/Desktop/sandbox/labagents/plots/gpt5_judge'
    os.makedirs(out_dir, exist_ok=True)
    plt.savefig(os.path.join(out_dir, 'overall_performance.png'), dpi=400, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"✅ Created {os.path.join(out_dir, 'overall_performance.png')}")

def main():
    print("\n🎨 Generating GPT-5 judge plots...\n")
    evaluations = load_all_evaluations()
    if not evaluations:
        print("❌ No GPT-5 evaluations found in evaluations_gpt5/")
        return
    print(f"✅ Loaded {len(evaluations)} questions with evaluations\n")
    create_overall_performance_chart(evaluations)
    print("\n✅ All GPT-5 plots created successfully!\n")

if __name__ == "__main__":
    main()


