# (Kat's) Ascendancy Trials

A benchmark for evaluating Large Language Models' tool-use capabilities in biological and chemical problem solving.

**Inspired by:** [ChemIQ: A Chemistry Intelligence Test for Chemical Reasoning](https://arxiv.org/abs/2505.07735) | [GitHub](https://github.com/oxpig/ChemIQ)

## Overview

While ChemIQ evaluates the performance of LLMs through direct questioning, **Ascendancy Trials** evaluates how effectively LLMs can leverage external tools (i.e. MCPs) to solve complex molecular problems. This benchmark tests the skill of tool-use in scientific domains. 

## Methodology

### Core Differences from ChemIQ
- **ChemIQ**: Direct model evaluation (knowledge recall, reasoning)
- **Ascendancy Trials**: Tool-augmented evaluation (tool selection, parameter setting, result interpretation)

### Approach to Start 
1. **Tool Selection**: Is the LLM correctly picking the correct tool to run?
2. **Results**: Are the results aligned with what we expect?

### A More Advanced Evaluation Approach (for later)
1. **Tool Orchestration**: Can the LLM identify which Rowan MCP tools are needed?
2. **Parameter Optimization**: Does the LLM set appropriate parameters for molecular simulations?
3. **Result Interpretation**: Can the LLM correctly interpret computational chemistry outputs?
4. **Iterative Refinement**: Does the LLM adapt its approach based on tool feedback?

## Data Structure

### Questions Format (`questions/`)
```jsonl
{
  "id": "ascendancy_001",
  "category": "molecular_design",
  "subcategory": "drug_optimization", 
  "difficulty": "intermediate",
  "question": "Design a molecule that...",
  "expected_tools": ["rdkit_analysis", "conformer_generation", "docking"],
  "evaluation_criteria": {
    "tool_selection": "Must use molecular docking",
    "parameter_accuracy": "Binding site coordinates within 2Å",
    "result_quality": "Binding affinity < -8.0 kcal/mol"
  },
  "reference_solution": {...}
}
```

### Response Format (`model_responses/`)
```json
{
  "model": "gpt-4o",
  "timestamp": "2024-01-01T00:00:00Z",
  "question_id": "ascendancy_001",
  "tool_calls": [
    {
      "tool": "rdkit_analysis",
      "parameters": {...},
      "result": {...},
      "evaluation": "correct|incorrect|partial"
    }
  ],
  "final_answer": "...",
  "success_metrics": {
    "tool_selection_accuracy": 0.95,
    "parameter_correctness": 0.87,
    "result_interpretation": 0.92,
    "overall_success": true
  }
}
```

## Contributing

Contributions are welcome: 
- Question design and validation
- New evaluation categories
- Tool integration improvements
