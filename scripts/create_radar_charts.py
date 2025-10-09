#!/usr/bin/env python3
"""
create_radar_charts.py - creates radar charts comparing models across key dimensions
"""

import json
import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from pathlib import Path

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

def normalize_model_name(filename):
    """Extract and normalize model name from filename"""
    name = filename.replace('_evaluation', '')
    parts = name.split('_', 1)
    if len(parts) == 2:
        model_name = parts[0] + '/' + parts[1]
    else:
        model_name = name
    model_name = model_name.replace(':free', '').replace('_free', '')
    return model_name

def load_evaluations(eval_dir):
    """Load all evaluations from directory"""
    evaluations = defaultdict(lambda: defaultdict(list))

    eval_files = glob.glob(f"{eval_dir}/*/json/*_evaluation.json")

    for eval_file in eval_files:
        try:
            with open(eval_file) as f:
                data = json.load(f)

            question_id = data.get('question_id')
            filename = Path(eval_file).stem
            model_name = normalize_model_name(filename)

            tier = question_id.split('_')[0] if '_' in question_id else 'tier1'

            evaluations[model_name][tier].append({
                'completion_score': data.get('completion_score', 0),
                'correctness_score': data.get('correctness_score', 0),
                'tool_use_score': data.get('tool_use_score', 0),
                'total_score': data.get('total_score', 0),
            })
        except Exception as e:
            pass

    return evaluations

def calculate_radar_metrics(evaluations):
    """
    Calculate radar chart metrics for each model:
    1. Tier 1 Performance (basic tool selection)
    2. Tier 2 Performance (multi-tool orchestration)
    3. Tier 3 Performance (complex reasoning)
    4. Completion Score (task completion)
    5. Correctness Score (answer accuracy)
    6. Tool Use Score (proper tool usage)
    """
    metrics = {}

    for model, tier_data in evaluations.items():
        # Calculate tier-specific performance (normalized to 0-100)
        tier1_scores = [e['total_score'] / 6.0 * 100 for e in tier_data.get('tier1', [])]
        tier2_scores = [e['total_score'] / 6.0 * 100 for e in tier_data.get('tier2', [])]
        tier3_scores = [e['total_score'] / 6.0 * 100 for e in tier_data.get('tier3', [])]

        # Calculate dimension-specific scores across all tiers
        all_evals = []
        for tier in ['tier1', 'tier2', 'tier3']:
            all_evals.extend(tier_data.get(tier, []))

        completion_scores = [e['completion_score'] / 2.0 * 100 for e in all_evals]
        correctness_scores = [e['correctness_score'] / 2.0 * 100 for e in all_evals]
        tool_use_scores = [e['tool_use_score'] / 2.0 * 100 for e in all_evals]

        metrics[model] = {
            'Tier 1\n(Basic)': np.mean(tier1_scores) if tier1_scores else 0,
            'Tier 2\n(Multi-tool)': np.mean(tier2_scores) if tier2_scores else 0,
            'Tier 3\n(Complex)': np.mean(tier3_scores) if tier3_scores else 0,
            'Completion': np.mean(completion_scores) if completion_scores else 0,
            'Correctness': np.mean(correctness_scores) if correctness_scores else 0,
            'Tool Use': np.mean(tool_use_scores) if tool_use_scores else 0,
        }

    return metrics

def create_radar_chart(metrics, output_path, title_suffix=""):
    """Create radar chart for top 5 models"""
    # Get top 5 models by average performance
    model_avg = {m: np.mean(list(vals.values())) for m, vals in metrics.items()}
    top_models = sorted(model_avg.items(), key=lambda x: x[1], reverse=True)[:5]
    top_model_names = [m[0] for m in top_models]

    # Dimensions
    categories = list(next(iter(metrics.values())).keys())
    num_vars = len(categories)

    # Compute angle for each axis
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # Complete the circle

    # Initialize plot
    fig, ax = plt.subplots(figsize=(12, 10), subplot_kw=dict(projection='polar'))

    # Plot each model
    for model_name in top_model_names:
        values = [metrics[model_name][cat] for cat in categories]
        values += values[:1]  # Complete the circle

        color = MODEL_COLORS.get(model_name, '#6B7280')
        model_display = model_name.split('/')[-1]

        ax.plot(angles, values, 'o-', linewidth=2, label=model_display, color=color)
        ax.fill(angles, values, alpha=0.15, color=color)

    # Fix axis to go in the right order and start at 12 o'clock
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # Draw axis lines for each angle and label
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=11, weight='bold')

    # Set y-axis limits
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], size=9)

    # Add grid
    ax.grid(True, linestyle='--', alpha=0.7)

    # Add legend
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)

    # Add title
    plt.title(f'Model Performance Radar Chart{title_suffix}\nTop 5 Models Across Key Dimensions',
              size=16, weight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"✅ Created {output_path}")

def main():
    print("🎨 Generating radar charts...")

    # Load evaluations from both judges
    print("📊 Loading Claude Sonnet 4 judge evaluations...")
    claude_evals = load_evaluations("/Users/katherineyenko/Desktop/sandbox/labagents/evaluations")
    print(f"   Loaded {len(claude_evals)} models")

    print("📊 Loading Qwen judge evaluations...")
    qwen_evals = load_evaluations("/Users/katherineyenko/Desktop/sandbox/labagents/evaluations_qwen")
    print(f"   Loaded {len(qwen_evals)} models")

    # Calculate metrics
    print("📈 Calculating radar metrics...")
    claude_metrics = calculate_radar_metrics(claude_evals)
    qwen_metrics = calculate_radar_metrics(qwen_evals)

    # Create radar charts
    print("🎨 Creating radar charts...")
    create_radar_chart(
        claude_metrics,
        "/Users/katherineyenko/Desktop/sandbox/labagents/plots/radar_chart_claude_judge.png",
        " (Claude Sonnet 4 Judge)"
    )

    create_radar_chart(
        qwen_metrics,
        "/Users/katherineyenko/Desktop/sandbox/labagents/plots_qwen/radar_chart_qwen_judge.png",
        " (Qwen Judge)"
    )

    print("\n✅ All radar charts created!")

if __name__ == "__main__":
    main()
