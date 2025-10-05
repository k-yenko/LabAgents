# Rigorous Evaluation Framework: Complete Implementation Plan

*Comprehensive plan for transforming LLM-as-judge into a validated, defensible evaluation system*

---

## 📊 Current State & Vision

### Where We Are
- ✅ **Working LLM judge** - Automated scoring across 3 dimensions (completion, correctness, tool use)
- ✅ **Web search enabled** - Judge can validate against real literature (JUST IMPLEMENTED!)
- ✅ **Structured logging** - Full execution traces for 22 chemistry questions across 9 models
- ❌ **No validation** - Same-family bias, no expert calibration, no ground truth
- ❌ **Limited insights** - Can see failures but not why they happen

### Where We're Going
- **Validated system** - Expert-calibrated judge with known accuracy (Cohen's kappa > 0.6)
- **Multi-perspective** - Ensemble judges to reduce bias
- **Ground truth** - Reference database with known correct answers
- **Error taxonomy** - Every failure categorized and analyzed
- **Actionable insights** - Clear path from evaluation → improvement
- **Sustainable process** - Weekly review cycle, continuous refinement

---

## 🎯 Core Principles

1. **Evals are a process, not just a tool** - Workflow > single metric
2. **Human-in-the-loop is critical** - LLM assists experts, doesn't replace them
3. **Error analysis > raw scores** - Understand WHY models fail
4. **Side-by-side comparison > absolute scores** - Relative strengths matter
5. **Start simple, then scale** - Fix basics before adding complexity

---

## 🏗️ 7-Phase Implementation Plan

### **Phase 1: Web Search Validation** ✅ COMPLETED
*Enable real literature validation for correctness scoring*

**What We Did:**
- Implemented OpenRouter `:online` suffix for web search
- Judge now searches PubChem, chemistry databases, and literature
- Extracts citations and quotes from search results
- Saves citations in evaluation JSON for traceability

**Results:**
- Judge can validate answers against experimental values
- Real URLs cited (e.g., PMC articles, PubChem entries)
- Objective correctness scoring based on literature
- Example: Caught 4400% error in remdesivir solubility prediction

**Cost:** ~$0.02 per evaluation (~$4 for 200 evaluations)

**Evidence It Works:**
```json
{
  "web_citations": [
    {
      "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7894405/",
      "title": "A mechanism‐based pharmacokinetic model of remdesivir...",
      "content": "aqueous solubility 0.339 mg/mL | Remdesivir has low aqueous solubility"
    }
  ]
}
```

---

### **Phase 2: Judge Prompt Improvements** ⏱️ 3-4 hours
*Fix basic issues before adding complexity*

**Quick Wins (2-3 hours):**

#### **2.1 Add Concrete Scoring Examples** ⏱️ 45 min
**Problem:** Rubric too vague - "reasonable range" means different things

**Implementation:**
```python
# In create_evaluation_prompt(), update CORRECTNESS section:

2. CORRECTNESS (0-2):
   **You have web search access - USE IT to validate answers against literature!**

   2/2 - Accurate computational result
       Examples from calibration set:
       ✓ pKa of acetic acid: 4.5-5.0 (literature: 4.76) ✓
       ✓ logP of aspirin: 1.0-1.4 (literature: 1.19) ✓
       ✓ Used appropriate DFT method (B3LYP or similar) ✓

   1/2 - Partially correct
       Examples:
       ⚠ pKa off by 0.3-1.0 units but method was sound
       ⚠ Right general approach but computational error

   0/2 - Incorrect or no computation
       Examples:
       ✗ pKa off by >1.0 unit (>20% error)
       ✗ Used web search to FIND answer instead of calculating
       ✗ Fundamental chemistry error
       ✗ No numerical result provided

   **Use web search to find experimental values and cite them!**
```

**Why:** Reduces variance, more consistent scoring

---

#### **2.2 Provide Full Execution Context** ⏱️ 1 hour
**Problem:** Judge only sees summary, can't evaluate methodology

**Implementation:**
```python
def extract_log_summary(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced summary with full execution trace"""

    # Build detailed tool trace
    tool_trace = []
    for idx, call in enumerate(log_data.get("tool_calls", [])):
        tool_trace.append({
            "step": idx + 1,
            "tool": call.get("tool_name", "unknown"),
            "parameters": call.get("parameters", {}),
            "result_preview": str(call.get("result", ""))[:300],  # First 300 chars
            "success": call.get("success", False),
            "execution_time_ms": call.get("execution_time_ms", 0)
        })

    return {
        # Existing fields
        "question_id": log_data.get("question_id"),
        "user_question": log_data.get("user_question"),
        "final_answer": log_data.get("final_answer", ""),

        # NEW: Full execution trace
        "tool_execution_trace": tool_trace,
        "workflow_sequence": [call["tool_name"] for call in log_data.get("tool_calls", [])],

        # Existing metrics
        "total_tool_calls": len(tool_trace),
        "tool_success_rate": sum(1 for t in tool_trace if t["success"]) / max(len(tool_trace), 1),
        "total_time_minutes": log_data.get("total_time_ms", 0) / (1000 * 60)
    }

def create_evaluation_prompt(self, log_summary: Dict[str, Any]) -> str:
    """Enhanced prompt with execution details"""

    # Format tool trace
    tool_trace_str = "\n".join([
        f"  {t['step']}. {t['tool']}({json.dumps(t['parameters'])}) → "
        f"{'✓ Success' if t['success'] else '✗ Failed'} ({t['execution_time_ms']}ms)"
        for t in log_summary.get("tool_execution_trace", [])
    ])

    return f"""You are an expert evaluator for AI agents performing computational chemistry tasks.

TASK: {log_summary['user_question']}

AGENT EXECUTION TRACE:
{tool_trace_str}

WORKFLOW SEQUENCE: {' → '.join(log_summary.get('workflow_sequence', []))}

FINAL ANSWER:
{log_summary['final_answer']}

[... rest of rubric ...]
"""
```

**Why:** Judge can now evaluate HOW agent computed, not just the final answer

---

#### **2.3 Clarify Completion Criteria** ⏱️ 30 min
**Problem:** Ambiguous - does completion mean claimed or actual?

**Implementation:**
```python
1. COMPLETION (0-2):
   Score based on OBJECTIVE task completion. Check the execution trace - don't trust what the agent claims!

   2/2 - Verifiably completed the computational workflow
       ✓ Required tools were executed successfully
       ✓ Calculation reached completion status
       ✓ Results were retrieved and presented
       ✓ Look at tool trace, not just final message!

   1/2 - Partial completion
       ⚠ Started calculation but didn't finish
       ⚠ Missing intermediate steps
       ⚠ Workflow incomplete or timed out

   0/2 - Did not complete
       ✗ No calculation performed
       ✗ Gave up before starting
       ✗ Critical tool failures prevented completion

   **IMPORTANT:** A model can complete the workflow (score 2) but still get the
   wrong answer (correctness 0). This distinction identifies overconfident models.
```

**Why:** Clear objective criteria, tracks model self-awareness

---

#### **2.4 Add Error Category Detection** ⏱️ 1 hour
**Problem:** Failures not categorized, can't identify patterns

**Implementation:**
```python
# Add to evaluation prompt:

ERROR CATEGORIZATION (if total score < 4):
Identify the primary failure mode:

- **METHODOLOGY**: Wrong computational method chosen (e.g., used semiempirical when DFT required)
- **EXECUTION**: Tool selection or parameter errors (e.g., wrong SMILES, bad workflow submission)
- **INTERPRETATION**: Misread results or unit errors (e.g., reported pKa as Ka)
- **NUMERICAL**: High computational error despite right method (e.g., 2+ units off)
- **INCOMPLETE**: Didn't finish the task (e.g., timeout, gave up)
- **CHEATING**: Used web search to find answer instead of computing (auto-fail)

Format your response:
<error_category>
Primary Error: [METHODOLOGY/EXECUTION/INTERPRETATION/NUMERICAL/INCOMPLETE/CHEATING]
Explanation: [1-2 sentences explaining why this category]
</error_category>
```

**Update parser:**
```python
def parse_judge_response(self, response: str, log_summary: Dict[str, Any], citations: List[Dict[str, str]] = None):
    # ... existing parsing ...

    # Extract error category
    error_match = re.search(r'<error_category>(.*?)</error_category>', response, re.DOTALL)
    error_category = None
    error_explanation = None

    if error_match:
        error_text = error_match.group(1).strip()
        primary_match = re.search(r'Primary Error:\s*(\w+)', error_text)
        explain_match = re.search(r'Explanation:\s*(.+)', error_text, re.DOTALL)

        error_category = primary_match.group(1) if primary_match else None
        error_explanation = explain_match.group(1).strip() if explain_match else None

    return ChemistryEvaluation(
        # ... existing fields ...
        error_category=error_category,
        error_explanation=error_explanation
    )
```

**Update dataclass:**
```python
@dataclass
class ChemistryEvaluation:
    # ... existing fields ...
    error_category: str = None  # METHODOLOGY, EXECUTION, etc.
    error_explanation: str = None  # Why this category
```

**Why:** Automatic error categorization enables pattern analysis

---

### **Phase 3: Ground Truth Database** ⏱️ 1-2 days
*Build reference values for objective validation*

#### **3.1 Create Reference Database** ⏱️ 4-6 hours

**Implementation:**
```python
# data/ground_truth.json

{
  "tier1_001": {
    "question": "Calculate aqueous solubility of remdesivir",
    "molecule": "remdesivir",
    "smiles": "CCC(CC)COC(=O)C(C)NP(=O)(OCC1C(C(C(O1)N2C=CC(=O)NC2=O)O)O)OC3=CC=CC=C3",
    "property": "solubility",
    "expected_value": 0.339,
    "unit": "mg/mL",
    "acceptable_range": [0.2, 0.5],
    "tolerance_percent": 30,
    "literature_source": "doi:10.1128/AAC.00424-20",
    "experimental_value": 0.339,
    "computational_notes": "FastSolv ML model typically accurate within ±50% for drug-like molecules",
    "common_errors": [
      "Confusing with formulated concentration (5 mg/mL with cyclodextrin)",
      "Using gas phase instead of aqueous",
      "Wrong protonation state"
    ]
  },

  "tier1_002": {
    "question": "Calculate pKa of acetic acid",
    "molecule": "acetic acid",
    "smiles": "CC(=O)O",
    "property": "pka",
    "expected_value": 4.76,
    "unit": "pKa units",
    "acceptable_range": [4.5, 5.0],
    "tolerance_percent": 5,
    "literature_source": "doi:10.1021/cr00032a009",
    "experimental_value": 4.76,
    "computational_notes": "DFT B3LYP/6-31G* typically within ±0.3 pKa units",
    "common_errors": [
      "Confusing Ka with pKa",
      "Not accounting for solvent (water)",
      "Using gas phase calculation"
    ]
  },

  "tier2_001": {
    "question": "Calculate logP of aspirin",
    "molecule": "aspirin",
    "smiles": "CC(=O)Oc1ccccc1C(=O)O",
    "property": "logP",
    "expected_value": 1.19,
    "unit": "logP",
    "acceptable_range": [1.0, 1.4],
    "tolerance_percent": 15,
    "literature_source": "PubChem CID 2244",
    "experimental_value": 1.19,
    "computational_notes": "XLogP3 or similar methods accurate within ±0.3 units",
    "common_errors": [
      "Using ionized form instead of neutral",
      "Wrong tautomer",
      "Confusing logP with logD"
    ]
  }

  // ... complete all 22 questions
}
```

**Load in evaluator:**
```python
class ComputationalChemistryJudge:
    def __init__(self, openrouter_api_key: str, judge_model: str = "anthropic/claude-sonnet-4",
                 output_dir: str = "evaluations", enable_web_search: bool = True):
        self.client = OpenAI(...)
        self.judge_model = judge_model
        self.output_dir = output_dir
        self.enable_web_search = enable_web_search

        # Load ground truth
        self.ground_truth = self.load_ground_truth()

    def load_ground_truth(self) -> Dict[str, Any]:
        """Load ground truth reference values"""
        gt_path = "data/ground_truth.json"
        if os.path.exists(gt_path):
            with open(gt_path, 'r') as f:
                return json.load(f)
        return {}

    def create_evaluation_prompt(self, log_summary: Dict[str, Any]) -> str:
        question_id = log_summary.get("question_id")

        # Get ground truth if available
        ground_truth_info = ""
        if question_id in self.ground_truth:
            gt = self.ground_truth[question_id]
            ground_truth_info = f"""
REFERENCE VALUES (for validation):
This question involves: {gt['molecule']}
Expected value: {gt['expected_value']} {gt['unit']} (±{gt['tolerance_percent']}%)
Acceptable range: {gt['acceptable_range'][0]} - {gt['acceptable_range'][1]}
Literature source: {gt['literature_source']}

Use web search to verify these values and compare agent's result.
"""

        return f"""You are an expert evaluator for AI agents performing computational chemistry tasks.

TASK: {log_summary['user_question']}

{ground_truth_info}

[... rest of prompt ...]
"""
```

**Why:** Objective validation, no guessing about correctness

---

#### **3.2 Automated Validation** ⏱️ 2-3 hours

**Implementation:**
```python
def validate_against_ground_truth(log_file_path: str) -> Dict[str, Any]:
    """Automated validation against ground truth"""

    with open(log_file_path, 'r') as f:
        log_data = json.load(f)

    question_id = log_data.get("question_id")

    # Load ground truth
    with open("data/ground_truth.json", 'r') as f:
        ground_truth = json.load(f)

    if question_id not in ground_truth:
        return {"validation_status": "no_ground_truth"}

    gt = ground_truth[question_id]

    # Extract numerical answer from agent
    agent_answer = extract_numerical_value(log_data.get("final_answer", ""))

    if agent_answer is None:
        return {
            "validation_status": "no_numerical_answer",
            "auto_correctness_score": 0,
            "confidence": "high"
        }

    # Calculate error
    expected = gt["expected_value"]
    error = abs(agent_answer - expected)
    percent_error = (error / expected) * 100
    in_range = gt["acceptable_range"][0] <= agent_answer <= gt["acceptable_range"][1]

    # Auto-score
    if in_range:
        auto_score = 2  # Perfect
        confidence = "high"
    elif percent_error <= gt.get("tolerance_percent", 10):
        auto_score = 1  # Close
        confidence = "high"
    elif percent_error <= gt.get("tolerance_percent", 10) * 2:
        auto_score = 1  # Borderline
        confidence = "medium"
    else:
        auto_score = 0  # Wrong
        confidence = "high"

    return {
        "validation_status": "validated",
        "agent_answer": agent_answer,
        "expected_answer": expected,
        "error_absolute": error,
        "error_percent": percent_error,
        "in_acceptable_range": in_range,
        "auto_correctness_score": auto_score,
        "confidence": confidence,
        "literature_source": gt.get("literature_source"),
        "ground_truth": gt
    }

def extract_numerical_value(text: str) -> float:
    """Extract numerical value from text"""
    import re

    # Common patterns for chemistry values
    patterns = [
        r'pKa\s*[=:]\s*([\d.]+)',
        r'logP\s*[=:]\s*([\d.]+)',
        r'solubility\s*[=:]\s*([\d.]+)',
        r'([\d.]+)\s*(?:mg/mL|kcal/mol|kJ/mol|Å)',
        r'(?:is|=|:)\s*([\d.]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except:
                continue

    return None
```

**Why:** Fast, objective validation for clear-cut cases

---

#### **3.3 Hybrid Scoring** ⏱️ 1-2 hours

**Implementation:**
```python
async def evaluate_with_hybrid_scoring(log_file_path: str, output_dir: str = "evaluations"):
    """Combine automated validation + LLM judge"""

    # 1. Automated validation
    auto_validation = validate_against_ground_truth(log_file_path)

    # 2. LLM judge evaluation
    evaluator = ComputationalChemistryJudge(
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        enable_web_search=True
    )
    llm_eval = await evaluator.evaluate_log(log_file_path)

    # 3. Combine intelligently
    if auto_validation.get("validation_status") == "validated":
        if auto_validation["confidence"] == "high":
            # Trust automated for correctness
            final_eval = {
                **llm_eval.__dict__,
                "correctness_score": auto_validation["auto_correctness_score"],
                "correctness_source": "automated",
                "auto_validation": auto_validation,
                "llm_correctness_score": llm_eval.correctness_score,  # Keep for comparison
            }
        else:
            # Low confidence - use LLM but include auto validation
            final_eval = {
                **llm_eval.__dict__,
                "correctness_source": "llm_judge",
                "auto_validation": auto_validation,
                "needs_expert_review": True
            }
    else:
        # No ground truth - rely on LLM + web search
        final_eval = {
            **llm_eval.__dict__,
            "correctness_source": "llm_web_search",
            "auto_validation": auto_validation
        }

    return final_eval
```

**Why:** Best of both worlds - automated when possible, LLM for nuance

---

### **Phase 4: Multi-Judge Ensemble** ⏱️ 1 day
*Reduce same-family bias with diverse perspectives*

#### **4.1 Ensemble Implementation** ⏱️ 4-6 hours

**Problem:** Claude judge favors Claude models (95-100% vs 13-82% for others)

**Implementation:**
```python
# scripts/ensemble_judge.py

JUDGE_MODELS = [
    "anthropic/claude-sonnet-4",      # Claude perspective
    "openai/gpt-4o",                   # OpenAI perspective
    "google/gemini-2.5-pro",           # Google perspective
]

async def ensemble_evaluate(log_file_path: str, output_dir: str = "evaluations_ensemble"):
    """Evaluate with multiple judges and aggregate"""

    individual_scores = []

    for judge_model in JUDGE_MODELS:
        print(f"🤖 Evaluating with {judge_model}...")

        evaluator = ComputationalChemistryJudge(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            judge_model=judge_model,
            enable_web_search=True
        )

        eval_result = await evaluator.evaluate_log(log_file_path)
        individual_scores.append({
            "judge": judge_model,
            "completion": eval_result.completion_score,
            "correctness": eval_result.correctness_score,
            "tool_use": eval_result.tool_use_score,
            "total": eval_result.total_score,
            "reasoning": eval_result.reasoning
        })

    # Aggregate scores
    ensemble_result = {
        "completion_mean": np.mean([s["completion"] for s in individual_scores]),
        "correctness_mean": np.mean([s["correctness"] for s in individual_scores]),
        "tool_use_mean": np.mean([s["tool_use"] for s in individual_scores]),
        "total_mean": np.mean([s["total"] for s in individual_scores]),

        "completion_std": np.std([s["completion"] for s in individual_scores]),
        "correctness_std": np.std([s["correctness"] for s in individual_scores]),
        "tool_use_std": np.std([s["tool_use"] for s in individual_scores]),

        "agreement_score": calculate_inter_judge_agreement(individual_scores),
        "individual_judges": individual_scores,

        "consensus_assessment": "pass" if np.mean([s["total"] for s in individual_scores]) >= 4 else "fail",
        "needs_review": np.std([s["total"] for s in individual_scores]) > 1.5  # High disagreement
    }

    return ensemble_result

def calculate_inter_judge_agreement(scores: List[Dict]) -> float:
    """Calculate agreement using Fleiss' Kappa"""
    from sklearn.metrics import cohen_kappa_score

    # For simplicity, use pairwise kappa and average
    kappas = []
    for i in range(len(scores)):
        for j in range(i+1, len(scores)):
            kappa = cohen_kappa_score(
                [1 if scores[i]["total"] >= 4 else 0],
                [1 if scores[j]["total"] >= 4 else 0]
            )
            kappas.append(kappa)

    return np.mean(kappas) if kappas else 0.0
```

**Why:** Diverse perspectives reduce bias, agreement metrics show confidence

---

#### **4.2 Bias Analysis** ⏱️ 2-3 hours

**Implementation:**
```python
# scripts/analyze_judge_bias.py

def analyze_same_family_bias():
    """Quantify same-family bias across judges"""

    # Load evaluations from each judge
    claude_evals = load_evaluations("evaluations/")
    gpt_evals = load_evaluations("evaluations_gpt4o/")
    gemini_evals = load_evaluations("evaluations_gemini/")

    bias_analysis = {}

    # For each model family
    for model_family in ["claude", "openai", "google"]:
        bias_analysis[model_family] = {
            "claude_judge": [],
            "gpt_judge": [],
            "gemini_judge": []
        }

        # Get scores from each judge for this model family
        for eval in claude_evals:
            if model_family in eval["model_name"].lower():
                bias_analysis[model_family]["claude_judge"].append(eval["total_score"])

        for eval in gpt_evals:
            if model_family in eval["model_name"].lower():
                bias_analysis[model_family]["gpt_judge"].append(eval["total_score"])

        for eval in gemini_evals:
            if model_family in eval["model_name"].lower():
                bias_analysis[model_family]["gemini_judge"].append(eval["total_score"])

    # Calculate bias metrics
    for model_family, scores in bias_analysis.items():
        claude_mean = np.mean(scores["claude_judge"]) if scores["claude_judge"] else 0
        gpt_mean = np.mean(scores["gpt_judge"]) if scores["gpt_judge"] else 0
        gemini_mean = np.mean(scores["gemini_judge"]) if scores["gemini_judge"] else 0

        print(f"\n{model_family.upper()} Models:")
        print(f"  Claude judge avg: {claude_mean:.2f}")
        print(f"  GPT judge avg: {gpt_mean:.2f}")
        print(f"  Gemini judge avg: {gemini_mean:.2f}")

        if model_family == "claude":
            bias = claude_mean - np.mean([gpt_mean, gemini_mean])
            print(f"  ⚠️  Same-family bias: +{bias:.2f} points")
        elif model_family == "openai":
            bias = gpt_mean - np.mean([claude_mean, gemini_mean])
            print(f"  ⚠️  Same-family bias: +{bias:.2f} points")
        elif model_family == "google":
            bias = gemini_mean - np.mean([claude_mean, gpt_mean])
            print(f"  ⚠️  Same-family bias: +{bias:.2f} points")

if __name__ == "__main__":
    analyze_same_family_bias()
```

**Why:** Quantifies bias, validates ensemble reduces it

---

### **Phase 5: Expert Calibration** ⏱️ 1-2 weeks
*Human validation for ground truth*

#### **5.1 Calibration Sample Selection** ⏱️ 2-3 hours

**Implementation:**
```python
# scripts/select_calibration_samples.py

def select_calibration_samples(n: int = 25) -> List[Dict]:
    """Select diverse, representative samples for expert annotation"""

    all_evals = load_all_evaluations("evaluations/")

    samples = {
        "high_scores": [],       # 5 clear passes (score 5-6)
        "low_scores": [],        # 5 clear fails (score 0-2)
        "borderline": [],        # 10 edge cases (score 3-4)
        "high_disagreement": [], # 5 high judge disagreement
    }

    # Ensemble evaluations for disagreement analysis
    ensemble_evals = load_all_evaluations("evaluations_ensemble/")

    # High scores
    high = [e for e in all_evals if e["total_score"] >= 5]
    samples["high_scores"] = random.sample(high, min(5, len(high)))

    # Low scores
    low = [e for e in all_evals if e["total_score"] <= 2]
    samples["low_scores"] = random.sample(low, min(5, len(low)))

    # Borderline
    borderline = [e for e in all_evals if 3 <= e["total_score"] <= 4]
    samples["borderline"] = random.sample(borderline, min(10, len(borderline)))

    # High disagreement (from ensemble)
    disagreements = [e for e in ensemble_evals if e.get("total_std", 0) > 1.0]
    samples["high_disagreement"] = disagreements[:5]

    # Flatten and export
    all_samples = []
    for category, sample_list in samples.items():
        for sample in sample_list:
            all_samples.append({
                **sample,
                "calibration_category": category
            })

    # Export to CSV for annotation
    df = pd.DataFrame(all_samples)
    df.to_csv("data/calibration_samples.csv", index=False)

    print(f"✅ Selected {len(all_samples)} calibration samples")
    print(f"   - High scores: {len(samples['high_scores'])}")
    print(f"   - Low scores: {len(samples['low_scores'])}")
    print(f"   - Borderline: {len(samples['borderline'])}")
    print(f"   - High disagreement: {len(samples['high_disagreement'])}")

    return all_samples
```

**Why:** Diverse sample ensures calibration covers edge cases

---

#### **5.2 Expert Annotation Interface** ⏱️ 3-4 hours

**Implementation:**
```python
# notebooks/expert_annotation.ipynb

import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
import pandas as pd

def create_annotation_widget(sample_idx: int, samples: pd.DataFrame):
    """Interactive annotation interface for chemistry expert"""

    sample = samples.iloc[sample_idx]

    # Display question
    display(HTML(f"<h2>Sample {sample_idx + 1}/{len(samples)}</h2>"))
    display(HTML(f"<h3>{sample['question_id']}: {sample['user_question']}</h3>"))
    display(HTML(f"<p><b>Model:</b> {sample['model_name']}</p>"))
    display(HTML(f"<p><b>Category:</b> {sample['calibration_category']}</p>"))

    # Show agent execution
    display(HTML("<h4>Agent Execution Trace:</h4>"))
    with open(sample['log_file'], 'r') as f:
        log_data = json.load(f)

    for idx, call in enumerate(log_data.get("tool_calls", [])[:10]):  # First 10 tools
        display(HTML(f"<li><b>{call['tool_name']}</b>: {call.get('parameters', {})}</li>"))

    # Show final answer
    display(HTML("<h4>Agent Final Answer:</h4>"))
    display(HTML(f"<pre>{sample['final_answer']}</pre>"))

    # Show LLM judge scores
    display(HTML(f"<h4>LLM Judge Score: {sample['total_score']}/6</h4>"))
    display(HTML(f"<p>Completion: {sample['completion_score']}/2 | Correctness: {sample['correctness_score']}/2 | Tool Use: {sample['tool_use_score']}/2</p>"))

    # Expert scoring widgets
    completion = widgets.IntSlider(min=0, max=2, value=sample['completion_score'], description='Completion:')
    correctness = widgets.IntSlider(min=0, max=2, value=sample['correctness_score'], description='Correctness:')
    tool_use = widgets.IntSlider(min=0, max=2, value=sample['tool_use_score'], description='Tool Use:')

    error_category = widgets.Dropdown(
        options=['None', 'METHODOLOGY', 'EXECUTION', 'INTERPRETATION', 'NUMERICAL', 'INCOMPLETE', 'CHEATING'],
        description='Error Type:',
        value='None'
    )

    rationale = widgets.Textarea(
        description='Rationale:',
        placeholder='Why these scores? What did agent do well/poorly? What should judge have caught?',
        layout=widgets.Layout(width='80%', height='100px')
    )

    judge_feedback = widgets.Textarea(
        description='Judge Feedback:',
        placeholder='Did the LLM judge score correctly? What did it miss? Any biases?',
        layout=widgets.Layout(width='80%', height='100px')
    )

    output = widgets.Output()

    def save_annotation(b):
        with output:
            clear_output()

            annotation = {
                "log_file": sample["log_file"],
                "question_id": sample["question_id"],
                "model_name": sample["model_name"],
                "expert_scores": {
                    "completion": completion.value,
                    "correctness": correctness.value,
                    "tool_use": tool_use.value,
                    "total": completion.value + correctness.value + tool_use.value
                },
                "llm_judge_scores": {
                    "completion": sample["completion_score"],
                    "correctness": sample["correctness_score"],
                    "tool_use": sample["tool_use_score"],
                    "total": sample["total_score"]
                },
                "agreement": {
                    "completion_match": completion.value == sample["completion_score"],
                    "correctness_match": correctness.value == sample["correctness_score"],
                    "tool_use_match": tool_use.value == sample["tool_use_score"],
                    "total_diff": abs((completion.value + correctness.value + tool_use.value) - sample["total_score"])
                },
                "error_category": error_category.value if error_category.value != 'None' else None,
                "expert_rationale": rationale.value,
                "judge_feedback": judge_feedback.value,
                "calibration_category": sample["calibration_category"],
                "annotation_timestamp": datetime.now().isoformat()
            }

            # Save to JSONL
            with open("data/expert_annotations.jsonl", 'a') as f:
                f.write(json.dumps(annotation) + "\n")

            print("✅ Saved! Moving to next sample...")

            # Load next sample
            if sample_idx + 1 < len(samples):
                clear_output(wait=True)
                create_annotation_widget(sample_idx + 1, samples)
            else:
                print("🎉 All samples annotated!")

    save_btn = widgets.Button(description='Save & Next', button_style='success')
    save_btn.on_click(save_annotation)

    display(completion, correctness, tool_use, error_category, rationale, judge_feedback, save_btn, output)

# Load samples and start annotation
samples = pd.read_csv("data/calibration_samples.csv")
create_annotation_widget(0, samples)
```

**Why:** Easy expert annotation, captures detailed feedback

---

#### **5.3 Agreement Analysis** ⏱️ 2-3 hours

**Implementation:**
```python
# scripts/calculate_agreement.py

from sklearn.metrics import cohen_kappa_score
from scipy.stats import pearsonr
import json

def calculate_judge_expert_agreement():
    """Calculate inter-rater reliability between LLM judge and expert"""

    # Load expert annotations
    annotations = []
    with open("data/expert_annotations.jsonl", 'r') as f:
        for line in f:
            annotations.append(json.loads(line))

    expert_scores = [a["expert_scores"]["total"] for a in annotations]
    judge_scores = [a["llm_judge_scores"]["total"] for a in annotations]

    # Cohen's Kappa (categorical agreement for pass/fail)
    expert_pass = [1 if s >= 4 else 0 for s in expert_scores]
    judge_pass = [1 if s >= 4 else 0 for s in judge_scores]
    kappa = cohen_kappa_score(expert_pass, judge_pass)

    # Pearson correlation (numerical agreement)
    correlation, p_value = pearsonr(expert_scores, judge_scores)

    # Identify systematic biases
    overscored = [a for a in annotations if a["llm_judge_scores"]["total"] > a["expert_scores"]["total"] + 1]
    underscored = [a for a in annotations if a["llm_judge_scores"]["total"] < a["expert_scores"]["total"] - 1]
    accurate = [a for a in annotations if abs(a["llm_judge_scores"]["total"] - a["expert_scores"]["total"]) <= 1]

    # Mean absolute error per dimension
    completion_mae = np.mean([abs(a["expert_scores"]["completion"] - a["llm_judge_scores"]["completion"]) for a in annotations])
    correctness_mae = np.mean([abs(a["expert_scores"]["correctness"] - a["llm_judge_scores"]["correctness"]) for a in annotations])
    tool_use_mae = np.mean([abs(a["expert_scores"]["tool_use"] - a["llm_judge_scores"]["tool_use"]) for a in annotations])

    report = {
        "sample_size": len(annotations),
        "kappa": kappa,  # Target: > 0.6 (substantial agreement)
        "correlation": correlation,  # Target: > 0.8 (strong)
        "p_value": p_value,
        "interpretation": interpret_kappa(kappa),
        "bias_analysis": {
            "overscored_count": len(overscored),
            "underscored_count": len(underscored),
            "accurate_count": len(accurate),
            "bias_direction": "positive" if len(overscored) > len(underscored) else "negative",
            "agreement_rate": len(accurate) / len(annotations)
        },
        "dimension_errors": {
            "completion_mae": completion_mae,
            "correctness_mae": correctness_mae,
            "tool_use_mae": tool_use_mae
        },
        "needs_improvement": kappa < 0.6 or correlation < 0.8,
        "improvement_areas": identify_improvement_areas(annotations)
    }

    # Save report
    with open("analysis/expert_agreement_report.json", 'w') as f:
        json.dump(report, f, indent=2)

    print(f"📊 Agreement Analysis:")
    print(f"   Cohen's Kappa: {kappa:.3f} ({report['interpretation']})")
    print(f"   Correlation: {correlation:.3f} (p={p_value:.4f})")
    print(f"   Agreement rate: {report['bias_analysis']['agreement_rate']:.1%}")
    print(f"   Bias direction: {report['bias_analysis']['bias_direction']}")

    return report

def interpret_kappa(kappa: float) -> str:
    """Interpret Cohen's Kappa value"""
    if kappa < 0:
        return "Poor (worse than chance)"
    elif kappa < 0.2:
        return "Slight"
    elif kappa < 0.4:
        return "Fair"
    elif kappa < 0.6:
        return "Moderate"
    elif kappa < 0.8:
        return "Substantial"
    else:
        return "Almost Perfect"

def identify_improvement_areas(annotations: List[Dict]) -> List[str]:
    """Identify where judge needs improvement"""

    areas = []

    # Analyze by error category
    error_categories = [a.get("error_category") for a in annotations if a.get("error_category")]
    if error_categories:
        from collections import Counter
        category_counts = Counter(error_categories)
        top_category = category_counts.most_common(1)[0][0]
        areas.append(f"High {top_category} errors - add examples to rubric")

    # Analyze dimension-specific issues
    completion_errors = [a for a in annotations if abs(a["expert_scores"]["completion"] - a["llm_judge_scores"]["completion"]) >= 1]
    if len(completion_errors) / len(annotations) > 0.3:
        areas.append("Completion scoring inconsistent - clarify criteria")

    correctness_errors = [a for a in annotations if abs(a["expert_scores"]["correctness"] - a["llm_judge_scores"]["correctness"]) >= 1]
    if len(correctness_errors) / len(annotations) > 0.3:
        areas.append("Correctness scoring issues - add more reference values or improve web search usage")

    tool_use_errors = [a for a in annotations if abs(a["expert_scores"]["tool_use"] - a["llm_judge_scores"]["tool_use"]) >= 1]
    if len(tool_use_errors) / len(annotations) > 0.3:
        areas.append("Tool use scoring unclear - define expected workflows")

    return areas
```

**Why:** Validates judge reliability, identifies improvement areas

---

### **Phase 6: Error Analysis Infrastructure** ⏱️ 1 week
*Systematic error taxonomy and pattern identification*

#### **6.1 Error Categorization** ⏱️ Already done in Phase 2.4!

We already implemented automatic error categorization in the judge prompt. Now we just need to aggregate and analyze.

#### **6.2 Pattern Analysis** ⏱️ 3-4 hours

**Implementation:**
```python
# notebooks/error_pattern_analysis.ipynb

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def analyze_error_patterns():
    """Comprehensive error pattern analysis"""

    # Load all evaluations
    evals = load_all_evaluations("evaluations/")

    # Filter failures
    failures = [e for e in evals if e["total_score"] < 4]

    # Convert to DataFrame
    df = pd.DataFrame(failures)

    # 1. Error distribution by model
    error_by_model = df.groupby(["model_name", "error_category"]).size().reset_index(name="count")

    fig1 = px.bar(
        error_by_model,
        x="model_name",
        y="count",
        color="error_category",
        title="Error Types by Model",
        labels={"count": "Number of Failures", "model_name": "Model"},
        barmode="stack"
    )
    fig1.write_html("plots/error_by_model.html")

    # 2. Error distribution by tier
    error_by_tier = df.groupby(["question_tier", "error_category"]).size().reset_index(name="count")

    fig2 = px.bar(
        error_by_tier,
        x="question_tier",
        y="count",
        color="error_category",
        title="Error Types by Question Difficulty",
        barmode="stack"
    )
    fig2.write_html("plots/error_by_tier.html")

    # 3. Model-specific insights
    model_insights = {}

    for model in df["model_name"].unique():
        model_failures = df[df["model_name"] == model]
        top_errors = model_failures["error_category"].value_counts().head(3).to_dict()

        model_insights[model] = {
            "total_failures": len(model_failures),
            "failure_rate": len(model_failures) / len([e for e in evals if e["model_name"] == model]),
            "top_errors": top_errors,
            "avg_score": model_failures["total_score"].mean(),
            "recommendations": generate_recommendations(model, top_errors)
        }

    # 4. Cross-model patterns
    # Which questions cause failures across ALL models?
    failure_questions = df.groupby("question_id").size().reset_index(name="failure_count")
    universal_hard = failure_questions[failure_questions["failure_count"] >= 5]  # Failed by 5+ models

    # 5. Calibration analysis (overconfidence)
    calibration = []
    for model in df["model_name"].unique():
        model_evals = [e for e in evals if e["model_name"] == model]
        claimed_complete = [e for e in model_evals if e["completion_score"] == 2]
        actually_correct = [e for e in claimed_complete if e["correctness_score"] >= 1]

        if claimed_complete:
            overconfidence_rate = (len(claimed_complete) - len(actually_correct)) / len(claimed_complete)
            calibration.append({
                "model": model,
                "claimed_complete": len(claimed_complete),
                "actually_correct": len(actually_correct),
                "overconfidence_rate": overconfidence_rate,
                "status": "overconfident" if overconfidence_rate > 0.3 else "well_calibrated"
            })

    # Save analysis
    analysis = {
        "error_distribution": error_by_model.to_dict(),
        "model_insights": model_insights,
        "universal_hard_questions": universal_hard.to_dict(),
        "calibration": calibration,
        "generated_at": datetime.now().isoformat()
    }

    with open("analysis/error_patterns.json", 'w') as f:
        json.dump(analysis, f, indent=2)

    return analysis

def generate_recommendations(model: str, top_errors: Dict[str, int]) -> List[str]:
    """Generate model-specific recommendations"""

    recs = []

    if top_errors.get("METHODOLOGY", 0) > 3:
        recs.append("Add examples of correct computational methods to prompt")

    if top_errors.get("EXECUTION", 0) > 3:
        recs.append("Improve tool selection guidance in system prompt")

    if top_errors.get("INTERPRETATION", 0) > 3:
        recs.append("Add examples of result interpretation to prompt")

    if top_errors.get("NUMERICAL", 0) > 3:
        recs.append("Emphasize numerical accuracy requirements in prompt")

    if top_errors.get("INCOMPLETE", 0) > 3:
        recs.append("Improve workflow monitoring and completion checking")

    if top_errors.get("CHEATING", 0) > 0:
        recs.append("CRITICAL: Model attempting to find answers via web search instead of computing")

    return recs

# Run analysis
analysis = analyze_error_patterns()

# Display summary
print("📊 Error Pattern Analysis\n")

print("🔍 Model Insights:")
for model, insights in analysis["model_insights"].items():
    print(f"\n{model}:")
    print(f"  Failure rate: {insights['failure_rate']:.1%}")
    print(f"  Top errors: {insights['top_errors']}")
    print(f"  Recommendations:")
    for rec in insights["recommendations"]:
        print(f"    - {rec}")

print("\n⚠️  Universal Hard Questions (failed by 5+ models):")
for _, row in analysis["universal_hard_questions"].iterrows():
    print(f"  - {row['question_id']}: {row['failure_count']} failures")

print("\n🎯 Model Calibration:")
for cal in analysis["calibration"]:
    print(f"  {cal['model']}: {cal['status']} (overconfidence: {cal['overconfidence_rate']:.1%})")
```

**Why:** Identifies patterns, generates actionable recommendations

---

#### **6.3 Improvement Tracking** ⏱️ 2-3 hours

**Implementation:**
```python
# scripts/track_improvements.py

def track_improvement_over_time():
    """Track how evaluation quality improves"""

    # Compare old vs new evaluations
    old_evals = load_evaluations("evaluations_v1/")  # Before improvements
    new_evals = load_evaluations("evaluations/")     # After improvements

    metrics = {
        "old": calculate_metrics(old_evals),
        "new": calculate_metrics(new_evals),
        "delta": {}
    }

    # Calculate improvements
    for key in metrics["old"].keys():
        metrics["delta"][key] = metrics["new"][key] - metrics["old"][key]

    print("📈 Improvement Tracking\n")
    print(f"Pass rate: {metrics['old']['pass_rate']:.1%} → {metrics['new']['pass_rate']:.1%} ({metrics['delta']['pass_rate']:+.1%})")
    print(f"Avg score: {metrics['old']['avg_score']:.2f} → {metrics['new']['avg_score']:.2f} ({metrics['delta']['avg_score']:+.2f})")
    print(f"Score variance: {metrics['old']['score_variance']:.2f} → {metrics['new']['score_variance']:.2f} ({metrics['delta']['score_variance']:+.2f})")

    return metrics

def calculate_metrics(evals: List[Dict]) -> Dict[str, float]:
    """Calculate evaluation metrics"""

    return {
        "pass_rate": sum(1 for e in evals if e["total_score"] >= 4) / len(evals),
        "avg_score": np.mean([e["total_score"] for e in evals]),
        "score_variance": np.var([e["total_score"] for e in evals]),
        "completion_avg": np.mean([e["completion_score"] for e in evals]),
        "correctness_avg": np.mean([e["correctness_score"] for e in evals]),
        "tool_use_avg": np.mean([e["tool_use_score"] for e in evals]),
    }
```

**Why:** Quantifies improvement, validates changes work

---

### **Phase 7: Sustainability & Iteration** ⏱️ Ongoing
*Establish continuous improvement loop*

#### **7.1 Weekly Review Workflow** ⏱️ 2-4 hours/week

**Monday: Run Evaluations**
```bash
# Test new models or prompt changes
python scripts/run_all_missing_evals.py --judge anthropic/claude-sonnet-4

# Run ensemble for critical cases
python scripts/ensemble_judge.py --flagged-only

# Automated validation
python scripts/hybrid_evaluation.py --all-logs
```

**Tuesday: Review Queue**
```bash
# Flag low-confidence cases
python scripts/flag_uncertain_cases.py --threshold 70

# Expert reviews 10% random sample
python notebooks/expert_annotation.ipynb --sample-rate 0.1

# Update error categories
python scripts/update_error_taxonomy.py
```

**Wednesday: Analysis**
```bash
# Generate error patterns
jupyter notebook notebooks/error_pattern_analysis.ipynb

# Model comparison
python scripts/compare_models.py --metric all

# Track improvements
python scripts/track_improvements.py
```

**Thursday: Iterate**
```bash
# Update prompts based on findings
python scripts/update_prompts.py --recommendations analysis/improvement_recommendations.json

# Refine tools if needed
python scripts/update_tool_validation.py

# Improve benchmark questions
python scripts/refine_questions.py --based-on analysis/universal_hard_questions.json
```

---

#### **7.2 Monthly Deep Dive** ⏱️ 4-8 hours/month

**Month 1: Validation**
- Re-calibrate judge on 25 new samples
- Update ground truth with new molecules
- Publish accuracy metrics

**Month 2: Expansion**
- Add new question types (tier 4?)
- Test additional models
- Expand error taxonomy

**Month 3: Publication**
- Document methodology
- Write up findings
- Share framework publicly

---

## 📊 Success Metrics

### **Evaluation Quality**
- ✅ **Cohen's Kappa > 0.6** (substantial agreement with expert)
- ✅ **Correlation > 0.8** (strong numerical agreement)
- ✅ **Coverage ≥ 10%** (expert validation on significant sample)
- ✅ **Error taxonomy completeness** (all failures categorized)

### **Bias Reduction**
- ✅ **Same-family bias < 0.5 points** (ensemble vs single judge)
- ✅ **Inter-judge agreement > 0.7** (ensemble consensus)
- ✅ **Web search utilization > 80%** (judge using literature)

### **Actionability**
- ✅ **Time to insight < 1 day** (from eval run to patterns identified)
- ✅ **Improvement velocity < 1 week** (test prompt changes quickly)
- ✅ **Reproducibility 100%** (all scores traceable to methodology)

### **Business Impact**
- ✅ **Model selection confidence** (can definitively recommend best model)
- ✅ **Cost optimization** (know which expensive models worth it)
- ✅ **Failure prevention** (identify risky use cases before deployment)

---

## 🎯 Implementation Checklist

### **Phase 1: Web Search** ✅ DONE
- [x] Implement OpenRouter `:online` suffix
- [x] Extract web citations from annotations
- [x] Enrich citations with quoted content
- [x] Test on sample evaluations
- [x] Verify real literature validation working

### **Phase 2: Judge Improvements** (Next - 3-4 hours)
- [ ] Add concrete scoring examples to rubric
- [ ] Provide full execution trace to judge
- [ ] Clarify completion criteria
- [ ] Add automatic error categorization
- [ ] Test on 10 samples, compare old vs new

### **Phase 3: Ground Truth** (1-2 days)
- [ ] Create `data/ground_truth.json` for all 22 questions
- [ ] Implement automated validation function
- [ ] Build hybrid scoring (auto + LLM)
- [ ] Test automated validation accuracy

### **Phase 4: Multi-Judge Ensemble** (1 day)
- [ ] Implement ensemble evaluation script
- [ ] Run GPT-4o + Gemini 2.5 Pro judges
- [ ] Calculate inter-judge agreement
- [ ] Analyze same-family bias reduction
- [ ] Test on full dataset

### **Phase 5: Expert Calibration** (1-2 weeks)
- [ ] Select 25 calibration samples
- [ ] Create annotation interface
- [ ] Recruit chemistry expert (or self-annotate if qualified)
- [ ] Complete 25 expert annotations
- [ ] Calculate Cohen's kappa and correlation
- [ ] Identify judge failure modes
- [ ] Update rubric based on expert feedback

### **Phase 6: Error Analysis** (1 week)
- [ ] Aggregate error categories from all evals
- [ ] Generate error pattern visualizations
- [ ] Identify model-specific failure modes
- [ ] Find universal hard questions
- [ ] Analyze model calibration (overconfidence)
- [ ] Generate improvement recommendations

### **Phase 7: Sustainability** (Ongoing)
- [ ] Establish weekly review workflow
- [ ] Schedule monthly deep dives
- [ ] Document all processes
- [ ] Create templates for future benchmarks
- [ ] Set up automated reporting

---

## 📈 Expected Timeline

**Week 1:**
- ✅ Web search (DONE)
- Day 1-2: Judge improvements
- Day 3-4: Ground truth database
- Day 5: Multi-judge ensemble setup

**Week 2:**
- Day 1-2: Run ensemble evaluations
- Day 3-4: Calibration sample selection + annotation setup
- Day 5: Start expert annotations (5-10 samples)

**Week 3:**
- Day 1-3: Complete expert annotations (remaining 15-20)
- Day 4-5: Agreement analysis + rubric refinement

**Week 4:**
- Day 1-3: Error pattern analysis
- Day 4-5: Generate recommendations + improvements

**Week 5:**
- Day 1-2: Implement improvements
- Day 3-4: Re-run evaluations
- Day 5: Validate improvements + document

**Ongoing:**
- 2-4 hours/week: Review + iteration
- 4-8 hours/month: Deep dive + expansion

---

## 💡 Key Insights

### **Start with Quick Wins**
Web search was the perfect first step - high impact, low effort. Continue this approach:
1. Fix obvious issues (Phase 2) before complex solutions
2. Ground truth enables automation (Phase 3)
3. THEN add ensemble (Phase 4) once basics work
4. Expert validation last (Phase 5) to validate the whole system

### **Build on What Works**
- ✅ You have web search working
- ✅ You have full execution logs
- ✅ You have structured evaluation pipeline
- ✅ Just need to improve what the judge sees and validate it

### **Human-in-the-Loop is Critical**
- LLM judge handles bulk (200 evaluations)
- Expert validates sample (25 calibration)
- Hybrid gives best of both worlds
- Error taxonomy shows WHERE to improve

### **Measurement Enables Improvement**
- Can't improve what you can't measure
- Ground truth → objective validation
- Expert calibration → known accuracy
- Error patterns → actionable insights
- Track improvements over time

---

## 🚀 Quick Start (Today)

**Next 4 Hours:**

1. **Hour 1: Add Scoring Examples** ⏱️ 45 min
   - Update `create_evaluation_prompt()` with concrete examples
   - Test on 3 samples

2. **Hour 2: Full Execution Trace** ⏱️ 1 hour
   - Update `extract_log_summary()` to include tool trace
   - Update prompt to show execution details
   - Test on 3 samples

3. **Hour 3: Error Categorization** ⏱️ 1 hour
   - Add error category to prompt
   - Update parser to extract it
   - Test on 3 failed samples

4. **Hour 4: Create Ground Truth Start** ⏱️ 1 hour
   - Create `data/ground_truth.json`
   - Add 5 most common questions (acetic acid, aspirin, etc.)
   - Test automated validation on those 5

**By end of day:**
- ✅ Judge has better rubric
- ✅ Judge sees full execution
- ✅ Errors automatically categorized
- ✅ 5 questions have ground truth validation

**Tomorrow: Finish ground truth, start ensemble!**

---

## 📚 References

- **Hamel's Eval Guide:** https://hamel.dev/blog/posts/eval-tools/
- **LLM-as-Judge Bias:** Zheng et al. 2023 - "Judging LLM-as-a-Judge"
- **Multi-Judge Ensembles:** Liu et al. 2023 - "G-Eval"
- **Calibration Methods:** Kadavath et al. 2022 - "Language Models (Mostly) Know What They Know"
- **Chemistry Databases:** PubChem, CompTox, experimental pKa databases

---

## 🎉 Bottom Line

**You've already completed the hardest part - web search for real validation!**

Now it's just:
1. **Days 1-2:** Quick judge improvements (3-4 hours)
2. **Days 3-4:** Ground truth database (1-2 days)
3. **Week 2:** Multi-judge ensemble + bias analysis (1 week)
4. **Weeks 3-4:** Expert calibration (2 weeks)
5. **Week 5:** Error analysis + sustainability (1 week)
6. **Ongoing:** 2-4 hours/week to maintain

**In 1 month, you'll have:**
- ✅ Validated, defensible evaluation system
- ✅ Known accuracy (expert-calibrated)
- ✅ Reduced bias (ensemble judges)
- ✅ Objective ground truth
- ✅ Systematic error insights
- ✅ Sustainable improvement process

**You're building the evaluation framework that other benchmarks will copy!** 🚀
