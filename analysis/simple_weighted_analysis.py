#!/usr/bin/env python3
"""
Simple Weighted Performance Analysis (no pandas dependency)
"""

import csv

# Read the CSV data manually
with open('model_performance_table.csv', 'r') as f:
    reader = csv.DictReader(f)
    data = list(reader)

models = ['claude-4.1-opus', 'claude-4-sonnet', 'gpt-5', 'o3', 'grok-4', 
          'gemini-2.5-pro', 'deepseek-v3.1', 'grok-code-fast-1']

# Define weights
weights = {
    'tier2_002': 2, 'tier2_003': 2, 'tier2_004': 2, 'tier2_005': 2, 'tier2_007': 2,
    'tier3_001': 4, 'tier3_002': 4, 'tier3_003': 4, 'tier3_004': 4, 'tier3_005': 4
}

print("Weighted Performance Analysis")
print("=" * 50)
print("Tier 2 questions: 2 points each (10 points max)")
print("Tier 3 questions: 4 points each (20 points max)")
print("Total possible: 30 points")
print()

# Calculate weighted scores
results = {}
for model in models:
    total_score = 0
    tier2_score = 0
    tier3_score = 0
    
    for row in data:
        question = row['question_id']
        correct = int(row[model])
        weight = weights[question]
        points = correct * weight
        
        total_score += points
        if question.startswith('tier2'):
            tier2_score += points
        else:
            tier3_score += points
    
    results[model] = {
        'total': total_score,
        'tier2': tier2_score, 
        'tier3': tier3_score
    }

# Sort by total score
sorted_models = sorted(models, key=lambda x: results[x]['total'], reverse=True)

print("Rankings (Weighted Scores):")
print("-" * 70)
print(f"{'Rank':<4} {'Model':<20} {'Tier 2':<10} {'Tier 3':<10} {'Total':<8} {'%':<6}")
print("-" * 70)

for i, model in enumerate(sorted_models, 1):
    # Clean model names
    display_name = model.replace('claude-4.1-opus', 'Claude 4.1 Opus') \
                       .replace('claude-4-sonnet', 'Claude 4 Sonnet') \
                       .replace('gpt-5', 'GPT-5') \
                       .replace('o3', 'o3') \
                       .replace('grok-4', 'Grok-4') \
                       .replace('gemini-2.5-pro', 'Gemini 2.5 Pro') \
                       .replace('deepseek-v3.1', 'DeepSeek v3.1') \
                       .replace('grok-code-fast-1', 'Grok Code Fast-1')
    
    tier2 = results[model]['tier2']
    tier3 = results[model]['tier3']
    total = results[model]['total']
    percentage = (total / 30) * 100
    
    print(f"{i:<4} {display_name:<20} {tier2}/10     {tier3}/20     {total}/30   {percentage:5.1f}%")

print("-" * 70)

# Create weighted CSV
print("\nCreating weighted performance table...")

# Write weighted CSV
with open('weighted_performance_table.csv', 'w', newline='') as f:
    fieldnames = ['question_id', 'weight'] + models
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    
    for row in data:
        question = row['question_id']
        weight = weights[question]
        
        weighted_row = {'question_id': question, 'weight': weight}
        for model in models:
            weighted_row[model] = int(row[model]) * weight
        
        writer.writerow(weighted_row)

print("✅ Saved: weighted_performance_table.csv")

# Key insights
top_model = sorted_models[0]
top_score = results[top_model]['total']

print(f"\n🏆 Top Performer: {top_model.replace('-', ' ').title()}")
print(f"   Score: {top_score}/30 points ({(top_score/30)*100:.1f}%)")

# Compare unweighted vs weighted rankings
unweighted_scores = {}
for model in models:
    unweighted_total = 0
    for row in data:
        unweighted_total += int(row[model])
    unweighted_scores[model] = unweighted_total

unweighted_sorted = sorted(models, key=lambda x: unweighted_scores[x], reverse=True)

print(f"\n📊 Ranking Changes (Unweighted → Weighted):")
for model in models:
    old_rank = unweighted_sorted.index(model) + 1
    new_rank = sorted_models.index(model) + 1
    change = old_rank - new_rank
    
    display_name = model.replace('-', ' ').replace('_', ' ').title()
    if change > 0:
        print(f"   {display_name}: #{old_rank} → #{new_rank} (+{change})")
    elif change < 0:
        print(f"   {display_name}: #{old_rank} → #{new_rank} ({change})")
    else:
        print(f"   {display_name}: #{old_rank} → #{new_rank} (no change)")

print("\nWeighted scoring emphasizes Tier 3 performance due to higher complexity.")