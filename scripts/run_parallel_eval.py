#!/usr/bin/env python3
"""
Automated parallel evaluation runner
Runs the same question across multiple models simultaneously
"""

import json
import time
import subprocess
import sys
from pathlib import Path

# Available models and their server ports
MODELS = {
    "claude-4.1-opus": 6277,
    "claude-4-sonnet": 6278,
    "gpt-5": 6279,
    "o3": 6280,
    "grok-4": 6281,
    "gemini-2.5-pro": 6282,
    "deepseek-v3.1": 6283,
    "grok-code-fast-1": 6284
}

def load_questions():
    """Load questions from v2_queries.md and extract question details"""
    queries_file = Path("questions/v2_queries.md")
    
    if not queries_file.exists():
        print("❌ questions/v2_queries.md not found!")
        return {}
    
    # For now, return the questions we know about
    # In a full implementation, you'd parse the markdown file
    questions = {
        "tier2_002": "Generate conformers of ibuprofen, optimize the lowest energy conformer, then calculate its logP and pKa values",
        "tier2_003": "Calculate molecular descriptors for caffeine, predict its solubility in water at 25°C, and determine its dipole moment",
        "tier2_004": "Find all tautomers of morphine and calculate the pKa of each tautomeric form to determine which is dominant at physiological pH",
        "tier2_005": "Optimize paracetamol geometry, calculate its electronic properties including HOMO/LUMO energies and dipole moment",
        "tier2_006": "Calculate the oxidation and reduction potentials of benzene versus SCE in acetonitrile",
        "tier2_007": "Predict the solubility of caffeine in water at 25°C, 37°C, and 50°C to determine the temperature dependence",
        "tier3_001": "Find the major tautomers of warfarin, calculate the pKa for each tautomeric form, identify the dominant form at pH 7.4, then predict its protein binding affinity",
        "tier3_002": "Optimize acetaminophen structure, calculate Fukui indices to identify reactive sites, predict sites of glucuronidation and sulfation, then calculate the ADMET properties",
        "tier3_003": "Generate conformers of atorvastatin, dock the top 5 conformers to HMG-CoA reductase (PDB: 1HWK), calculate binding energies, and compare to the crystal structure conformation",
        "tier3_004": "Run a dihedral scan on serotonin's ethylamine chain, identify the energy minimum, then calculate Fukui indices to predict the most reactive sites for electrophilic attack",
        "tier3_005": "Generate conformers of paclitaxel (taxol), select the lowest energy conformer, then predict its ADMET properties focusing on blood-brain barrier permeability",
        "tier3_006": "Optimize penicillin G geometry, calculate molecular descriptors, predict solubility at multiple temperatures, then dock to a β-lactamase enzyme to understand resistance mechanisms"
    }
    
    return questions

def generate_eval_commands(question_id, question_text, models_to_run):
    """Generate start_eval_session commands for each model"""
    commands = {}
    
    for model in models_to_run:
        if model not in MODELS:
            print(f"⚠️  Unknown model: {model}")
            continue
            
        command = f'Use the start_eval_session tool with question_id="{question_id}", model="{model}", question="{question_text}"'
        commands[model] = command
    
    return commands

def print_parallel_instructions(question_id, question_text, models_to_run):
    """Print instructions for running parallel evaluations"""
    
    print(f"🎯 PARALLEL EVALUATION SETUP")
    print(f"Question ID: {question_id}")
    print(f"Question: {question_text[:80]}{'...' if len(question_text) > 80 else ''}")
    print(f"Models: {', '.join(models_to_run)}")
    print()
    
    print("📋 STEP-BY-STEP INSTRUCTIONS:")
    print()
    
    print("1. 🚀 START PARALLEL SERVERS:")
    print("   python3 start_parallel_servers.py")
    print("   (Leave this running in a terminal)")
    print()
    
    print(f"2. 🪟 OPEN {len(models_to_run)} CLAUDE CODE WORKSPACES:")
    for i, model in enumerate(models_to_run, 1):
        port = MODELS[model]
        print(f"   Workspace {i}: Connect to MCP server at http://127.0.0.1:{port}/sse ({model})")
    print()
    
    print("3. 🎬 COPY-PASTE THESE COMMANDS (one per workspace):")
    print()
    
    for i, model in enumerate(models_to_run, 1):
        command = f'Use the start_eval_session tool with question_id="{question_id}", model="{model}", question="{question_text}"'
        print(f"   Workspace {i} ({model}):")
        print(f"   {command}")
        print()
    
    print("4. ▶️  RUN ALL COMMANDS SIMULTANEOUSLY")
    print("   Each model will work on the question in parallel")
    print()
    
    print("5. ✅ RESULTS WILL BE AUTOMATICALLY SAVED TO:")
    print("   • results/v2_results.jsonl (updated with answers)")
    print("   • rowan_eval_results.jsonl (detailed logs)")
    print()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 run_parallel_eval.py <question_id> [model1,model2,...]")
        print()
        print("Available question IDs:")
        questions = load_questions()
        for qid in questions.keys():
            print(f"  • {qid}")
        print()
        print("Available models:")
        for model in MODELS.keys():
            print(f"  • {model}")
        print()
        print("Examples:")
        print("  python3 run_parallel_eval.py tier2_002")
        print("  python3 run_parallel_eval.py tier2_002 claude-4.1-opus,gpt-5")
        return
    
    question_id = sys.argv[1]
    questions = load_questions()
    
    if question_id not in questions:
        print(f"❌ Question ID '{question_id}' not found!")
        print("Available question IDs:", list(questions.keys()))
        return
    
    question_text = questions[question_id]
    
    # Determine which models to run
    if len(sys.argv) > 2:
        models_to_run = [m.strip() for m in sys.argv[2].split(',')]
    else:
        models_to_run = list(MODELS.keys())  # All models
    
    # Validate models
    invalid_models = [m for m in models_to_run if m not in MODELS]
    if invalid_models:
        print(f"❌ Invalid models: {invalid_models}")
        print("Available models:", list(MODELS.keys()))
        return
    
    print_parallel_instructions(question_id, question_text, models_to_run)

if __name__ == "__main__":
    main()