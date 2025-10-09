# LabAgents

A domain-specific benchmark evaluating how well LLM agents leverage computational chemistry tools via MCP (Model Context Protocol). We tested 8+ models on 22 chemistry tasks requiring tool selection, workflow planning, and multi-step execution.

> *Can an AI agent reason like a scientist?*

---

## Table of Contents

1. [The Journey](#the-journey)
2. [Evaluation Results](#evaluation-results)
3. [What I Learned](#what-we-learned)
4. [Benchmark Design](#benchmark-design)
5. [Quick Start](#quick-start)
6. [Technical Details](#technical-details)

---

## The Journey

### Where It Started

I built the Rowan MCP server as a fun project to connect a model to external tools - no virtual environments, no package installations, but just a way to connect with external domain-specific tools.

### The Questions That Keep Me Up

Once I had the MCP running, I knew I'd eventually need to address my blind faith in Claude to pick out the right tools and use them correctly to solve chemical questions. Claude was helpful during development, but how do I know it's:
- Calling tools with the correct parameters?
- Getting answers that match what we'd see in the lab?
- Actually the best model for these tasks?

My first approach was knowingly naive - I gave all the models the same tools and prompts, ran them through some questions, and subjectively compared the outputs. No real method for evals, just vibes. 

### What I'm Still Learning

And I'm still figuring out the best way to evaluate. But I believe researchers will use different models for different tasks within the same pipeline. For example, in a single drug discovery workflow:
- Maybe Gemini 2.5 Pro is best at protein structure predictions,
- Maybe Claude is best at chemical property calculations, and
- Maybe ChatGPT is best at ADMET predictions

**How would we know? Where is this information consolidated?**

This project is my attempt to start answering these questions - and eventually build **BioArena**: a scientist-validated, domain-specific ranking system for life sciences AI.

### My Observations

**1. Models are getting better at tool use**
- Claude Sonnet 4: 88.4% weighted score (NEW #1!)
- All Claude models dominate top 3: Sonnet 4 (88.4%), Sonnet 4.5 (87.0%), Opus 4.1 (85.1%)
- Clear tier: Claude > GPT-5/Gemini > Grok/DeepSeek > o3

**2. Domain expertise is essential**
- tier1_001 was a deliberate trick question (drug NOT soluble in water)
- Models confidently reported solubility concentrations
- Judges didn't even catch this either; they need domain grounding too

**3. Reasoning ≠ Tool Execution**
- O3 reasons exceptionally well but struggles with tool selection
- Strong reasoning doesn't automatically translate to good agent performance

- **I still need human-labeled golden datasets for ground truth**

---

## Evaluation Results

### Overall Leaderboard (Weighted by Difficulty)

*Tier 1 = 1x weight, Tier 2 = 2x weight, Tier 3 = 4x weight*

| Rank | Model | Weighted Score | Evaluations |
|------|-------|---------------|-------------|
| 🥇 1 | Claude Sonnet 4 | 88.4% | 22/22 |
| 🥈 2 | Claude Sonnet 4.5 | 87.0% | 22/22 |
| 🥉 3 | Claude Opus 4.1 | 85.1% | 22/22 |
| 4 | GPT-5 | 69.9% | 22/22 |
| 5 | Gemini 2.5 Pro | 69.2% | 22/22 |
| 6 | Grok Code Fast 1 | 63.4% | 22/22 |
| 7 | DeepSeek v3.1 | 58.0% | 22/22 |
| 8 | Grok 4 Fast | 53.9% | 20/22 |
| 9 | o3 | 33.7% | 22/22 |

*Full results in [leaderboard/](leaderboard/)*

### Judge Comparison

I was using Claude for everything, including judging the results. To check for same-family bias, I added **Qwen 3 Max** as an independent judge (Qwen wasn't evaluated in the benchmark, so it has no stake in the results).

- **Claude Sonnet 4** (primary judge with web search)
- **Qwen 3 Max** (independent verification)

*Judge agreement analysis in [plots_comparison/](plots_comparison/)*

---

## What We Learned

### 1. Validation Methodology Evolution

**The LLM-as-Judge Pipeline:**
Following Hamel Husain's evaluation principles, we:
1. Created human-labeled golden datasets (in progress)
2. Held out test sets for unbiased validation
3. Measured judge performance against expert labels

**Key finding**: Web-search enabled judges perform better, but still miss domain-specific edge cases.

### 2. Judge Performance & Bias

Comparing 3 judges (Claude Sonnet 4, Qwen, GPT-5):
- **Agreement rate**: [To be analyzed from plots_comparison/]
- **Same-family bias**: [Evidence from cross-judge analysis]
- **Literature validation**: Web search dramatically improves correctness scoring

### 3. Model Capabilities

**Tool Selection**: Claude models dominate
- Sonnet 4.5: Best overall (90.7%)
- Opus 4.1: Most consistent (22/22 questions)
- GPT-5: Struggles with tool orchestration (63.6%)

**Reasoning vs Execution**:
- O3 has strong reasoning but poor tool selection
- Gemini balances both reasonably well (69.2%)

### 4. Next Steps

**Immediate priorities:**
- [ ] Create human-labeled golden dataset for all 22 questions
- [ ] Update Rowan MCP with latest tool improvements
- [ ] Detailed analysis of tier1_001 (trick question case study)
- [ ] Expand benchmark to protein structure and toxicity tasks

**Long-term vision: BioArena**
- Scientist-validated rankings across life sciences domains
- Community-driven evaluation with expert verification
- Domain-specific leaderboards (chemistry, biology, clinical)

---

## Benchmark Design

### Task Tiers

**Tier 1: Basic Tool Selection** (10 questions)
- Single-tool tasks testing tool selection accuracy
- Example: "Calculate the logP of aspirin"

**Tier 2: Multi-Tool Orchestration** (6 questions)
- Independent parallel workflows requiring planning
- Example: "Generate conformers AND calculate pKa for ibuprofen"

**Tier 3: Scientific Reasoning** (6 questions)
- Complex conditional logic and sequential dependencies
- Example: "Find the most stable tautomer, then calculate its properties"

**[→ See All Questions](QUESTIONS.md)**

### Evaluation Methodology

We used **LLM-as-Judge** evaluation with:
- **Web-search enabled judges** to validate against literature values
- **Multiple independent judges** (Claude, Qwen, GPT-5) to detect bias
- **Weighted scoring** (1x tier1, 2x tier2, 4x tier3) to emphasize complexity
- **3 dimensions**: Completion (0-2), Correctness (0-2), Tool Use (0-2)
- **Pass threshold**: 4/6 points

---

## Quick Start

### Run Agent on Questions

```bash
# Single question, single model
python agent_runner.py tier1_001 --model "openai/gpt-5"

# All questions in a tier
python agent_runner.py tier1 --model "anthropic/claude-sonnet-4.5"

# Specific model on all tiers
./run_missing_sonnet45.sh
```

### Evaluate with LLM Judge

```bash
# Evaluate all logs for a question
python scripts/run_all_missing_evals.py

# Generate leaderboard and plots
python leaderboard/update_leaderboard.py
python scripts/create_evaluation_plots.py
```

---

## Technical Details

### Models Evaluated

| Model | Provider | Type |
|-------|----------|------|
| Claude Opus 4.1 | Anthropic | Flagship reasoning |
| Claude Sonnet 4.5 | Anthropic | Latest balanced |
| Claude Sonnet 4 | Anthropic | Fast reasoning |
| GPT-5 | OpenAI | Latest flagship |
| o3 | OpenAI | Reasoning specialist |
| Gemini 2.5 Pro | Google | Multimodal flagship |
| DeepSeek v3.1 | DeepSeek | Open-source |
| Grok 4 Fast | xAI | Fast variant |

### Rowan MCP Tools (32 total)

**Core Calculations**: Geometry optimization, conformers, electronic properties, MD simulations

**Chemical Properties**: pKa, redox potential, solubility, tautomers, Fukui indices

**Drug Discovery**: ADMET prediction, descriptors, molecular docking

**Reaction Analysis**: PES scans, IRC calculations, TS optimization

**[→ Full Tool Documentation](https://docs.rowansci.com)**

---

### Directory Structure

```
labagents/
├── agent_runner.py           # Main agent execution script
├── llm_judge_evaluator.py    # LLM-as-judge evaluation
├── logs/                     # Agent execution logs
│   └── {question_id}/{model}/
├── evaluations/              # Judge evaluations (Claude Sonnet 4)
├── evaluations_qwen/         # Qwen judge evaluations
├── evaluations_gpt5/         # GPT-5 judge evaluations
├── leaderboard/              # Leaderboard CSVs
├── plots/                    # Visualization plots
├── plots_qwen/               # Qwen judge plots
├── plots_comparison/         # Cross-judge comparison
├── questions/                # Benchmark task definitions
└── scripts/                  # Utilities and automation
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
