#!/usr/bin/env python3
"""
Simple, clean visualization for tier1_001 trick question.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np

def extract_predicted_value(log_data):
    """Extract the predicted solubility value from final answer"""
    final_answer = log_data.get('final_answer', '')
    import re

    # Models that asked for SMILES help
    if 'please provide' in final_answer.lower() or 'could not resolve' in final_answer.lower():
        return "Asked for SMILES"
    if 'apologize' in final_answer.lower() and 'smiles string' in final_answer.lower():
        return "Asked for SMILES"

    # Models that submitted workflow but never retrieved results (got stuck polling)
    if 'submitted' in final_answer.lower() and 'workflow' in final_answer.lower():
        return "Submitted, didn't retrieve"
    if "i'll check" in final_answer.lower() or "i'll wait" in final_answer.lower():
        return "Submitted, didn't retrieve"
    if "i'll now check" in final_answer.lower() and 'workflow' in final_answer.lower():
        return "Submitted, didn't retrieve"

    # Look for mg/mL first (most specific clinical value)
    match = re.search(r'(\d+\.?\d*)\s*mg/mL', final_answer)
    if match:
        return f"{match.group(1)} mg/mL"

    # Look for g/L
    match = re.search(r'(\d+\.?\d*)\s*g/L', final_answer)
    if match:
        return f"{match.group(1)} g/L"

    # Look for mM or mmol
    match = re.search(r'(\d+\.?\d*)\s*mM', final_answer)
    if match:
        return f"{match.group(1)} mM"

    # Look for log S value (more flexible regex)
    match = re.search(r'(-?\d+\.?\d*)\s*log\s*S', final_answer, re.IGNORECASE)
    if match:
        return f"log S = {match.group(1)}"
    match = re.search(r'log\s*S[:\s=,\(]+(-?\d+\.?\d*)', final_answer, re.IGNORECASE)
    if match:
        return f"log S = {match.group(1)}"

    # Look for molarity
    match = re.search(r'(\d+\.?\d*)\s*M(?:\s|,|\.)', final_answer)
    if match:
        return f"{match.group(1)} M"

    return "Reported value"

def load_tier1_001_data():
    """Load all logs and evaluations for tier1_001"""
    data = []
    logs_dir = Path('logs/tier1_001')

    for model_dir in sorted(logs_dir.iterdir()):
        if not model_dir.is_dir():
            continue

        log_files = list(model_dir.glob('*.json'))
        if not log_files:
            continue
        log_file = max(log_files, key=lambda f: f.stat().st_mtime)

        with open(log_file) as f:
            log_data = json.load(f)

        model_name = log_data['model_name'].replace('/', '_')
        model_display = log_data['model_name'].split('/')[-1]

        # Clean up model display names
        if ':free' in model_display:
            model_display = model_display.replace(':free', '')

        # Load evaluations
        sonnet_eval_path = Path(f'evaluations_sonnet4/tier1_001/json/{model_name}_evaluation.json')
        qwen_eval_path = Path(f'evaluations_qwen/tier1_001/json/{model_name}_evaluation.json')

        sonnet_eval = json.load(open(sonnet_eval_path)) if sonnet_eval_path.exists() else None
        qwen_eval = json.load(open(qwen_eval_path)) if qwen_eval_path.exists() else None

        entry = {
            'model': model_display,
            'predicted_value': extract_predicted_value(log_data),
            'sonnet_correctness': sonnet_eval.get('correctness_score', 0) if sonnet_eval else 0,
            'qwen_correctness': qwen_eval.get('correctness_score', 0) if qwen_eval else 0,
            'sonnet_total': sonnet_eval.get('total_score', 0) if sonnet_eval else 0,
            'qwen_total': qwen_eval.get('total_score', 0) if qwen_eval else 0,
            'sonnet_pass': 'Pass' if (sonnet_eval and sonnet_eval.get('overall_assessment') == 'pass') else 'Fail',
            'qwen_pass': 'Pass' if (qwen_eval and qwen_eval.get('overall_assessment') == 'pass') else 'Fail',
        }
        data.append(entry)

    return pd.DataFrame(data)

def create_figure(df):
    """Create modern, professional table visualization"""

    # Setup modern styling to match overall_performance.png
    import matplotlib
    matplotlib.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
        'font.size': 11,
        'figure.facecolor': 'white',
    })

    fig = plt.figure(figsize=(16, 6.5))
    ax_table = fig.add_subplot(111)
    ax_table.axis('tight')
    ax_table.axis('off')

    # Prepare table data
    table_data = []
    for _, row in df.iterrows():
        table_data.append([
            row['model'],
            row['predicted_value'],
            f"{row['sonnet_correctness']}/2",
            f"{row['qwen_correctness']}/2",
            f"{row['sonnet_total']}/6\n{row['sonnet_pass']}",
            f"{row['qwen_total']}/6\n{row['qwen_pass']}"
        ])

    # Create table with modern styling
    table = ax_table.table(
        cellText=table_data,
        colLabels=['Model', 'What Model Reported',
                  'Sonnet Judge\nCorrectness', 'Qwen Judge\nCorrectness',
                  'Sonnet\nTotal/Pass', 'Qwen\nTotal/Pass'],
        cellLoc='center',
        loc='center',
        colWidths=[0.16, 0.24, 0.12, 0.12, 0.15, 0.15]
    )

    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.5)

    # Modern header styling (dark header like overall_performance.png)
    for i in range(6):
        cell = table[(0, i)]
        cell.set_facecolor('#1F2937')  # dark gray matching modern aesthetic
        cell.set_text_props(weight='bold', color='white', fontsize=12)
        cell.set_edgecolor('#E5E7EB')
        cell.set_linewidth(1.5)

    # Color rows with modern palette
    for i in range(1, len(table_data) + 1):
        # All cells get clean borders
        for j in range(6):
            table[(i, j)].set_edgecolor('#E5E7EB')
            table[(i, j)].set_linewidth(1.0)

        # Model name - light gray background
        table[(i, 0)].set_facecolor('#F9FAFB')
        table[(i, 0)].set_text_props(weight='500', fontsize=11)

        # Predicted value - cream background, monospace
        table[(i, 1)].set_facecolor('#FFFBEB')
        table[(i, 1)].set_text_props(fontsize=10, family='monospace')

        # Sonnet correctness - modern red/yellow/green
        sonnet_correct = df.iloc[i-1]['sonnet_correctness']
        if sonnet_correct == 0:
            table[(i, 2)].set_facecolor('#FEE2E2')  # modern soft red
        elif sonnet_correct == 1:
            table[(i, 2)].set_facecolor('#FEF3C7')  # modern soft yellow
        else:
            table[(i, 2)].set_facecolor('#D1FAE5')  # modern soft green

        # Qwen correctness
        qwen_correct = df.iloc[i-1]['qwen_correctness']
        if qwen_correct == 0:
            table[(i, 3)].set_facecolor('#FEE2E2')
        elif qwen_correct == 1:
            table[(i, 3)].set_facecolor('#FEF3C7')
        else:
            table[(i, 3)].set_facecolor('#D1FAE5')

        # Pass/Fail columns - modern green/red
        sonnet_pass = df.iloc[i-1]['sonnet_pass']
        table[(i, 4)].set_facecolor('#D1FAE5' if sonnet_pass == 'Pass' else '#FEE2E2')
        if sonnet_pass == 'Pass':
            table[(i, 4)].set_text_props(weight='600', color='#059669')
        else:
            table[(i, 4)].set_text_props(weight='600', color='#DC2626')

        qwen_pass = df.iloc[i-1]['qwen_pass']
        table[(i, 5)].set_facecolor('#D1FAE5' if qwen_pass == 'Pass' else '#FEE2E2')
        if qwen_pass == 'Pass':
            table[(i, 5)].set_text_props(weight='600', color='#059669')
        else:
            table[(i, 5)].set_text_props(weight='600', color='#DC2626')

    # No title - will be embedded in README with context
    plt.savefig('plots/performance/tier1_001_trick_question.png',
                dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.05)
    plt.close()

    print("\nFigure saved to: plots/performance/tier1_001_trick_question.png")

def main():
    print("Loading tier1_001 data...")
    df = load_tier1_001_data()

    print("Creating simplified figure...")
    create_figure(df)

    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"All {len(df)} models reported solubility values")
    print(f"Avg correctness (Sonnet): {df['sonnet_correctness'].mean():.2f}/2")
    print(f"Avg correctness (Qwen): {df['qwen_correctness'].mean():.2f}/2")
    print(f"But passed anyway (Sonnet): {(df['sonnet_pass']=='Pass').sum()}/{len(df)}")
    print(f"But passed anyway (Qwen): {(df['qwen_pass']=='Pass').sum()}/{len(df)}")
    print("="*70)

if __name__ == "__main__":
    main()
