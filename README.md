# Agentic Scientific Tool Selection Benchmark 

A comprehensive benchmark system for evaluating tool selection and chaining capabilities across different AI agents and computational chemistry/biology tools.

## Models Being Tested

- **GPT-5** - Latest OpenAI model
- **Claude Sonnet** - Latest Anthropic Sonnet model  
- **Claude Opus** - Latest Anthropic Opus model
- **O3** - OpenAI's reasoning model
- **DeepSeek** - DeepSeek's latest model
- **Grok** - xAI's model
- **Qwen** - Alibaba's latest model

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

### Tier 2: Tool Chaining
Questions requiring sequential use of multiple tools where output from one feeds into the next.

### Tier 3: Complex Workflows
Advanced scenarios requiring conditional logic, multiple tool chains, and decision-making based on intermediate results.

## Example Questions

**Tier 1:** "Calculate the ADMET properties of semaglutide to assess its pharmacokinetic profile."

**Tier 2:** "Generate conformers of semaglutide and identify the lowest energy structure, then calculate its solubility in water at physiological pH."

**Tier 3:** "Analyze the binding of semaglutide to the GLP-1 receptor, optimize the docked pose, then compare how modifications to the fatty acid chain length affect both binding affinity and predicted half-life."
