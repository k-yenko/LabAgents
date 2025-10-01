#!/bin/bash

# Batch run Claude models on tier1 questions
# Run this while tier1_002 opus is still running

source .venv/bin/activate

echo "🚀 Running Claude models on tier1_002-008..."

# tier1_002 - skip opus (already running), do sonnet
echo "📊 Running tier1_002 with Claude Sonnet..."
python openrouter_agent.py tier1_002 --model "anthropic/claude-sonnet-4"

# tier1_003 - both models
echo "📊 Running tier1_003 with Claude Opus..."
python openrouter_agent.py tier1_003 --model "anthropic/claude-opus-4.1"
echo "📊 Running tier1_003 with Claude Sonnet..."
python openrouter_agent.py tier1_003 --model "anthropic/claude-sonnet-4"

# tier1_004 - both models
echo "📊 Running tier1_004 with Claude Opus..."
python openrouter_agent.py tier1_004 --model "anthropic/claude-opus-4.1"
echo "📊 Running tier1_004 with Claude Sonnet..."
python openrouter_agent.py tier1_004 --model "anthropic/claude-sonnet-4"

# tier1_005 - both models
echo "📊 Running tier1_005 with Claude Opus..."
python openrouter_agent.py tier1_005 --model "anthropic/claude-opus-4.1"
echo "📊 Running tier1_005 with Claude Sonnet..."
python openrouter_agent.py tier1_005 --model "anthropic/claude-sonnet-4"

# tier1_006 - both models
echo "📊 Running tier1_006 with Claude Opus..."
python openrouter_agent.py tier1_006 --model "anthropic/claude-opus-4.1"
echo "📊 Running tier1_006 with Claude Sonnet..."
python openrouter_agent.py tier1_006 --model "anthropic/claude-sonnet-4"

# tier1_007 - both models
echo "📊 Running tier1_007 with Claude Opus..."
python openrouter_agent.py tier1_007 --model "anthropic/claude-opus-4.1"
echo "📊 Running tier1_007 with Claude Sonnet..."
python openrouter_agent.py tier1_007 --model "anthropic/claude-sonnet-4"

# tier1_008 - both models
echo "📊 Running tier1_008 with Claude Opus..."
python openrouter_agent.py tier1_008 --model "anthropic/claude-opus-4.1"
echo "📊 Running tier1_008 with Claude Sonnet..."
python openrouter_agent.py tier1_008 --model "anthropic/claude-sonnet-4"

echo "✅ Completed all Claude model runs!"
echo "📁 Check logs/ for results"
echo ""
echo "Next steps:"
echo "python llm_judge_evaluator.py tier1_002"
echo "python llm_judge_evaluator.py tier1_003"
echo "# ... etc for each question"