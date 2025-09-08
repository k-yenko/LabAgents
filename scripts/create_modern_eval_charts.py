#!/usr/bin/env python3
"""
Create modern evaluation charts with consistent styling
"""

import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Professional muted color palette for social media - assigned by model
MODEL_COLORS = {
    'gpt-5': '#4A90A4',           # muted steel blue
    'claude-4-sonnet': '#7B68A6', # muted purple
    'claude-4.1-opus': '#A0786A', # muted brown
    'o3': '#8B9DC3',              # muted lavender
    'grok-4': '#6B8E5A',          # muted olive green
    'grok-code-fast-1': '#B08B8B', # muted rose
    'gemini-2.5-pro': '#8FA0A0',  # muted gray-blue
    'deepseek-v3.1': '#9A8B6B',   # muted tan
}

def setup_modern_style():
    """Setup modern chart styling"""
    plt.style.use('default')
    
    # Set modern font and styling
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans'],
        'font.size': 11,
        'axes.titlesize': 16,
        'axes.titleweight': 'bold',
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.spines.left': True,
        'axes.spines.bottom': True,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.linewidth': 0.5,
    })

def load_correctness_scores():
    """Load correctness scores from all question folders"""
    all_scores = {}
    
    # All question folders (excluding tier2_006 and tier3_006)
    folders = ['questions/tier2_002', 'questions/tier2_003', 'questions/tier2_004', 'questions/tier2_005', 'questions/tier2_007',
               'questions/tier3_001', 'questions/tier3_002', 'questions/tier3_003', 'questions/tier3_004', 'questions/tier3_005']
    
    for folder in folders:
        score_file = f"{folder}/score.json"
        if os.path.exists(score_file):
            with open(score_file, 'r') as f:
                data = json.load(f)
                
            # Extract the correctness scores
            for key, scores in data.items():
                if key.endswith('_scores'):
                    question_id = key.replace('_scores', '')
                    all_scores[question_id] = scores
    
    return all_scores

def load_tool_selection_scores():
    """Load tool selection scores from all question folders"""
    all_scores = {}
    
    # All question folders (excluding tier2_006 and tier3_006)
    folders = ['questions/tier2_002', 'questions/tier2_003', 'questions/tier2_004', 'questions/tier2_005', 'questions/tier2_007',
               'questions/tier3_001', 'questions/tier3_002', 'questions/tier3_003', 'questions/tier3_004', 'questions/tier3_005']
    
    for folder in folders:
        score_file = f"{folder}/tool_selection_scores.json"
        if os.path.exists(score_file):
            with open(score_file, 'r') as f:
                data = json.load(f)
                
            # Extract the tool selection scores
            for key, scores in data.items():
                if key.endswith('_tool_selection'):
                    question_id = key.replace('_tool_selection', '')
                    all_scores[question_id] = scores
    
    return all_scores

def create_modern_correctness_chart():
    """Create modern correctness evaluation chart"""
    setup_modern_style()
    
    scores_data = load_correctness_scores()
    
    if not scores_data:
        print("No correctness scores found")
        return {}
    
    # Initialize model scores
    model_scores = {}
    
    # Process each question's scores
    for question_id, question_scores in scores_data.items():
        for model, score_data in question_scores.items():
            if model not in model_scores:
                model_scores[model] = 0
            # Count correct answers (1 for correct, 0 for incorrect)
            model_scores[model] += 1 if score_data.get('correct', False) else 0
    
    # Sort models by score (descending) - best on top
    sorted_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)
    models = [item[0] for item in sorted_models]
    scores = [item[1] for item in sorted_models]
    
    # Reverse for horizontal bar chart so best is on top
    models.reverse()
    scores.reverse()
    
    # Create the chart
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Use model-specific colors
    colors = [MODEL_COLORS.get(model, '#95A5A6') for model in models]
    bars = ax.barh(models, scores, color=colors)
    
    # Add score labels on bars
    total_questions = len(scores_data)
    for i, (bar, score) in enumerate(zip(bars, scores)):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                f'{score}/{total_questions}', 
                va='center', ha='left', fontweight='bold', fontsize=11)
    
    ax.set_xlabel('Correctness Score (Number of Questions Passed)', fontsize=12)
    ax.set_title('Correctness Evaluation - AI Models', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim(0, total_questions + 1)
    
    plt.tight_layout()
    plt.savefig('figures/correctness_eval.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Created figures/correctness_eval.png")
    return model_scores

def create_modern_correctness_grouped_chart():
    """Create modern grouped correctness chart by tier"""
    setup_modern_style()
    
    scores_data = load_correctness_scores()
    
    if not scores_data:
        print("No correctness scores found")
        return
    
    # Initialize model scores by tier
    tier2_scores = {}
    tier3_scores = {}
    
    # Process each question's scores
    for question_id, question_scores in scores_data.items():
        is_tier3 = question_id.startswith('tier3')
        
        for model, score_data in question_scores.items():
            score = 1 if score_data.get('correct', False) else 0
            
            if is_tier3:
                if model not in tier3_scores:
                    tier3_scores[model] = 0
                tier3_scores[model] += score
            else:
                if model not in tier2_scores:
                    tier2_scores[model] = 0
                tier2_scores[model] += score
    
    # Get all models and sort by total score
    all_models = set(tier2_scores.keys()) | set(tier3_scores.keys())
    total_scores = {}
    for model in all_models:
        total_scores[model] = tier2_scores.get(model, 0) + tier3_scores.get(model, 0)
    
    sorted_models = sorted(total_scores.items(), key=lambda x: x[1], reverse=True)
    models = [item[0] for item in sorted_models]
    models.reverse()  # Best on top
    
    # Prepare data
    tier2_values = [tier2_scores.get(model, 0) for model in models]
    tier3_values = [tier3_scores.get(model, 0) for model in models]
    
    # Create the chart
    fig, ax = plt.subplots(figsize=(12, 8))
    
    y_pos = np.arange(len(models))
    bar_height = 0.35
    
    # Count questions by tier
    tier2_count = len([q for q in scores_data.keys() if q.startswith('tier2')])
    tier3_count = len([q for q in scores_data.keys() if q.startswith('tier3')])
    
    bars1 = ax.barh(y_pos - bar_height/2, tier2_values, bar_height, 
                    label=f'Tier 2 (max {tier2_count})', color='#3498DB')
    bars2 = ax.barh(y_pos + bar_height/2, tier3_values, bar_height, 
                    label=f'Tier 3 (max {tier3_count})', color='#E74C3C')
    
    # Add value labels
    for i, value in enumerate(tier2_values):
        if value > 0:
            ax.text(value + 0.05, i - bar_height/2, str(value), 
                    va='center', ha='left', fontweight='bold', fontsize=10)
    
    for i, value in enumerate(tier3_values):
        if value > 0:
            ax.text(value + 0.05, i + bar_height/2, str(value), 
                    va='center', ha='left', fontweight='bold', fontsize=10)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(models)
    ax.set_xlabel('Number of Questions Passed', fontsize=12)
    ax.set_title('Correctness Evaluation by Tier', fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='lower right', fontsize=11)
    
    max_val = max(max(tier2_values + tier3_values, default=0), tier2_count, tier3_count)
    ax.set_xlim(0, max_val + 1)
    
    plt.tight_layout()
    plt.savefig('figures/correctness_grouped_eval.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Created figures/correctness_grouped_eval.png")

def create_modern_tool_selection_chart():
    """Create modern tool selection chart"""
    setup_modern_style()
    
    scores_data = load_tool_selection_scores()
    
    if not scores_data:
        print("No tool selection scores found")
        return {}
    
    # Initialize model scores
    model_scores = {}
    
    # Process each question's scores
    for question_id, question_scores in scores_data.items():
        for model, score_data in question_scores.items():
            if model not in model_scores:
                model_scores[model] = 0
            model_scores[model] += score_data.get('tool_selection_score', 0)
    
    # Sort models by score (descending) - best on top
    sorted_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)
    models = [item[0] for item in sorted_models]
    scores = [item[1] for item in sorted_models]
    
    # Reverse for horizontal bar chart so best is on top
    models.reverse()
    scores.reverse()
    
    # Create the chart
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Use model-specific colors
    colors = [MODEL_COLORS.get(model, '#95A5A6') for model in models]
    bars = ax.barh(models, scores, color=colors)
    
    # Add score labels on bars
    total_questions = len(scores_data)
    for i, (bar, score) in enumerate(zip(bars, scores)):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                f'{score}/{total_questions}', 
                va='center', ha='left', fontweight='bold', fontsize=11)
    
    ax.set_xlabel('Questions with Complete Expected Tool Usage', fontsize=12)
    ax.set_title('Function Calling Evaluation on Agentic Tool-Use\nfor Computational Chemistry Tasks', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim(0, total_questions + 1)
    
    plt.tight_layout()
    plt.savefig('figures/tool_selection_eval.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Created figures/tool_selection_eval.png")
    return model_scores

def create_modern_tool_selection_grouped_chart():
    """Create modern grouped tool selection chart by tier"""
    setup_modern_style()
    
    scores_data = load_tool_selection_scores()
    
    if not scores_data:
        print("No tool selection scores found")
        return
    
    # Initialize model scores by tier
    tier2_scores = {}
    tier3_scores = {}
    
    # Process each question's scores
    for question_id, question_scores in scores_data.items():
        is_tier3 = question_id.startswith('tier3')
        
        for model, score_data in question_scores.items():
            score = score_data.get('tool_selection_score', 0)
            
            if is_tier3:
                if model not in tier3_scores:
                    tier3_scores[model] = 0
                tier3_scores[model] += score
            else:
                if model not in tier2_scores:
                    tier2_scores[model] = 0
                tier2_scores[model] += score
    
    # Get all models and sort by total score
    all_models = set(tier2_scores.keys()) | set(tier3_scores.keys())
    total_scores = {}
    for model in all_models:
        total_scores[model] = tier2_scores.get(model, 0) + tier3_scores.get(model, 0)
    
    sorted_models = sorted(total_scores.items(), key=lambda x: x[1], reverse=True)
    models = [item[0] for item in sorted_models]
    models.reverse()  # Best on top
    
    # Prepare data
    tier2_values = [tier2_scores.get(model, 0) for model in models]
    tier3_values = [tier3_scores.get(model, 0) for model in models]
    
    # Create the chart
    fig, ax = plt.subplots(figsize=(12, 8))
    
    y_pos = np.arange(len(models))
    bar_height = 0.35
    
    # Count questions by tier
    tier2_count = len([q for q in scores_data.keys() if q.startswith('tier2')])
    tier3_count = len([q for q in scores_data.keys() if q.startswith('tier3')])
    
    bars1 = ax.barh(y_pos - bar_height/2, tier2_values, bar_height, 
                    label=f'Tier 2 (max {tier2_count})', color='#3498DB')
    bars2 = ax.barh(y_pos + bar_height/2, tier3_values, bar_height, 
                    label=f'Tier 3 (max {tier3_count})', color='#E74C3C')
    
    # Add value labels
    for i, value in enumerate(tier2_values):
        if value > 0:
            ax.text(value + 0.05, i - bar_height/2, str(value), 
                    va='center', ha='left', fontweight='bold', fontsize=10)
    
    for i, value in enumerate(tier3_values):
        if value > 0:
            ax.text(value + 0.05, i + bar_height/2, str(value), 
                    va='center', ha='left', fontweight='bold', fontsize=10)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(models)
    ax.set_xlabel('Number of Questions Passed', fontsize=12)
    ax.set_title('Tool Selection Evaluation by Tier', fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='lower right', fontsize=11)
    
    max_val = max(max(tier2_values + tier3_values, default=0), tier2_count, tier3_count)
    ax.set_xlim(0, max_val + 1)
    
    plt.tight_layout()
    plt.savefig('figures/tool_selection_grouped_eval.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Created figures/tool_selection_grouped_eval.png")

def create_weighted_performance_chart():
    """Create weighted performance chart (combining both correctness and complexity weighting)"""
    setup_modern_style()
    
    # Load data from the weighted performance table
    weighted_file = 'data/weighted_performance_table.csv'
    if not os.path.exists(weighted_file):
        print("No weighted performance data found")
        return
    
    import csv
    model_scores = {}
    
    with open(weighted_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            question_id = row['question_id']
            weight = int(row['weight'])
            
            # Skip tier2_006 and tier3_006
            if question_id in ['tier2_006', 'tier3_006']:
                continue
            
            for model in reader.fieldnames[2:]:  # Skip question_id and weight columns
                if model not in model_scores:
                    model_scores[model] = 0
                model_scores[model] += int(row[model])
    
    # Sort models by score (descending) - best on top
    sorted_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)
    models = [item[0] for item in sorted_models]
    scores = [item[1] for item in sorted_models]
    
    # Reverse for horizontal bar chart so best is on top
    models.reverse()
    scores.reverse()
    
    # Create the chart
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Use model-specific colors
    colors = [MODEL_COLORS.get(model, '#95A5A6') for model in models]
    bars = ax.barh(models, scores, color=colors)
    
    # Calculate max possible score (excluding tier2_006 and tier3_006)
    max_score = 5 * 2 + 5 * 4  # 5 tier2 questions * 2 points + 5 tier3 questions * 4 points = 30
    
    # Add score labels on bars
    for i, (bar, score) in enumerate(zip(bars, scores)):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2, 
                f'{score}/{max_score}', 
                va='center', ha='left', fontweight='bold', fontsize=11)
    
    ax.set_xlabel('Weighted Score (Max 30)', fontsize=12)
    ax.set_title('Correctness Evaluation on Multi-Step\nComputational Chemistry Tasks Requiring Agentic Tool-Use', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim(0, max_score + 2)
    
    plt.tight_layout()
    plt.savefig('figures/weighted_performance_eval.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Created figures/weighted_performance_eval.png")

def create_agentic_performance_chart():
    """Create agentic performance chart (simple correctness count)"""
    setup_modern_style()
    
    scores_data = load_correctness_scores()
    
    if not scores_data:
        print("No correctness scores found")
        return
    
    # Initialize model scores
    model_scores = {}
    
    # Process each question's scores
    for question_id, question_scores in scores_data.items():
        for model, score_data in question_scores.items():
            if model not in model_scores:
                model_scores[model] = 0
            model_scores[model] += 1 if score_data.get('correct', False) else 0
    
    # Sort models by score (descending) - best on top
    sorted_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)
    models = [item[0] for item in sorted_models]
    scores = [item[1] for item in sorted_models]
    
    # Reverse for horizontal bar chart so best is on top
    models.reverse()
    scores.reverse()
    
    # Create the chart
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Use model-specific colors
    colors = [MODEL_COLORS.get(model, '#95A5A6') for model in models]
    bars = ax.barh(models, scores, color=colors)
    
    # Add score labels on bars
    total_questions = len(scores_data)
    for i, (bar, score) in enumerate(zip(bars, scores)):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                f'{score}/{total_questions}', 
                va='center', ha='left', fontweight='bold', fontsize=11)
    
    ax.set_xlabel('Success rate on multi-step computational chemistry tasks requiring tool use and domain expertise', 
                 fontsize=11, color='#666666')
    ax.set_title('Agentic AI Model Performance\nComputational Chemistry Benchmarks', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim(0, total_questions + 1)
    
    plt.tight_layout()
    plt.savefig('figures/agentic_performance_eval.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Created figures/agentic_performance_eval.png")

if __name__ == "__main__":
    print("Creating modern evaluation charts...")
    
    # Create all modern charts with consistent styling
    create_modern_correctness_chart()
    create_modern_correctness_grouped_chart()
    create_modern_tool_selection_chart() 
    create_modern_tool_selection_grouped_chart()
    create_weighted_performance_chart()
    create_agentic_performance_chart()
    
    print("Modern evaluation charts created successfully!")