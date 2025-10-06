#!/bin/bash
# Run GPT-5 and Gemini judges in parallel

echo "🚀 Starting parallel judge evaluation..."
echo "  - GPT-5 judge → evaluations_gpt5/"
echo "  - Gemini judge → evaluations_gemini/"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to parent directory (labagents_v2)
cd "$PARENT_DIR"

# Run both judges in parallel using background processes
.venv/bin/python scripts/run_all_evals_gpt5_judge.py > gpt5_judge.log 2>&1 &
GPT5_PID=$!
echo "📊 GPT-5 judge started (PID: $GPT5_PID, log: gpt5_judge.log)"

.venv/bin/python scripts/run_all_evals_gemini_judge.py > gemini_judge.log 2>&1 &
GEMINI_PID=$!
echo "📊 Gemini judge started (PID: $GEMINI_PID, log: gemini_judge.log)"

echo ""
echo "⏳ Waiting for both judges to complete..."
echo "   You can monitor progress with:"
echo "   tail -f gpt5_judge.log"
echo "   tail -f gemini_judge.log"
echo ""

# Wait for both processes to complete
wait $GPT5_PID
GPT5_EXIT=$?

wait $GEMINI_PID
GEMINI_EXIT=$?

echo ""
echo "=" | head -c 80
echo ""
echo "🏁 PARALLEL EVALUATION COMPLETE"
echo "=" | head -c 80
echo ""

if [ $GPT5_EXIT -eq 0 ]; then
    echo "✅ GPT-5 judge completed successfully"
else
    echo "❌ GPT-5 judge failed (exit code: $GPT5_EXIT)"
fi

if [ $GEMINI_EXIT -eq 0 ]; then
    echo "✅ Gemini judge completed successfully"
else
    echo "❌ Gemini judge failed (exit code: $GEMINI_EXIT)"
fi

echo ""
echo "📁 Output directories:"
echo "   - evaluations_gpt5/"
echo "   - evaluations_gemini/"
echo ""
echo "📋 Logs:"
echo "   - gpt5_judge.log"
echo "   - gemini_judge.log"
