#!/usr/bin/env python3
"""
analyze_log_patterns.py - analyze logs for efficiency, cost, and performance patterns
"""

import json
import glob
import pandas as pd
from pathlib import Path
from collections import defaultdict

def normalize_model_name(model_name):
    """Normalize model name for consistency"""
    return model_name.replace(':free', '').replace('_free', '')

def load_all_logs():
    """Load all successful log files and extract metrics"""
    log_data = []

    log_files = glob.glob("logs/*/*/*.json")

    for log_file in log_files:
        if 'api_error' in log_file:
            continue

        try:
            with open(log_file, 'r') as f:
                data = json.load(f)

            model_name = normalize_model_name(data.get('model_name', 'unknown'))
            question_id = data.get('question_id', 'unknown')
            tier = question_id.split('_')[0] if '_' in question_id else 'tier1'

            log_data.append({
                'model': model_name,
                'question': question_id,
                'tier': tier,
                'time_ms': data.get('total_time_ms', 0),
                'time_s': data.get('total_time_ms', 0) / 1000,
                'cost_usd': data.get('total_cost_usd', 0),
                'total_tokens': data.get('total_tokens', 0),
                'prompt_tokens': data.get('total_prompt_tokens', 0),
                'completion_tokens': data.get('total_completion_tokens', 0),
                'reasoning_tokens': data.get('total_reasoning_tokens', 0),
                'tool_calls': data.get('total_tool_calls', 0),
                'successful_tool_calls': data.get('successful_tool_calls', 0),
                'api_calls': data.get('total_api_calls', 0),
                'completed': data.get('completed_successfully', False),
                'thinking_steps': data.get('total_thinking_steps', 0),
            })
        except Exception as e:
            print(f"Error loading {log_file}: {e}")

    return pd.DataFrame(log_data)

def analyze_efficiency(df):
    """Analyze model efficiency metrics"""
    print("\n" + "="*80)
    print("📊 EFFICIENCY ANALYSIS")
    print("="*80)

    # Group by model
    model_stats = df.groupby('model').agg({
        'time_s': ['mean', 'median', 'sum'],
        'cost_usd': ['mean', 'median', 'sum'],
        'total_tokens': ['mean', 'median', 'sum'],
        'tool_calls': ['mean', 'median', 'sum'],
        'question': 'count'
    }).round(3)

    model_stats.columns = ['_'.join(col).strip() for col in model_stats.columns.values]
    model_stats = model_stats.rename(columns={'question_count': 'num_runs'})

    # Sort by different metrics
    print("\n🕐 By Average Time (fastest first):")
    print(model_stats.sort_values('time_s_mean')[['time_s_mean', 'time_s_median', 'num_runs']].head(10))

    print("\n💰 By Average Cost (cheapest first):")
    print(model_stats.sort_values('cost_usd_mean')[['cost_usd_mean', 'cost_usd_sum', 'num_runs']].head(10))

    print("\n🪙 By Average Tokens (most efficient first):")
    print(model_stats.sort_values('total_tokens_mean')[['total_tokens_mean', 'total_tokens_sum', 'num_runs']].head(10))

    print("\n🔧 By Average Tool Calls:")
    print(model_stats.sort_values('tool_calls_mean', ascending=False)[['tool_calls_mean', 'tool_calls_sum', 'num_runs']].head(10))

    return model_stats

def analyze_o3_failures(df):
    """Deep dive into o3's poor performance"""
    print("\n" + "="*80)
    print("🔍 O3 FAILURE ANALYSIS")
    print("="*80)

    o3_data = df[df['model'] == 'openai/o3'].copy()

    if len(o3_data) == 0:
        print("No o3 data found")
        return

    print(f"\nTotal o3 runs: {len(o3_data)}")
    print(f"Completed successfully: {o3_data['completed'].sum()} ({o3_data['completed'].sum()/len(o3_data)*100:.1f}%)")

    print("\n📊 O3 Statistics:")
    print(f"  Avg time: {o3_data['time_s'].mean():.2f}s (median: {o3_data['time_s'].median():.2f}s)")
    print(f"  Avg cost: ${o3_data['cost_usd'].mean():.4f} (median: ${o3_data['cost_usd'].median():.4f})")
    print(f"  Avg tokens: {o3_data['total_tokens'].mean():.0f} (median: {o3_data['total_tokens'].median():.0f})")
    print(f"  Avg tool calls: {o3_data['tool_calls'].mean():.1f} (median: {o3_data['tool_calls'].median():.1f})")
    print(f"  Avg reasoning tokens: {o3_data['reasoning_tokens'].mean():.0f}")

    print("\n🔧 Tool Call Success Rate:")
    o3_data['tool_success_rate'] = o3_data.apply(
        lambda row: row['successful_tool_calls'] / row['tool_calls'] if row['tool_calls'] > 0 else 0,
        axis=1
    )
    print(f"  Avg success rate: {o3_data['tool_success_rate'].mean()*100:.1f}%")

    print("\n❌ Failed runs (tool calls):")
    failed = o3_data[~o3_data['completed']]
    if len(failed) > 0:
        print(f"  Failed: {len(failed)} runs")
        print(f"  Avg tool calls in failures: {failed['tool_calls'].mean():.1f}")
        print(f"  Avg successful tools in failures: {failed['successful_tool_calls'].mean():.1f}")

    return o3_data

def analyze_tool_use_patterns(df):
    """Analyze which models use tools most effectively"""
    print("\n" + "="*80)
    print("🔧 TOOL USE PATTERNS")
    print("="*80)

    # Calculate tool success rate for each model
    model_tool_stats = df.groupby('model').apply(
        lambda x: pd.Series({
            'avg_tool_calls': x['tool_calls'].mean(),
            'avg_successful_tools': x['successful_tool_calls'].mean(),
            'tool_success_rate': x['successful_tool_calls'].sum() / x['tool_calls'].sum() if x['tool_calls'].sum() > 0 else 0,
            'completion_rate': x['completed'].sum() / len(x),
            'num_runs': len(x)
        })
    ).round(3)

    print("\n📊 Tool Use Effectiveness (by success rate):")
    print(model_tool_stats.sort_values('tool_success_rate', ascending=False))

    print("\n🎯 Tool Calls vs Completion Rate:")
    comparison = model_tool_stats[['avg_tool_calls', 'tool_success_rate', 'completion_rate']].sort_values('completion_rate', ascending=False)
    print(comparison)

    return model_tool_stats

def find_interesting_patterns(df):
    """Find other interesting patterns in the data"""
    print("\n" + "="*80)
    print("🔍 INTERESTING PATTERNS")
    print("="*80)

    # Token efficiency (tokens per successful completion)
    completed_df = df[df['completed'] == True].copy()
    if len(completed_df) > 0:
        print("\n💡 Token Efficiency (successful completions only):")
        token_efficiency = completed_df.groupby('model')['total_tokens'].mean().sort_values()
        print(token_efficiency.head(10))

    # Cost efficiency (cost per successful completion)
    if len(completed_df) > 0:
        print("\n💰 Cost Efficiency (successful completions only):")
        cost_efficiency = completed_df.groupby('model')['cost_usd'].mean().sort_values()
        print(cost_efficiency.head(10))

    # Tier-based analysis
    print("\n📈 Performance by Tier:")
    tier_completion = df.groupby(['tier', 'model'])['completed'].mean().unstack().fillna(0)
    print(tier_completion.round(3))

    # Reasoning tokens analysis
    print("\n🧠 Reasoning Token Usage:")
    reasoning_stats = df.groupby('model')['reasoning_tokens'].agg(['mean', 'sum', 'count']).sort_values('mean', ascending=False)
    print(reasoning_stats.head(10))

def save_analysis_data(model_stats, o3_data, tool_stats, df):
    """Save analysis data for visualization"""
    # Save summary statistics
    model_stats.to_csv('analysis/model_efficiency_stats.csv')

    # Save full data
    df.to_csv('analysis/all_log_data.csv', index=False)

    # Save o3 specific data
    if o3_data is not None and len(o3_data) > 0:
        o3_data.to_csv('analysis/o3_analysis.csv', index=False)

    # Save tool stats
    tool_stats.to_csv('analysis/tool_use_stats.csv')

    print("\n✅ Analysis data saved to analysis/ directory")

if __name__ == "__main__":
    print("🔍 Analyzing log patterns...")

    # Create analysis directory
    import os
    os.makedirs('analysis', exist_ok=True)

    # Load data
    df = load_all_logs()
    print(f"📊 Loaded {len(df)} log entries from {df['model'].nunique()} models")

    # Run analyses
    model_stats = analyze_efficiency(df)
    o3_data = analyze_o3_failures(df)
    tool_stats = analyze_tool_use_patterns(df)
    find_interesting_patterns(df)

    # Save data
    save_analysis_data(model_stats, o3_data, tool_stats, df)

    print("\n✅ Analysis complete!")
