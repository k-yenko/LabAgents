#!/usr/bin/env python3
"""
Create performance summary from the CSV table
"""

import pandas as pd

# Read the performance table
df = pd.read_csv('model_performance_table.csv')

# Calculate totals
models = ['claude-4.1-opus', 'claude-4-sonnet', 'gpt-5', 'o3', 'grok-4', 
          'gemini-2.5-pro', 'deepseek-v3.1', 'grok-code-fast-1']

print("Agentic AI Model Performance on Computational Chemistry Benchmarks")
print("=" * 75)

# Overall performance
print("\n1. Overall Performance on Multi-Step Computational Chemistry Tasks:")
print("   (N=10 questions spanning molecular property prediction, conformational analysis,")
print("    and protein-ligand interaction studies)")
print()
for model in models:
    total = df[model].sum()
    display_name = model.replace('claude-4.1-opus', 'Claude 4.1 Opus') \
                       .replace('claude-4-sonnet', 'Claude 4 Sonnet') \
                       .replace('gpt-5', 'GPT-5') \
                       .replace('o3', 'o3') \
                       .replace('grok-4', 'Grok-4') \
                       .replace('gemini-2.5-pro', 'Gemini 2.5 Pro') \
                       .replace('deepseek-v3.1', 'DeepSeek v3.1') \
                       .replace('grok-code-fast-1', 'Grok Code Fast-1')
    print(f"   {display_name:18} {total:2d}/10 ({total*10:3.0f}%)")

# Tier 2 performance (excluding tier2_006)
tier2_questions = ['tier2_002', 'tier2_003', 'tier2_004', 'tier2_005', 'tier2_007']
tier2_df = df[df['question_id'].isin(tier2_questions)]

print(f"\n2. Tier 2 Performance - Intermediate Complexity Tasks:")
print(f"   (N={len(tier2_questions)} questions: molecular descriptors, conformer analysis, pKa prediction)")
print()
for model in models:
    total = tier2_df[model].sum()
    display_name = model.replace('claude-4.1-opus', 'Claude 4.1 Opus') \
                       .replace('claude-4-sonnet', 'Claude 4 Sonnet') \
                       .replace('gpt-5', 'GPT-5') \
                       .replace('o3', 'o3') \
                       .replace('grok-4', 'Grok-4') \
                       .replace('gemini-2.5-pro', 'Gemini 2.5 Pro') \
                       .replace('deepseek-v3.1', 'DeepSeek v3.1') \
                       .replace('grok-code-fast-1', 'Grok Code Fast-1')
    print(f"   {display_name:18} {total:2d}/{len(tier2_questions)} ({total/len(tier2_questions)*100:3.0f}%)")

# Tier 3 performance (excluding tier3_006)
tier3_questions = ['tier3_001', 'tier3_002', 'tier3_003', 'tier3_004', 'tier3_005']
tier3_df = df[df['question_id'].isin(tier3_questions)]

print(f"\n3. Tier 3 Performance - Advanced Multi-Step Workflows:")
print(f"   (N={len(tier3_questions)} questions: tautomer analysis, ADMET prediction, molecular docking)")
print()
for model in models:
    total = tier3_df[model].sum()
    display_name = model.replace('claude-4.1-opus', 'Claude 4.1 Opus') \
                       .replace('claude-4-sonnet', 'Claude 4 Sonnet') \
                       .replace('gpt-5', 'GPT-5') \
                       .replace('o3', 'o3') \
                       .replace('grok-4', 'Grok-4') \
                       .replace('gemini-2.5-pro', 'Gemini 2.5 Pro') \
                       .replace('deepseek-v3.1', 'DeepSeek v3.1') \
                       .replace('grok-code-fast-1', 'Grok Code Fast-1')
    print(f"   {display_name:18} {total:2d}/{len(tier3_questions)} ({total/len(tier3_questions)*100:3.0f}%)")

# Question difficulty analysis
print("\n4. Task Difficulty Analysis (Cross-Model Success Rates):")
print("   Proportion of models successfully completing each task:")
print()

# Group by tier for better organization
tier2_rows = df[df['question_id'].str.startswith('tier2')].sort_values('question_id')
tier3_rows = df[df['question_id'].str.startswith('tier3')].sort_values('question_id')

print("   Tier 2 Tasks:")
for _, row in tier2_rows.iterrows():
    question = row['question_id']
    success_count = row[models].sum()
    success_rate = success_count / len(models)
    print(f"   {question:12} {success_count:2d}/8 models ({success_rate*100:3.0f}%)")

print("\n   Tier 3 Tasks:")
for _, row in tier3_rows.iterrows():
    question = row['question_id']
    success_count = row[models].sum()
    success_rate = success_count / len(models)
    print(f"   {question:12} {success_count:2d}/8 models ({success_rate*100:3.0f}%)")

# Create a formatted table for easy copying
print("\n" + "="*90)
print("TABLE 1. Agentic AI Model Performance on Computational Chemistry Benchmarks")
print("="*90)
print()
print("Performance evaluation of large language models with agentic capabilities")
print("on multi-step computational chemistry tasks requiring tool use and domain expertise.")
print()

print(f"{'Model':<20} {'Tier 2':<12} {'Tier 3':<12} {'Overall':<12} {'Success Rate'}")
print(f"{'':20} {'(N=5)':<12} {'(N=5)':<12} {'(N=10)':<12}")
print("-" * 75)

for model in models:
    tier2_score = tier2_df[model].sum()
    tier3_score = tier3_df[model].sum()
    total_score = df[model].sum()
    success_rate = total_score / 10 * 100
    
    # Clean up model name for display
    display_name = model.replace('claude-4.1-opus', 'Claude 4.1 Opus') \
                       .replace('claude-4-sonnet', 'Claude 4 Sonnet') \
                       .replace('gpt-5', 'GPT-5') \
                       .replace('o3', 'o3') \
                       .replace('grok-4', 'Grok-4') \
                       .replace('gemini-2.5-pro', 'Gemini 2.5 Pro') \
                       .replace('deepseek-v3.1', 'DeepSeek v3.1') \
                       .replace('grok-code-fast-1', 'Grok Code Fast-1')
    
    print(f"{display_name:<20} {tier2_score}/5        {tier3_score}/5        {total_score}/10       {success_rate:4.0f}%")

print("-" * 75)
print()
print("Tier 2: Intermediate complexity tasks (conformer generation, molecular descriptors,")
print("        pKa prediction, solubility calculations)")
print("Tier 3: Advanced multi-step workflows (tautomer enumeration, ADMET prediction,")
print("        protein-ligand docking, Fukui indices calculation)")
print()
print("Success rates represent the proportion of tasks completed correctly according to")
print("domain expert evaluation against literature benchmarks and experimental data.")