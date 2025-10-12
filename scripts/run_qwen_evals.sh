#!/bin/bash
# Run Qwen judge on all existing logs for bias comparison

echo "🤖 Running Qwen judge on all logs..."
echo "This will evaluate all existing logs with qwen/qwen-2.5-72b-instruct"
echo ""

# Activate venv and run
cd "$(dirname "$0")/.."

.venv/bin/python -c "
import asyncio
import glob
import os
from dotenv import load_dotenv
from llm_judge_evaluator import evaluate_single_log

load_dotenv()

async def run_all_qwen_evals():
    # Find all log files
    all_logs = []
    for log_file in glob.glob('logs/*/*/*.json'):
        if 'api_error' not in log_file:
            all_logs.append(log_file)

    print(f'Found {len(all_logs)} logs to evaluate with Qwen')
    print('='*80)

    successes = 0
    failures = 0

    for i, log_file in enumerate(all_logs, 1):
        question_id = log_file.split('/')[1]
        model_name = log_file.split('/')[2]

        print(f'\n[{i}/{len(all_logs)}] {question_id} - {model_name}')

        try:
            await evaluate_single_log(
                log_file,
                output_dir='evaluations_qwen',
                judge_model='qwen/qwen-2.5-72b-instruct',
                enable_web_search=True
            )
            successes += 1
            print(f'  ✅ Success ({successes}/{i})')
        except Exception as e:
            failures += 1
            print(f'  ❌ Failed: {e}')

    print(f'\n{'='*80}')
    print(f'COMPLETED: {successes} successes, {failures} failures')
    print(f'Qwen evaluations saved to: evaluations_qwen/')
    print(f'{'='*80}')

asyncio.run(run_all_qwen_evals())
"
