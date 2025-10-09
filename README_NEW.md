# LabAgents

A domain-specific benchmark evaluating how well LLM agents leverage computational chemistry tools via MCP (Model Context Protocol). We tested 8+ frontier models on 22 chemistry tasks requiring tool selection, workflow planning, and multi-step execution.

> *Can AI agents reason like chemists? We put them to the test - twice.*

---

## Table of Contents

1. [The Journey](#the-journey)
2. [Evolution: V1 → V2](#evolution-v1--v2)
3. [Key Findings](#key-findings)
4. [Evaluation Results](#evaluation-results)
5. [Benchmark Design](#benchmark-design)
6. [Quick Start](#quick-start)
7. [Technical Details](#technical-details)

---

## The Journey

### Why This Matters: Package Hell for Scientists

As scientists, we don't want to deal with dependency conflicts, environment setup, or wrestling with installation scripts. We want to focus on **doing science**. This philosophy drove the creation of the Rowan MCP server - a single interface to computational chemistry tools that "just works."

### The Question: How Do We Know It's Right?

I primarily used Claude during MCP development. But a critical question emerged: **How do we validate the outputs?** How do we benchmark this? How do we know Claude is selecting the right tools and arriving at correct answers?

### The Hypothesis: Model-Specific Strengths

What if different models produce different answers using different tools - but both are valid approaches? More importantly: **What if models have domain-specific strengths we don't know about?**

- What if GPT-5 excels at protein structure tasks?
- What if Claude dominates chemical reasoning?
- What if Grok is uniquely good at clinical toxicity predictions?

**How would we know? Where is this information consolidated?**

This benchmark is the first step toward answering these questions - and eventually building **BioArena**: a scientist-validated, domain-specific ranking system for life sciences AI.

---

## Evolution: V1 → V2

### Version 1: The First Attempt (September 2024)

**What I Built:**
- 10 questions (5 Tier 2, 5 Tier 3)
- Binary tool-use evaluation (did it call expected functions?)
- Claude Sonnet as LLM-as-judge for correctness
- Simple weighted scoring (Tier 2 = 2pts, Tier 3 = 4pts)

**Key Results:**
- GPT-5 led in correctness
- Claude Sonnet 4 excelled at tool selection
- Claude Opus 4.1 gave correct pKa without calling pKa tool (!)

**What I Learned:**

> *"This is... very far from complete."*

1. **Logging was inconsistent** - Sometimes captured all tool calls, sometimes missed crucial interactions
2. **Models took shortcuts** - Opus correctly predicted pKa without using the pKa tool
3. **Evaluation was too simple** - Binary scoring missed nuance in scientific reasoning
4. **No ground truth validation** - Judges didn't validate against literature

**The "Aha" Moment:**
> *Models can arrive at correct answers without using expected tools. This isn't wrong - it's revealing model capabilities we didn't anticipate.*

---

### Version 2: Learning from Mistakes (October 2024)

**What Changed:**

| Aspect | V1 | V2 | Why It Matters |
|--------|----|----|---------------|
| **Questions** | 10 (Tier 2-3 only) | 22 (Tier 1-3) | Added Tier 1 for tool selection baseline |
| **Logging** | Inconsistent | Full execution trace | See *everything* - parameters, results, timing |
| **Judge Grounding** | No external validation | **Web search enabled** | Judges validate against literature |
| **Judge Bias** | Single judge (Claude) | **3 judges** (Claude, Qwen, GPT-5) | Detect same-family bias |
| **Scoring** | Binary tool-use | **3 dimensions** (0-2 each) | Completion + Correctness + Tool Use |
| **Weighting** | Arbitrary (2x, 4x) | **Tier-based** (1x, 2x, 4x) | Reflects true difficulty |
| **Evaluation Method** | Post-hoc batch | Structured rubric + citations | Auditable, reproducible |

**Inspired by Hamel Husain's Eval Principles:**
1. Get human labels (in progress - golden datasets)
2. Hold out test sets for unbiased validation
3. Measure judge performance against expert labels

**Critical Improvements:**

**🔍 Web-Search Enabled Judges**
- Judges now validate against PubChem, literature databases
- Extract actual experimental values vs "trusting" model outputs
- **But still miss edge cases** (see tier1_001 trick question)

**📊 Multi-Judge Validation**
- Claude Sonnet 4 (primary, web-search)
- Qwen 3 Max (independent verification)
- GPT-5 (OpenAI perspective)
- Cross-judge agreement analysis in [plots_comparison/](plots_comparison/)

**📝 Comprehensive Logging**
- Every tool call with parameters
- All intermediate results
- Execution timeline
- Cost tracking per API call

---

## Key Findings

### 1. Models Are Getting Better (But Differently)

**V1 Results (Sep 2024):**
- GPT-5: Best correctness
- Claude Sonnet 4: Best tool selection
- Opus: Mysterious shortcuts

**V2 Results (Oct 2024):**
- **Claude Sonnet 4.5**: 90.7% weighted score, 100% pass rate
- **Claude Sonnet 4**: 86.0%, 95% pass rate
- **Claude Opus 4.1**: 85.1%, 95.5% pass rate
- **Gemini 2.5 Pro**: 69.2%, 81.8% pass rate
- **GPT-5**: 63.6%, 60% pass rate

**The Shift:** Claude models now dominate both correctness AND tool use. GPT-5 dropped significantly.

### 2. Reasoning ≠ Tool Execution

**O3's Paradox:**
- Exceptional reasoning capabilities
- Poor tool selection and workflow execution
- **Insight**: Strong reasoning doesn't automatically translate to good agent performance

### 3. Domain Expertise Is Still Essential

**The tier1_001 Trick Question:**
- Question: "Calculate water solubility of [specific drug]"
- **Truth**: Drug is NOT water-soluble
- **What happened**: Models confidently reported solubility concentrations
- **Judge performance**: Rarely caught this error, even with web search

**Lesson**: LLM judges need more than web search - they need domain-specific validation frameworks.

### 4. Judge Bias Exists (But We Can Measure It)

Comparing Claude vs Qwen vs GPT-5 judges:
- Different literature values found for same molecule
- Varying score distributions
- Evidence of potential same-family bias (analysis in progress)

**The Fix**: Multiple independent judges + human expert validation

---

## Evaluation Results

### Overall Leaderboard (Weighted by Difficulty)

*Tier 1 = 1x weight, Tier 2 = 2x weight, Tier 3 = 4x weight*

| Rank | Model | Weighted Score | Pass Rate | Evaluations |
|------|-------|---------------|-----------|-------------|
| 🥇 1 | Claude Sonnet 4.5 | 90.7% | 100% | 18/22 |
| 🥈 2 | Claude Sonnet 4 | 86.0% | 95% | 20/22 |
| 🥉 3 | Claude Opus 4.1 | 85.1% | 95.5% | 22/22 |
| 4 | Gemini 2.5 Pro | 69.2% | 81.8% | 22/22 |
| 5 | GPT-5 | 63.6% | 60% | 20/22 |
| 6 | Grok Code Fast 1 | 59.9% | 47.6% | 21/22 |
| 7 | DeepSeek v3.1 | 51.9% | 37% | 27/22 |
| 8 | Grok 4 Fast | 54.7% | 28% | 25/22 |
| 9 | O3 | 33.7% | 13.6% | 22/22 |

*Full results in [leaderboard/](leaderboard/)*

### Judge Comparison

We evaluated with **3 different LLM judges** to detect potential same-family bias:

- **Claude Sonnet 4** (primary judge with web search)
- **Qwen 3 Max** (independent verification)
- **GPT-5** (OpenAI perspective)

**Key Findings:**
- Judges found different literature values for same molecules
- Agreement rate: [Analysis in progress]
- Evidence of same-family bias: [To be determined]

*Judge agreement analysis in [plots_comparison/](plots_comparison/)*

---

## Benchmark Design

### Task Tiers

**Tier 1: Basic Tool Selection** (10 questions)
- Single-tool tasks testing tool selection accuracy
- Example: "Calculate the logP of aspirin"
- Tests: Can models identify the right tool for the job?

**Tier 2: Multi-Tool Orchestration** (6 questions)
- Independent parallel workflows requiring planning
- Example: "Generate conformers AND calculate pKa for ibuprofen"
- Tests: Can models plan and execute parallel workflows?

**Tier 3: Scientific Reasoning** (6 questions)
- Complex conditional logic and sequential dependencies
- Example: "Find the most stable tautomer, then calculate its properties"
- Tests: Can models handle scientific decision-making?

**[→ See All Questions](QUESTIONS.md)**

### Evaluation Methodology

**V2 LLM-as-Judge Pipeline:**
- ✅ **Web-search enabled** - Validates against literature values
- ✅ **Multiple judges** - Claude, Qwen, GPT-5 for bias detection
- ✅ **Weighted scoring** - 1x tier1, 2x tier2, 4x tier3
- ✅ **3 dimensions** - Completion (0-2), Correctness (0-2), Tool Use (0-2)
- ✅ **Citation tracking** - Judges cite sources with quotes
- ✅ **Pass threshold** - 4/6 points required

**Rubric Example (Correctness):**
```
STEP 1: Search for literature values
  → Search: "[molecule name] [property] experimental value"

STEP 2: Extract values and compare
  → Agent's value: X
  → Literature value: Y (from [source URL])
  → Absolute error: |X - Y|

STEP 3: Score based on error magnitude
  ✓ pKa: within ±0.5 units = 2/2
  ✓ logP: within ±0.3 units = 2/2
  ✓ Solubility: within ±50% = 2/2
```

---

## What We Learned

### 1. The Evolution of Evaluation

**V1 Mistakes:**
- Binary scoring too simplistic
- No literature validation
- Single judge (potential bias)
- Inconsistent logging

**V2 Improvements:**
- Granular rubrics (0-2 per dimension)
- Web-search for validation
- Multi-judge comparison
- Full execution traces

**Still Missing:**
- Human-labeled golden datasets
- Ground truth validation framework
- Domain expert review

### 2. Model Capabilities Evolved

**September 2024:**
- GPT-5 led in correctness
- Models took mysterious shortcuts
- Tool selection was hit-or-miss

**October 2024:**
- Claude models dominate comprehensively
- Tool selection is much more reliable
- But reasoning models (O3) still struggle with execution

### 3. The Trick Question Reveals Limits

**tier1_001: The Deliberate Trap**
- Asked for water solubility of a water-insoluble drug
- **Models**: Confidently reported concentrations
- **Judges**: Rarely caught the error (even with web search!)

**Implication**: We need domain-expert validation, not just literature lookup.

### 4. Next Steps

**Immediate Priorities:**
- [ ] Create human-labeled golden dataset for all 22 questions
- [ ] Complete judge bias analysis (cross-judge comparison)
- [ ] Write detailed case study on tier1_001 trick question
- [ ] Update Rowan MCP with latest tool improvements
- [ ] Expand to Tier 1 questions (10 more for baseline)

**Medium-Term:**
- [ ] Protein structure prediction tasks
- [ ] Clinical toxicity prediction benchmarks
- [ ] Drug discovery workflow evaluation

**Long-Term Vision: BioArena**
- Scientist-validated rankings across life sciences domains
- Community-driven evaluation with expert verification
- Domain-specific leaderboards (chemistry, biology, clinical)
- LMArena-style platform for head-to-head comparisons

---

## Quick Start

### Run Agent on Questions

```bash
# Single question, single model
python agent_runner.py tier1_001 --model "openai/gpt-5"

# All questions in a tier
python agent_runner.py tier1 --model "anthropic/claude-sonnet-4.5"

# Run missing questions for a model
./run_missing_sonnet45.sh
```

### Evaluate with LLM Judge

```bash
# Run evaluations with default judge (GPT-5)
python scripts/run_all_missing_evals.py

# Use specific judge
python scripts/run_all_missing_evals.py --judge "qwen/qwen3-max"

# Run multiple judges in parallel
python run_all_judges_parallel.py --judges gpt5 gemini qwen claude
```

### Generate Leaderboard & Plots

```bash
# Update leaderboard with weighted scoring
python leaderboard/update_leaderboard.py

# Generate visualizations
python scripts/create_evaluation_plots.py

# Compare judges
python create_judge_comparison_plots.py
```

---

## Technical Details

### Models Evaluated

| Model | Provider | Type | Notes |
|-------|----------|------|-------|
| Claude Opus 4.1 | Anthropic | Flagship reasoning | Most consistent (22/22) |
| Claude Sonnet 4.5 | Anthropic | Latest balanced | Best overall (90.7%) |
| Claude Sonnet 4 | Anthropic | Fast reasoning | Strong tool use |
| GPT-5 | OpenAI | Latest flagship | Dropped from V1 (#1 → #5) |
| O3 | OpenAI | Reasoning specialist | Strong reasoning, poor tools |
| Gemini 2.5 Pro | Google | Multimodal flagship | Balanced performance |
| DeepSeek v3.1 | DeepSeek | Open-source | Moderate performance |
| Grok 4 Fast | xAI | Fast variant | Lower accuracy |

### Rowan MCP Tools (32 total)

**Core Calculations**: Geometry optimization, conformers, electronic properties, MD simulations

**Chemical Properties**: pKa, redox potential, solubility, tautomers, Fukui indices

**Drug Discovery**: ADMET prediction, descriptors, molecular docking

**Reaction Analysis**: PES scans, IRC calculations, TS optimization

**[→ Full Tool Documentation](https://docs.rowansci.com)**

### Directory Structure

```
labagents/
├── agent_runner.py           # Main agent execution script
├── llm_judge_evaluator.py    # LLM-as-judge evaluation
├── logs/                     # Agent execution logs
│   └── {question_id}/{model}/
├── evaluations/              # Claude Sonnet 4 judge
├── evaluations_qwen/         # Qwen judge
├── evaluations_gpt5/         # GPT-5 judge
├── leaderboard/              # Weighted leaderboard CSVs
├── plots/                    # Sonnet judge plots
├── plots_qwen/               # Qwen judge plots
├── plots_comparison/         # Cross-judge analysis
├── questions/                # Benchmark tasks
├── reflections/              # V1 analysis & learnings
└── scripts/                  # Automation utilities
```

### Requirements

- Python 3.13+
- `.env` with `OPENROUTER_API_KEY`
- Rowan MCP server running locally
- Dependencies: `openai`, `anthropic`, `matplotlib`, `seaborn`

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

---

## References

**V1 Evaluation Framework:**
- [V1 Reflections](reflections/labagents_v1_reflections.md) - Original evaluation methodology and findings

**Evaluation Best Practices:**
- Hamel Husain's [LLM Evaluation Guide](https://hamel.dev/blog/posts/evals/)

**Chemistry Benchmarks:**
- ChemIQ: Assessing Chemical Intelligence of LLMs
- ChemBench: Framework for evaluating chemistry reasoning
- ChemCrow: LLM chemistry agent (predecessor work)

---

## Acknowledgments

Built with inspiration from:
- LMArena's community evaluation model
- Hamel Husain's evaluation principles
- The computational chemistry community's feedback

**Future Vision**: BioArena - where scientists validate AI capabilities through real-world challenges.
