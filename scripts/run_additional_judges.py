"""
Run evaluations with Gemini 2.5 Pro and GPT-5 judges to test evaluator bias
"""

import subprocess
import sys
from pathlib import Path
import json

def get_all_log_files():
    """Get all successful log files from logs directory"""
    log_files = []
    logs_dir = Path('logs')

    for question_dir in sorted(logs_dir.glob('tier*')):
        for model_dir in question_dir.iterdir():
            if model_dir.is_dir():
                # Find the most recent successful log (not api_error or error)
                json_files = [f for f in model_dir.glob('*.json')
                             if 'api_error' not in f.name and 'error' not in f.name]
                if json_files:
                    # Get most recent
                    latest = max(json_files, key=lambda f: f.stat().st_mtime)
                    log_files.append(latest)

    return log_files

def run_evaluation(log_file, judge_model, output_dir):
    """Run a single evaluation"""
    cmd = [
        'python', 'llm_judge_evaluator.py',
        '--single', str(log_file),
        '--output-dir', output_dir,
        '--judge', judge_model
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

def main():
    judges = {
        'gemini': {
            'model': 'google/gemini-2.5-pro',
            'output_dir': 'evaluations_gemini'
        },
        'gpt5': {
            'model': 'openai/gpt-5',
            'output_dir': 'evaluations_gpt5'
        }
    }

    print("🔍 Finding all log files...")
    log_files = get_all_log_files()
    print(f"   Found {len(log_files)} log files\n")

    for judge_name, config in judges.items():
        judge_model = config['model']
        output_dir = config['output_dir']

        print(f"{'='*80}")
        print(f"🤖 Running evaluations with {judge_model}")
        print(f"   Output directory: {output_dir}")
        print(f"{'='*80}\n")

        success_count = 0
        fail_count = 0

        for i, log_file in enumerate(log_files, 1):
            question_id = log_file.parent.parent.name
            model_name = log_file.parent.name

            print(f"[{i}/{len(log_files)}] Evaluating {question_id}/{model_name}...", end=' ')

            success, output = run_evaluation(log_file, judge_model, output_dir)

            if success:
                print("✅")
                success_count += 1
            else:
                print(f"❌ {output[:100]}")
                fail_count += 1

        print(f"\n{'='*80}")
        print(f"✅ Completed {judge_name}: {success_count} successful, {fail_count} failed")
        print(f"{'='*80}\n")

    print(f"\n🎉 All evaluations complete!")
    print(f"   📁 Claude Sonnet 4 judge: evaluations_sonnet4/")
    print(f"   📁 Qwen 3 Max judge: evaluations_qwen/")
    print(f"   📁 Gemini 2.5 Pro judge: evaluations_gemini/")
    print(f"   📁 GPT-5 judge: evaluations_gpt5/")

if __name__ == "__main__":
    main()
