#!/bin/bash

# Missing questions for Sonnet 4.5
MISSING_QUESTIONS=(
  "tier2_007"
)

MODEL="anthropic/claude-sonnet-4.5"

echo "Running ${#MISSING_QUESTIONS[@]} missing questions for Sonnet 4.5..."

for question in "${MISSING_QUESTIONS[@]}"; do
  echo ""
  echo "========================================="
  echo "Running $question with $MODEL"
  echo "========================================="

  python3 agent_runner.py "$question" --model "$MODEL"

  if [ $? -eq 0 ]; then
    echo "✅ $question completed"
  else
    echo "❌ $question failed"
  fi
done

echo ""
echo "========================================="
echo "All missing questions processed!"
echo "========================================="
