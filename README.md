# LabAgents

Large Language Model (LLM) agents are increasingly capable of using external tools via MCP to perform complex tasks. However, existing benchmarks rarely focus on life sciences research contexts or simulate tool-rich experimental environments.

**LabAgents** addresses this gap as a domain-specific benchmark for chemistry and biology research workflows, evaluating how well AI agents leverage MCP (Model Context Protocol) tools. It measures an agent's ability to:

1. **Select the right tools** from a chemistry/biology MCP suite
2. **Plan and execute multi-step** experimental workflows
3. **Deliver correct results** on scientific tasks

> *TL;DR: It tests how well agents can navigate through problems, just as a scientist would.*

---

## Quick Start

1. **Activate environment:**
   ```bash
   source .venv/bin/activate
   ```

2. **Run a question:**
   ```bash
   python openrouter_agent.py tier1_001 -m "openai/gpt-5"
   ```

3. **Batch evaluate all models for a question:**
   ```bash
   python llm_judge_evaluator.py tier1_001
   ```

## Models Evaluated

| Model | Provider | Type |
|-------|----------|------|
| **claude-4.1-opus** | Anthropic | Latest Opus model |
| **claude-4-sonnet** | Anthropic | Latest Sonnet model |
| **gpt-5** | OpenAI | Latest flagship model |
| **o3** | OpenAI | Reasoning model |
| **grok-4** | xAI | Latest model |
| **gemini-2.5-pro** | Google | Latest Gemini model |
| **deepseek-v3.1** | DeepSeek | Latest model |
| **grok-code-fast-1** | xAI | Fast coding model |

## Rowan MCP Tools

### Core Calculations
- `rowan_multistage_opt` - Multi-level geometry optimization with hierarchical methods
- `rowan_conformers` - Conformer generation and optimization
- `rowan_electronic_properties` - Electronic structure properties (orbitals, density, ESP)
- `rowan_spin_states` - Spin state calculations for different multiplicities
- `rowan_molecular_dynamics` - MD simulations with various ensembles

### Chemical Properties
- `rowan_pka` - pKa value predictions
- `rowan_redox_potential` - Oxidation/reduction potentials vs SCE
- `rowan_solubility` - Solubility predictions in multiple solvents
- `rowan_tautomers` - Tautomer enumeration and ranking
- `rowan_fukui` - Fukui indices for reactivity prediction

### Drug Discovery
- `rowan_admet` - ADME-Tox property predictions
- `rowan_descriptors` - Molecular descriptors for ML/QSAR
- `rowan_docking` - Protein-ligand docking with ML refinement

### Reaction Analysis
- `rowan_scan` - Potential energy surface scans (1D/2D)
- `rowan_scan_analyzer` - Extract key geometries from scans
- `rowan_irc` - Intrinsic reaction coordinate calculations

### Utilities
- `rowan_molecule_lookup` - PubChem lookup with caching
- `rowan_workflow_management` - Manage computational workflows
- `rowan_folder_management` - Organize calculations in folders
- `rowan_system_management` - Server utilities and information

## Benchmark Structure

### Tier 1: Basic Tool Selection
Simple, direct questions requiring selection of a single appropriate tool.

### Tier 2: Multi-Tool Orchestration
Tasks requiring workflow planning and independent calculations across multiple tools.

### Tier 3: Scientific Planning and Conditional Logic
Complex tasks where outputs from one workflow become inputs of another.

## Benchmark Questions

**16 computational chemistry tasks** across 3 tiers spanning basic tool use to complex multi-step workflows.

**[→ See All Questions](QUESTIONS.md)**

---

## Commands

### Run Questions
```bash
# Single question, single model
python openrouter_agent.py tier1_001 -m "openai/gpt-5"

# Single question, ALL 8 models
python openrouter_agent.py tier1_001 --all-models

# All questions in tier, single model
python openrouter_agent.py tier1 --model "anthropic/claude-opus-4.1"

# All questions in tier, ALL 8 models
python openrouter_agent.py tier1 --all-models
```

### Evaluate Results
```bash
# Evaluate all models for one question
python llm_judge_evaluator.py tier1_001

# Evaluate all models for tier3_004 (serotonin example)
python llm_judge_evaluator.py tier3_004

# Single log file
python llm_judge_evaluator.py --single logs/tier1_001/openai_gpt-5_timestamp.json
```

## Directory Structure

```
logs/{question_id}/{model}_{timestamp}.json     # Execution logs
evaluations/{question_id}/{model}_evaluation.* # Evaluation results
```

## Project Structure

```
labagents/
├── scripts/              # Auxiliary Python utilities
├── reflections/          # Analysis and evaluation insights
├── questions/            # Benchmark questions and documentation
├── logs/                 # Execution logs by question/model
├── evaluations/          # LLM-as-a-judge evaluation results
├── openrouter_agent.py   # Main evaluation script
└── llm_judge_evaluator.py # Evaluation analysis
```

## Requirements

- `.env` with `OPENROUTER_API_KEY`
- Rowan MCP server running at `/Users/katherineyenko/Desktop/sandbox/rowan-mcp`
- Activate virtual environment: `source .venv/bin/activate`
