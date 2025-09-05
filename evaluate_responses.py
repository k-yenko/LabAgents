#!/usr/bin/env python3
"""
LLM-as-a-Judge Evaluation Script
Evaluates model responses using the evaluation rubric and generates score.json files
"""

import json
import os
import glob
from pathlib import Path
from typing import Dict, Any, List
import openai  # or whatever LLM client you're using

class ResponseEvaluator:
    def __init__(self, rubric_path: str = "evaluation_rubric.md", 
                 expected_values_path: str = "expected_values.json",
                 judge_model: str = "gpt-4"):
        """Initialize the evaluator with rubric and judge model"""
        self.rubric_path = rubric_path
        self.expected_values_path = expected_values_path
        self.judge_model = judge_model
        self.rubric_content = self._load_rubric()
        self.expected_values = self._load_expected_values_config()
        
    def _load_rubric(self) -> str:
        """Load the evaluation rubric from file"""
        with open(self.rubric_path, 'r') as f:
            return f.read()
    
    def _load_expected_values_config(self) -> Dict[str, Any]:
        """Load expected values configuration from JSON file"""
        with open(self.expected_values_path, 'r') as f:
            return json.load(f)
    
    def _get_expected_values(self, question_id: str) -> Dict[str, Any]:
        """Get expected values for a specific question"""
        return self.expected_values.get(question_id, {})
    
    def _create_judge_prompt(self, question: str, response: str, expected_values: Dict[str, Any]) -> str:
        """Create the prompt for the LLM judge"""
        prompt = f"""{self.rubric_content}

## Question to Evaluate
{question}

## Expected Values (for reference)
{expected_values.get('description', 'No specific expected values provided')}

## Model Response to Evaluate
{response}

Please evaluate this response according to the rubric above and return the JSON format specified."""
        
        return prompt
    
    def evaluate_single_response(self, question: str, response: str, model_name: str, expected_values: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single model response"""
        if not response.strip():
            return {
                model_name: {
                    "correct": False,
                    "score": 0,
                    "notes": "Empty response - no answer provided"
                }
            }
        
        prompt = self._create_judge_prompt(question, response, expected_values)
        
        try:
            # Call your LLM judge here - this is a placeholder
            # Replace with your actual LLM client call
            judge_response = self._call_judge_llm(prompt)
            
            # Parse the JSON response from the judge
            evaluation = json.loads(judge_response)
            
            # Ensure the evaluation has the correct structure
            if model_name not in evaluation:
                # If judge didn't use the exact model name, restructure
                if len(evaluation) == 1:
                    key = list(evaluation.keys())[0]
                    evaluation[model_name] = evaluation.pop(key)
                else:
                    raise ValueError("Judge response format incorrect")
            
            return evaluation
            
        except Exception as e:
            print(f"Error evaluating {model_name}: {e}")
            return {
                model_name: {
                    "correct": False,
                    "score": 0,
                    "notes": f"Evaluation error: {str(e)}"
                }
            }
    
    def _call_judge_llm(self, prompt: str) -> str:
        """Call the LLM judge - replace with your actual implementation"""
        # Placeholder - replace with your actual LLM client
        # Example for OpenAI:
        # client = openai.OpenAI()
        # response = client.chat.completions.create(
        #     model=self.judge_model,
        #     messages=[{"role": "user", "content": prompt}],
        #     temperature=0
        # )
        # return response.choices[0].message.content
        
        # For now, return a mock response
        return '{"mock_model": {"correct": true, "score": 1, "notes": "Mock evaluation"}}'
    
    def evaluate_question_folder(self, folder_path: str) -> Dict[str, Any]:
        """Evaluate all responses in a question folder and generate score.json"""
        response_file = os.path.join(folder_path, "response.jsonl")
        
        if not os.path.exists(response_file):
            print(f"No response.jsonl found in {folder_path}")
            return {}
        
        # Load responses
        responses = []
        with open(response_file, 'r') as f:
            for line in f:
                responses.append(json.loads(line.strip()))
        
        if not responses:
            print(f"No responses found in {response_file}")
            return {}
        
        # Get question info from first response
        question_id = responses[0]["question_id"]
        question = responses[0]["question"]
        expected_values = self._get_expected_values(question_id)
        
        # Evaluate each response
        all_evaluations = {}
        for response_data in responses:
            model_name = response_data["model"]
            response_text = response_data["response"]
            
            evaluation = self.evaluate_single_response(
                question, response_text, model_name, expected_values
            )
            all_evaluations.update(evaluation)
        
        # Create score.json structure
        score_data = {
            f"{question_id}_scores": all_evaluations,
            "evaluation_criteria": {
                "scoring_method": "llm_judge_binary",
                "rubric_file": self.rubric_path,
                "judge_model": self.judge_model,
                **expected_values
            },
            "summary": self._calculate_summary(all_evaluations)
        }
        
        # Save score.json
        score_file = os.path.join(folder_path, "score.json")
        with open(score_file, 'w') as f:
            json.dump(score_data, f, indent=2)
        
        print(f"Generated {score_file}")
        return score_data
    
    def _calculate_summary(self, evaluations: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics"""
        total_models = len(evaluations)
        correct_answers = sum(1 for eval_data in evaluations.values() if eval_data["correct"])
        incorrect_answers = total_models - correct_answers
        success_rate = f"{(correct_answers / total_models * 100):.1f}%" if total_models > 0 else "0%"
        
        return {
            "total_models": total_models,
            "correct_answers": correct_answers,
            "incorrect_answers": incorrect_answers,
            "success_rate": success_rate
        }
    
    def evaluate_all_questions(self, base_path: str = ".") -> None:
        """Evaluate all question folders"""
        # Find all tier*/response.jsonl files
        pattern = os.path.join(base_path, "tier*/response.jsonl")
        response_files = glob.glob(pattern)
        
        for response_file in response_files:
            folder_path = os.path.dirname(response_file)
            print(f"Evaluating {folder_path}...")
            self.evaluate_question_folder(folder_path)

def main():
    """Main execution function"""
    evaluator = ResponseEvaluator()
    
    # Evaluate all questions
    evaluator.evaluate_all_questions()
    
    print("Evaluation complete!")

if __name__ == "__main__":
    main()
