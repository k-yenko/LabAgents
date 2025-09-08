# LabAgents

Large Language Model (LLM) agents are increasingly capable of using external tools via MCP to perform complex tasks. However, existing benchmarks rarely focus on life sciences research contexts or simulate tool-rich experimental environments. LabAgents addresses this gap as a domain-specific benchmark for chemistry and biology research workflows, evaluating how well AI agents leverage MCP (Model Context Protocol) tools. It measures an agent's ability to:

1. Select the right tools from a chemistry/biology MCP suite
2. Plan and execute multi-step experimental workflows
3. Deliver correct results on scientific tasks

TL;DR, it tests how well agents can navigate through problems, just as a scientist would.

---

## Getting Started

### Starting the Eval Tracker Server

```bash
source venv/bin/activate && python3 eval_tracker_server.py
```


## Models Being Tested

- **claude-4.1-opus** - Latest Anthropic Opus model
- **claude-4-sonnet** - Latest Anthropic Sonnet model
- **gpt-5** - Latest OpenAI model
- **o3** - OpenAI's reasoning model
- **grok-4** - xAI's latest model
- **gemini-2.5-pro** - Google's latest Gemini model
- **deepseek-v3.1** - DeepSeek's latest model
- **grok-code-fast-1** - xAI's fast coding model

## Available Rowan MCP Tools

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

## Benchmark Tiers

### Tier 1: Basic Tool Selection
Simple, direct questions requiring selection of a single appropriate tool.

### Tier 2: Multi-Tool Orchestration
Tasks requiring workflow planning and independent calculations across multiple tools. 

### Tier 3: Scientific Planning and Conditional Logic
Complex tasks where outputs from one workflow become inputs of another.

## Example Questions:

**Tier 1:** "Calculate the ADMET properties of semaglutide to assess its pharmacokinetic profile."

**Tier 2:** "Generate conformers of semaglutide and identify the lowest energy structure, then calculate its solubility in water at physiological pH."

**Tier 3:** "Analyze the binding of semaglutide to the GLP-1 receptor, optimize the docked pose, then compare how modifications to the fatty acid chain length affect both binding affinity and predicted half-life."

## Current Questions Being Tested

**Tier 2 (5 questions):**
  - Ibuprofen conformers + pKa/logP - Major NSAID, widely studied
  - Caffeine descriptors + solubility - Model drug compound
  - Morphine tautomers + pKa - Important opioid pharmacology
  - Paracetamol electronic structure - Essential drug, HOMO/LUMO analysis
  - Caffeine temperature solubility - Temperature-dependent solubility studies

**Tier 3 (5 questions):**
  - Warfarin tautomers - Critical anticoagulant research
  - Acetaminophen metabolic sites - Drug metabolism studies
  - Atorvastatin docking - Major statin, structure-activity relationships
  - Serotonin reaction pathways - Neurotransmitter research
  - Taxol ADMET analysis - Major cancer drug, BBB permeability
