#!/usr/bin/env python3
"""
function_calling_eval.py - evaluates whether agents selected the correct tools for each question
"""

import json
import os
import sys

def load_expected_tools(folder_path):
    """Load expected tools from answer.md file"""
    answer_file = f"{folder_path}/answer.md"
    
    if not os.path.exists(answer_file):
        return []
    
    with open(answer_file, "r") as f:
        content = f.read()
    
    # Extract Expected Tool Use section
    expected_tools = []
    lines = content.split('\n')
    in_tool_section = False
    
    for line in lines:
        if line.startswith('**Expected Tool Use**:'):
            in_tool_section = True
            continue
        elif in_tool_section and line.startswith('**'):
            # End of tool section
            break
        elif in_tool_section and line.startswith('- `'):
            # Extract tool name between backticks
            tool_start = line.find('`') + 1
            tool_end = line.find('`', tool_start)
            if tool_start > 0 and tool_end > tool_start:
                tool_name = line[tool_start:tool_end]
                expected_tools.append(tool_name)
    
    return expected_tools

def evaluate_tool_selection(question, expected_tools, actual_tools, model_name, question_id):
    """Simple binary evaluation - 1 if all expected tools used (any order), 0 otherwise"""
    
    # Normalize tool names by removing prefixes like "mcp_rowan_"
    def normalize_tool_name(tool):
        # Remove common prefixes
        prefixes_to_remove = ["mcp_rowan_", "mcp__rowan__rowan_"]
        for prefix in prefixes_to_remove:
            if tool.startswith(prefix):
                return tool[len(prefix):]
        return tool
    
    # Normalize both expected and actual tools
    normalized_expected = set(normalize_tool_name(tool) for tool in expected_tools)
    normalized_actual = set(normalize_tool_name(tool) for tool in actual_tools)
    
    # Score is 1 if all expected tools are present, 0 otherwise
    # Extra tools are allowed
    has_all_required = normalized_expected.issubset(normalized_actual)
    score = 1 if has_all_required else 0
    
    missing_tools = list(normalized_expected - normalized_actual)
    extra_tools = list(normalized_actual - normalized_expected)
    
    return {
        "tool_selection_score": score,
        "missing_critical_tools": missing_tools,
        "extra_tools": extra_tools,
        "has_all_required": has_all_required,
        "normalized_expected": list(normalized_expected),
        "normalized_actual": list(normalized_actual),
        "notes": f"Simple binary evaluation: {'PASS' if has_all_required else 'FAIL'} - All required tools {'present' if has_all_required else 'missing'} (normalized tool names)"
    }

# Removed Claude judge function - using simple binary evaluation instead

def evaluate_question_folder(folder_path):
    """Evaluate tool selection for all models in a question folder"""
    # Load responses
    response_file = f"{folder_path}/response.jsonl"
    if not os.path.exists(response_file):
        print(f"No response.jsonl found in {folder_path}")
        return {}
    
    with open(response_file, "r") as f:
        responses = [json.loads(line) for line in f]
    
    question = responses[0]["question"]
    question_id = responses[0]["question_id"]
    
    # Load expected tools
    expected_tools = load_expected_tools(folder_path)
    print(f"Expected tools for {question_id}: {expected_tools}")
    
    all_scores = {}
    
    for resp in responses:
        print(f"Evaluating tool selection for {resp['model']}...")
        
        # Get actual tools used
        actual_tools = resp.get("tools_called", [])
        
        # Simple evaluation - no Claude judge needed
        evaluation = evaluate_tool_selection(
            question, expected_tools, actual_tools, resp["model"], question_id
        )
        
        # Add model-specific data  
        evaluation["expected_tools"] = expected_tools
        evaluation["actual_tools"] = actual_tools
        evaluation["tools_overlap"] = list(set(evaluation["normalized_expected"]) & set(evaluation["normalized_actual"]))
        # missing_tools already calculated correctly in evaluate_tool_selection using normalized names
        
        all_scores[resp["model"]] = evaluation
        print(f"Model {resp['model']}: Score = {evaluation['tool_selection_score']} ({'PASS' if evaluation['has_all_required'] else 'FAIL'})")
    
    # Load existing score.json or create new one
    score_file = f"{folder_path}/tool_selection_scores.json"
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
    
    # Update tool selection scores
    scores_key = f"{question_id}_tool_selection"
    score_data[scores_key] = all_scores
    
    # Update evaluation criteria
    score_data["evaluation_criteria"] = {
        **score_data.get("evaluation_criteria", {}),
        "evaluation_type": "simple_binary_tool_selection",
        "scoring": "1 if all expected tools present (any order), 0 otherwise",
        "allows_extra_tools": True,
        "focus": "required_tool_completeness"
    }
    
    # Calculate summary statistics
    total_models = len(all_scores)
    avg_score = sum(score.get("tool_selection_score", 0) for score in all_scores.values()) / total_models if total_models > 0 else 0
    passing_models = sum(1 for score in all_scores.values() if score.get("tool_selection_score", 0) == 1)
    
    score_data["summary"] = {
        "total_models": total_models,
        "average_tool_selection_score": round(avg_score, 1),
        "passing_models": passing_models,  # Score = 1
        "failing_models": total_models - passing_models,  # Score = 0
        "expected_tools_count": len(expected_tools)
    }
    
    # Save updated tool selection scores
    with open(score_file, "w") as f:
        json.dump(score_data, f, indent=2)
    
    print(f"Updated {folder_path}/tool_selection_scores.json")
    print(f"Results: Average tool selection score: {avg_score:.1f}")
    print(f"Passing models: {passing_models}/{total_models}")
    
    return score_data

if __name__ == "__main__":
    # Require folder argument
    if len(sys.argv) != 2:
        print("Usage: python function_calling_eval.py <folder>")
        print("Example: python function_calling_eval.py tier2_003")
        sys.exit(1)
    
    folder = sys.argv[1]
    # Add questions/ prefix if not already present
    if not folder.startswith('questions/'):
        folder = f'questions/{folder}'
    evaluate_question_folder(folder)