#!/usr/bin/env python3
"""
correctness_eval.py - simple llm judge evaluation for correctness scoring
"""

import json
import os
import sys
import anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def evaluate_response(question, response, model_name, answer_file_path):
    # Load rubric
    with open("evaluation_rubric.md", "r") as f:
        rubric = f.read()
    
    # Load the expected answer
    with open(answer_file_path, "r") as f:
        expected_answer = f.read()
    
    prompt = f"""{rubric}

## Question
{question}

## Expected Answer (Reference)
{expected_answer}

## Model Response to Evaluate
{response}

## Model Name
{model_name}

Please evaluate this response against the expected answer using the rubric criteria."""
    
    return prompt

def call_claude_judge(prompt):
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def evaluate_question_folder(folder_path):
    # Load responses
    with open(f"{folder_path}/response.jsonl", "r") as f:
        responses = [json.loads(line) for line in f]
    
    question = responses[0]["question"]
    question_id = responses[0]["question_id"]
    answer_file = f"{folder_path}/answer.md"
    
    all_scores = {}
    
    for resp in responses:
        print(f"Evaluating {resp['model']}...")
        
        # Generate prompt
        prompt = evaluate_response(question, resp["response"], resp["model"], answer_file)
        
        # Call Claude judge
        try:
            claude_response = call_claude_judge(prompt)
            print(f"Raw Claude response for {resp['model']}: {claude_response[:200]}...")
            
            # Clean the response - sometimes Claude adds extra text
            claude_response = claude_response.strip()
            
            # Try to extract JSON from the response
            if "{" in claude_response:
                start = claude_response.find("{")
                end = claude_response.rfind("}") + 1
                json_part = claude_response[start:end]
                evaluation = json.loads(json_part)
            else:
                raise ValueError("No JSON found in Claude response")
            
            # Add to scores (handle if Claude returns nested structure)
            if resp["model"] in evaluation:
                all_scores[resp["model"]] = evaluation[resp["model"]]
            else:
                # If Claude returns single evaluation, assign to model
                all_scores[resp["model"]] = evaluation
                
        except Exception as e:
            print(f"Error evaluating {resp['model']}: {e}")
            print(f"Claude response was: {claude_response[:500] if 'claude_response' in locals() else 'No response'}")
            all_scores[resp["model"]] = {
                "correct": False,
                "score": 0,
                "notes": f"Evaluation error: {str(e)}"
            }
    
    # Load existing score.json
    score_file = f"{folder_path}/score.json"
    if os.path.exists(score_file):
        try:
            with open(score_file, "r") as f:
                content = f.read().strip()
                if content:
                    score_data = json.loads(content)
                else:
                    score_data = {}
        except json.JSONDecodeError:
            print(f"Warning: {score_file} contains invalid JSON, creating new one")
            score_data = {}
    else:
        score_data = {}
    
    # Update scores section
    scores_key = f"{question_id}_scores"
    score_data[scores_key] = all_scores
    
    # Update evaluation criteria
    score_data["evaluation_criteria"] = {
        **score_data.get("evaluation_criteria", {}),
        "scoring_method": "llm_judge_claude_sonnet",
        "judge_model": "claude-sonnet-4-20250514"
    }
    
    # Calculate and update summary
    total_models = len(all_scores)
    correct_answers = sum(1 for score in all_scores.values() if score.get("correct", False))
    
    score_data["summary"] = {
        "total_models": total_models,
        "correct_answers": correct_answers,
        "incorrect_answers": total_models - correct_answers,
        "success_rate": f"{(correct_answers / total_models * 100):.1f}%" if total_models > 0 else "0%"
    }
    
    # Save updated score.json
    with open(score_file, "w") as f:
        json.dump(score_data, f, indent=2)
    
    print(f"Updated {folder_path}/score.json")
    print(f"Results: {correct_answers}/{total_models} correct ({score_data['summary']['success_rate']})")
    
    return score_data

if __name__ == "__main__":
    # Require folder argument
    if len(sys.argv) != 2:
        print("Usage: python evaluate_responses.py <folder>")
        print("Example: python evaluate_responses.py tier2_003")
        sys.exit(1)
    
    folder = sys.argv[1]
    # Add questions/ prefix if not already present
    if not folder.startswith('questions/'):
        folder = f'questions/{folder}'
    evaluate_question_folder(folder)