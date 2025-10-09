#!/usr/bin/env python3
"""
create_evaluation_plots.py - generates modern professional evaluation charts from LLM judge evaluations

reads from: evaluations/{question_id}/json/{model}_evaluation.json
generates: modern, professional charts for papers/presentations
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

# Modern professional color palette
MODEL_COLORS = {
    'anthropic/claude-opus-4.1': '#8B5CF6',      # vibrant purple
    'anthropic/claude-sonnet-4.5': '#A78BFA',    # lighter purple
    'anthropic/claude-sonnet-4': '#C4B5FD',      # light purple
    'openai/gpt-5': '#10B981',                   # emerald green
    'openai/o3': '#34D399',                      # light emerald
    'google/gemini-2.5-pro': '#F59E0B',          # amber
    'deepseek/deepseek-chat-v3.1:free': '#3B82F6', # blue
    'x-ai/grok-4-fast:free': '#EC4899',          # pink
    'x-ai/grok-code-fast-1': '#F472B6',          # light pink
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

def load_all_evaluations():
    """Load all evaluation results from evaluations/ directory"""
    evaluations = defaultdict(dict)

    # Find all evaluation JSON files
    eval_pattern = "evaluations/*/json/*_evaluation.json"
    eval_files = glob.glob(eval_pattern)

    for eval_file in eval_files:
        try:
            with open(eval_file, 'r') as f:
                data = json.load(f)

            question_id = data.get('question_id')

            # Extract model name from filename
            filename = Path(eval_file).stem
            model_name = filename.replace('_evaluation', '').replace('_', '/', 1)

            # Handle special cases for model name extraction
            if 'deepseek' in model_name:
                model_name = model_name.replace('_', ':', 1)  # Fix deepseek:free
            if 'grok' in model_name and 'free' in model_name:
                model_name = model_name.replace('_free', ':free')

            # Determine tier for weighting
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

def create_overall_performance_chart(evaluations):
    """Create main performance chart showing weighted score by model"""
    setup_modern_style()

    # Calculate weighted score for each model
    model_data = []

    for model_name in set(m for models in evaluations.values() for m in models.keys()):
        # Collect all evaluations for this model
        model_evals = []
        for question_id, models in evaluations.items():
            if model_name in models:
                model_evals.append(models[model_name])

        # Calculate weighted score
        weighted_score = calculate_weighted_score(model_evals)
        total_evals = len(model_evals)

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

    # Add percentage labels
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
    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/overall_performance.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"✅ Created plots/overall_performance.png")

def calculate_weighted_score(evaluations_list):
    """Calculate weighted score with tier1=1x, tier2=2x, tier3=4x"""
    tier_weights = {'tier1': 1.0, 'tier2': 2.0, 'tier3': 4.0}

    weighted_total = 0
    weight_sum = 0

    for eval_data in evaluations_list:
        tier = eval_data.get('tier', 'tier1')
        weight = tier_weights.get(tier, 1.0)
        score_normalized = eval_data['total_score'] / 6.0 * 100  # Convert to percentage

        weighted_total += score_normalized * weight
        weight_sum += weight

    return weighted_total / weight_sum if weight_sum > 0 else 0

def create_score_breakdown_chart(evaluations):
    """Create breakdown chart showing weighted scores for each model"""
    setup_modern_style()

    # Collect all evaluations per model with tier info
    model_data = defaultdict(list)

    for question_id, models in evaluations.items():
        for model_name, scores in models.items():
            model_data[model_name].append(scores)

    # Calculate weighted scores
    model_avg = []
    for model, evals in model_data.items():
        weighted_score = calculate_weighted_score(evals)

        # Also calculate average component scores for display
        avg_completion = np.mean([e['completion_score'] for e in evals])
        avg_correctness = np.mean([e['correctness_score'] for e in evals])
        avg_tool_use = np.mean([e['tool_use_score'] for e in evals])

        model_avg.append({
            'model': model,
            'weighted_score': weighted_score,
            'completion': avg_completion,
            'correctness': avg_correctness,
            'tool_use': avg_tool_use,
            'total': avg_completion + avg_correctness + avg_tool_use
        })

    # Sort by weighted score
    model_avg.sort(key=lambda x: x['weighted_score'], reverse=True)

    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(14, 8))

    models = [d['model'] for d in model_avg]
    completion = [d['completion'] for d in model_avg]
    correctness = [d['correctness'] for d in model_avg]
    tool_use = [d['tool_use'] for d in model_avg]

    y_pos = np.arange(len(models))

    ax.barh(y_pos, completion, label='Completion', color='#10B981', alpha=0.85)
    ax.barh(y_pos, correctness, left=completion, label='Correctness', color='#F59E0B', alpha=0.85)
    ax.barh(y_pos, tool_use, left=np.array(completion)+np.array(correctness),
            label='Tool Use', color='#8B5CF6', alpha=0.85)

    # Add weighted score labels
    for i, data in enumerate(model_avg):
        ax.text(data['total'] + 0.1, i, f"{data['weighted_score']:.1f}%",
                va='center', ha='left', fontweight='bold', fontsize=10)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(models)
    ax.set_xlabel('Average Score', fontsize=13, fontweight='600')
    ax.set_title('Score Breakdown by Evaluation Category (Ranked by Weighted Score)\nCompletion + Correctness + Tool Use',
                 fontsize=18, fontweight='bold', pad=20)
    ax.legend(loc='lower right', fontsize=11, framealpha=0.95)
    ax.set_xlim(0, 7)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig('plots/score_breakdown.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"✅ Created plots/score_breakdown.png")

def create_tier_performance_chart(evaluations):
    """Create chart showing performance by question tier"""
    setup_modern_style()

    # Organize by tier
    tier_stats = defaultdict(lambda: defaultdict(lambda: {'passed': 0, 'total': 0}))

    for question_id, models in evaluations.items():
        # Determine tier from question_id
        if question_id.startswith('tier1'):
            tier = 'Tier 1 (Basic)'
        elif question_id.startswith('tier2'):
            tier = 'Tier 2 (Intermediate)'
        elif question_id.startswith('tier3'):
            tier = 'Tier 3 (Advanced)'
        else:
            continue

        for model_name, scores in models.items():
            tier_stats[tier][model_name]['total'] += 1
            if scores['passed']:
                tier_stats[tier][model_name]['passed'] += 1

    # Get all unique models
    all_models = set()
    for tier_data in tier_stats.values():
        all_models.update(tier_data.keys())
    all_models = sorted(all_models)

    # Prepare data for grouped bar chart
    tiers = sorted(tier_stats.keys())

    fig, ax = plt.subplots(figsize=(16, 8))

    x = np.arange(len(all_models))
    width = 0.25

    for i, tier in enumerate(tiers):
        pass_rates = []
        for model in all_models:
            stats = tier_stats[tier].get(model, {'passed': 0, 'total': 0})
            pass_rate = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            pass_rates.append(pass_rate)

        offset = width * (i - 1)
        bars = ax.bar(x + offset, pass_rates, width, label=tier, alpha=0.85)

    ax.set_ylabel('Pass Rate (%)', fontsize=13, fontweight='600')
    ax.set_title('Model Performance by Question Tier',
                 fontsize=18, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(all_models, rotation=45, ha='right')
    ax.legend(fontsize=11, framealpha=0.95)
    ax.set_ylim(0, 110)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig('plots/tier_performance.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"✅ Created plots/tier_performance.png")

def create_heatmap(evaluations):
    """Create heatmap showing pass/fail for each model-question combination"""
    setup_modern_style()

    # Get all unique models and questions
    all_models = set()
    all_questions = set()
    for question_id, models in evaluations.items():
        all_questions.add(question_id)
        all_models.update(models.keys())

    all_models = sorted(all_models)
    all_questions = sorted(all_questions)

    # Create matrix
    matrix = np.zeros((len(all_questions), len(all_models)))

    for i, question in enumerate(all_questions):
        for j, model in enumerate(all_models):
            if model in evaluations.get(question, {}):
                # 1 for pass, 0 for fail
                matrix[i][j] = 1 if evaluations[question][model]['passed'] else 0
            else:
                matrix[i][j] = np.nan  # No data

    # Create heatmap
    fig, ax = plt.subplots(figsize=(16, 12))

    cmap = sns.color_palette(["#EF4444", "#10B981"], as_cmap=True)
    sns.heatmap(matrix, annot=False, cmap=cmap, cbar_kws={'label': 'Pass/Fail'},
                xticklabels=all_models, yticklabels=all_questions,
                linewidths=0.5, linecolor='white', ax=ax,
                vmin=0, vmax=1)

    ax.set_title('Model Performance Heatmap\nGreen = Pass, Red = Fail',
                 fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel('Model', fontsize=13, fontweight='600')
    ax.set_ylabel('Question ID', fontsize=13, fontweight='600')

    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig('plots/performance_heatmap.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"✅ Created plots/performance_heatmap.png")

def create_summary_stats(evaluations):
    """Create summary statistics file"""
    model_stats = defaultdict(lambda: {
        'total_questions': 0,
        'passed': 0,
        'failed': 0,
        'avg_total_score': [],
        'avg_completion': [],
        'avg_correctness': [],
        'avg_tool_use': []
    })

    for question_id, models in evaluations.items():
        for model_name, scores in models.items():
            stats = model_stats[model_name]
            stats['total_questions'] += 1
            if scores['passed']:
                stats['passed'] += 1
            else:
                stats['failed'] += 1
            stats['avg_total_score'].append(scores['total_score'])
            stats['avg_completion'].append(scores['completion_score'])
            stats['avg_correctness'].append(scores['correctness_score'])
            stats['avg_tool_use'].append(scores['tool_use_score'])

    # Write summary
    with open('plots/summary_statistics.txt', 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("EVALUATION SUMMARY STATISTICS\n")
        f.write("=" * 80 + "\n\n")

        for model in sorted(model_stats.keys()):
            stats = model_stats[model]
            pass_rate = (stats['passed'] / stats['total_questions']) * 100

            f.write(f"\n{model}\n")
            f.write("-" * 80 + "\n")
            f.write(f"  Total Questions: {stats['total_questions']}\n")
            f.write(f"  Passed: {stats['passed']} ({pass_rate:.1f}%)\n")
            f.write(f"  Failed: {stats['failed']} ({100-pass_rate:.1f}%)\n")
            f.write(f"  Avg Total Score: {np.mean(stats['avg_total_score']):.2f}/6\n")
            f.write(f"  Avg Completion: {np.mean(stats['avg_completion']):.2f}/2\n")
            f.write(f"  Avg Correctness: {np.mean(stats['avg_correctness']):.2f}/2\n")
            f.write(f"  Avg Tool Use: {np.mean(stats['avg_tool_use']):.2f}/2\n")

    print(f"✅ Created plots/summary_statistics.txt")

def main():
    """Generate all evaluation plots"""
    print("\n🎨 Generating modern evaluation plots...\n")

    # Load all evaluations
    print("📊 Loading evaluation data...")
    evaluations = load_all_evaluations()

    if not evaluations:
        print("❌ No evaluations found in evaluations/ directory")
        return

    print(f"✅ Loaded {len(evaluations)} questions with evaluations\n")

    # Create all plots
    print("📈 Creating visualizations...\n")
    create_overall_performance_chart(evaluations)
    create_score_breakdown_chart(evaluations)
    create_tier_performance_chart(evaluations)
    create_heatmap(evaluations)
    create_summary_stats(evaluations)

    print("\n✅ All plots created successfully in plots/ directory!")

if __name__ == "__main__":
    main()
