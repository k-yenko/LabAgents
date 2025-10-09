#!/usr/bin/env python3
"""
Weighted Performance Analysis Script
Creates weighted scoring where Tier 2 = 2 points, Tier 3 = 4 points
"""

import pandas as pd
import numpy as np

# Read the original performance table
df = pd.read_csv('model_performance_table.csv')

print("Weighted Model Performance Analysis")
print("=" * 50)
print("Tier 2 questions: 2 points each")
print("Tier 3 questions: 4 points each")
print()

# Define models
models = ['claude-4.1-opus', 'claude-4-sonnet', 'gpt-5', 'o3', 'grok-4', 
          'gemini-2.5-pro', 'deepseek-v3.1', 'grok-code-fast-1']

# Define question weights
question_weights = {
    'tier2_002': 2,
    'tier2_003': 2, 
    'tier2_004': 2,
    'tier2_005': 2,
    'tier2_007': 2,
    'tier3_001': 4,
    'tier3_002': 4,
    'tier3_003': 4,
    'tier3_004': 4,
    'tier3_005': 4
}

# Calculate weighted scores for each model
weighted_scores = {}
tier2_scores = {}
tier3_scores = {}

for model in models:
    total_weighted_score = 0
    tier2_weighted = 0
    tier3_weighted = 0
    
    for _, row in df.iterrows():
        question = row['question_id']
        correct = row[model]
        weight = question_weights[question]
        
        weighted_points = correct * weight
        total_weighted_score += weighted_points
        
        if question.startswith('tier2'):
            tier2_weighted += weighted_points
        else:
            tier3_weighted += weighted_points
    
    weighted_scores[model] = total_weighted_score
    tier2_scores[model] = tier2_weighted
    tier3_scores[model] = tier3_weighted

# Calculate maximum possible scores
max_tier2_score = 5 * 2  # 5 tier2 questions × 2 points each = 10
max_tier3_score = 5 * 4  # 5 tier3 questions × 4 points each = 20
max_total_score = max_tier2_score + max_tier3_score  # 30 points total

print("Maximum Possible Scores:")
print(f"Tier 2: {max_tier2_score} points (5 questions × 2 points)")
print(f"Tier 3: {max_tier3_score} points (5 questions × 4 points)")  
print(f"Total: {max_total_score} points")
print()

# Sort models by weighted performance
sorted_models = sorted(models, key=lambda x: weighted_scores[x], reverse=True)

print("Weighted Performance Rankings:")
print("-" * 65)
print(f"{'Rank':<4} {'Model':<20} {'Tier 2':<10} {'Tier 3':<10} {'Total':<8} {'%':<6}")
print("-" * 65)

for i, model in enumerate(sorted_models, 1):
    display_name = model.replace('claude-4.1-opus', 'Claude 4.1 Opus') \
                       .replace('claude-4-sonnet', 'Claude 4 Sonnet') \
                       .replace('gpt-5', 'GPT-5') \
                       .replace('o3', 'o3') \
                       .replace('grok-4', 'Grok-4') \
                       .replace('gemini-2.5-pro', 'Gemini 2.5 Pro') \
                       .replace('deepseek-v3.1', 'DeepSeek v3.1') \
                       .replace('grok-code-fast-1', 'Grok Code Fast-1')
    
    tier2_score = tier2_scores[model]
    tier3_score = tier3_scores[model] 
    total_score = weighted_scores[model]
    percentage = (total_score / max_total_score) * 100
    
    print(f"{i:<4} {display_name:<20} {tier2_score}/{max_tier2_score:<9} {tier3_score}/{max_tier3_score:<9} {total_score}/{max_total_score:<7} {percentage:5.1f}%")

print("-" * 65)
print()

# Create weighted performance table
weighted_data = []
for _, row in df.iterrows():
    question = row['question_id'] 
    weight = question_weights[question]
    
    weighted_row = {'question_id': question, 'weight': weight}
    
    for model in models:
        weighted_row[model] = row[model] * weight
    
    weighted_data.append(weighted_row)

weighted_df = pd.DataFrame(weighted_data)

# Save weighted table
weighted_df.to_csv('weighted_performance_table.csv', index=False)
print("Saved weighted_performance_table.csv")

# Analysis insights
print("\nKey Insights:")
print("=" * 30)

# Top performer
top_model = sorted_models[0]
top_score = weighted_scores[top_model]
top_pct = (top_score / max_total_score) * 100

print(f"🥇 Top Performer: {top_model.replace('-', ' ').title()} ({top_score}/{max_total_score} points, {top_pct:.1f}%)")

# Tier specialists
best_tier2 = max(models, key=lambda x: tier2_scores[x])
best_tier3 = max(models, key=lambda x: tier3_scores[x])

print(f"🥈 Best at Tier 2: {best_tier2.replace('-', ' ').title()} ({tier2_scores[best_tier2]}/{max_tier2_score} points)")
print(f"🥉 Best at Tier 3: {best_tier3.replace('-', ' ').title()} ({tier3_scores[best_tier3]}/{max_tier3_score} points)")

# Performance gaps
scores_list = list(weighted_scores.values())
performance_gap = max(scores_list) - min(scores_list)
print(f"📊 Performance Gap: {performance_gap} points between best and worst")

# Average performance
avg_score = np.mean(scores_list)
avg_pct = (avg_score / max_total_score) * 100
print(f"📈 Average Performance: {avg_score:.1f}/{max_total_score} points ({avg_pct:.1f}%)")

print()
print("Note: Weighted scoring emphasizes the higher difficulty of Tier 3 questions")
print("      which require more complex multi-step computational workflows.")