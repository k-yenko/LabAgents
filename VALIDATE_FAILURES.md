# How to Validate Real Failures (Avoiding Judge Bias)

## 🚨 The Problem You Identified

**Current state**:
- Claude judge scores all evaluations
- Claude models: 95-100% pass rate
- OpenAI o3: 13.6% pass rate
- **This is suspicious** - likely same-family bias

**Your question**: "Aren't my failures biased? How do I ensure failures are actually failures?"

**Answer**: YES, they're biased. Here's how to find REAL failures.

---

## ✅ Method 1: Ground Truth Validation (Objective, No Judge Needed)

**Principle**: You don't need a judge to check if a number is correct.

### **Step 1: Create Simple Ground Truth File** (30 min)

```json
// data/ground_truth_simple.json
{
  "tier1_002": {
    "question": "Calculate pKa of acetic acid",
    "molecule": "acetic acid",
    "expected_value": 4.76,
    "acceptable_range": [4.2, 5.2],
    "source": "Experimental consensus value"
  },
  "tier1_003": {
    "question": "Calculate logP of aspirin",
    "molecule": "aspirin",
    "expected_value": 1.19,
    "acceptable_range": [0.8, 1.5],
    "source": "PubChem CID 2244"
  },
  "tier1_004": {
    "question": "Calculate pKa of benzoic acid",
    "molecule": "benzoic acid",
    "expected_value": 4.20,
    "acceptable_range": [3.8, 4.6],
    "source": "Experimental literature"
  }
  // Add 5-10 most common questions with KNOWN experimental values
}
```

### **Step 2: Automated Correctness Check** (1 hour)

```python
# scripts/validate_against_ground_truth.py

import json
import glob
import re
from typing import Optional

def extract_numerical_value(text: str, property_type: str) -> Optional[float]:
    """Extract numerical answer from agent's final answer"""

    # Common patterns
    patterns = {
        'pka': [
            r'pKa\s*[=:is]\s*([\d.]+)',
            r'pKa.*?([\d.]+)',
            r'acid dissociation constant.*?([\d.]+)',
        ],
        'logp': [
            r'logP\s*[=:is]\s*([\d.]+)',
            r'partition coefficient.*?([\d.]+)',
        ],
        'solubility': [
            r'([\d.]+)\s*mg/mL',
            r'solubility.*?([\d.]+)',
        ]
    }

    for pattern in patterns.get(property_type.lower(), []):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except:
                continue

    return None

def validate_answer(log_file: str, ground_truth: dict) -> dict:
    """Check if answer is objectively correct, no judge needed"""

    with open(log_file, 'r') as f:
        log_data = json.load(f)

    question_id = log_data.get('question_id')

    if question_id not in ground_truth:
        return {'status': 'no_ground_truth'}

    gt = ground_truth[question_id]
    final_answer = log_data.get('final_answer', '')

    # Extract numerical value
    agent_value = extract_numerical_value(final_answer, gt.get('property_type', 'pka'))

    if agent_value is None:
        return {
            'status': 'no_numerical_answer',
            'objective_correctness': False,
            'reason': 'Agent did not provide numerical answer'
        }

    # Check if in acceptable range (OBJECTIVE)
    in_range = gt['acceptable_range'][0] <= agent_value <= gt['acceptable_range'][1]
    error = abs(agent_value - gt['expected_value'])
    percent_error = (error / gt['expected_value']) * 100

    return {
        'status': 'validated',
        'agent_value': agent_value,
        'expected_value': gt['expected_value'],
        'error': error,
        'percent_error': percent_error,
        'in_acceptable_range': in_range,
        'objective_correctness': in_range,
        'source': gt['source']
    }

def compare_judge_vs_ground_truth():
    """Find where Claude judge disagrees with objective ground truth"""

    # Load ground truth
    with open('data/ground_truth_simple.json', 'r') as f:
        ground_truth = json.load(f)

    results = []

    for question_id in ground_truth.keys():
        # Find all model logs for this question
        log_pattern = f"logs/{question_id}/*/*.json"
        log_files = glob.glob(log_pattern)

        for log_file in log_files:
            if 'api_error' in log_file:
                continue

            # Get objective correctness
            obj_validation = validate_answer(log_file, ground_truth)

            if obj_validation['status'] != 'validated':
                continue

            # Get Claude judge's score
            model_name = log_file.split('/')[-2]  # Extract model folder name
            eval_file = f"evaluations/{question_id}/json/{model_name}_evaluation.json"

            if not os.path.exists(eval_file):
                continue

            with open(eval_file, 'r') as f:
                judge_eval = json.load(f)

            # Compare
            objective_correct = obj_validation['objective_correctness']
            judge_correct = judge_eval['correctness_score'] >= 1  # Judge gave 1-2 points

            agreement = objective_correct == judge_correct

            results.append({
                'question_id': question_id,
                'model': model_name,
                'agent_value': obj_validation['agent_value'],
                'expected_value': obj_validation['expected_value'],
                'percent_error': obj_validation['percent_error'],
                'objective_correct': objective_correct,
                'judge_score': judge_eval['correctness_score'],
                'judge_correct': judge_correct,
                'agreement': agreement,
                'bias_type': classify_bias(objective_correct, judge_correct)
            })

    return results

def classify_bias(objective_correct: bool, judge_correct: bool) -> str:
    """Classify type of disagreement"""
    if objective_correct and not judge_correct:
        return 'FALSE_NEGATIVE'  # Judge too harsh
    elif not objective_correct and judge_correct:
        return 'FALSE_POSITIVE'  # Judge too lenient
    else:
        return 'AGREEMENT'

def analyze_bias_patterns(results: list):
    """Identify systematic bias patterns"""

    import pandas as pd
    df = pd.DataFrame(results)

    print("="*80)
    print("JUDGE BIAS ANALYSIS")
    print("="*80)

    # Overall agreement rate
    agreement_rate = df['agreement'].mean()
    print(f"\nOverall Agreement: {agreement_rate:.1%}")
    print(f"  ✓ Judge agrees with ground truth: {agreement_rate:.1%}")
    print(f"  ✗ Judge disagrees: {1-agreement_rate:.1%}")

    # Bias breakdown
    bias_counts = df['bias_type'].value_counts()
    print(f"\nBias Breakdown:")
    print(f"  Agreement: {bias_counts.get('AGREEMENT', 0)} cases")
    print(f"  False Negatives: {bias_counts.get('FALSE_NEGATIVE', 0)} cases (judge too harsh)")
    print(f"  False Positives: {bias_counts.get('FALSE_POSITIVE', 0)} cases (judge too lenient)")

    # By model family
    print(f"\n{'='*80}")
    print("BIAS BY MODEL FAMILY")
    print("="*80)

    for model_family in ['claude', 'openai', 'google']:
        family_df = df[df['model'].str.contains(model_family, case=False)]

        if len(family_df) == 0:
            continue

        family_agreement = family_df['agreement'].mean()
        false_pos = len(family_df[family_df['bias_type'] == 'FALSE_POSITIVE'])
        false_neg = len(family_df[family_df['bias_type'] == 'FALSE_NEGATIVE'])

        print(f"\n{model_family.upper()} models:")
        print(f"  Agreement with ground truth: {family_agreement:.1%}")
        print(f"  False positives (judge too lenient): {false_pos}")
        print(f"  False negatives (judge too harsh): {false_neg}")

        # Same-family bias indicator
        if model_family == 'claude':
            if false_pos > false_neg:
                print(f"  ⚠️  BIAS DETECTED: Judge gives Claude models benefit of doubt")
        elif model_family == 'openai':
            if false_neg > false_pos:
                print(f"  ⚠️  BIAS DETECTED: Judge too harsh on OpenAI models")

    # Export disagreements for manual review
    disagreements = df[df['agreement'] == False]
    disagreements.to_csv('analysis/judge_disagreements.csv', index=False)

    print(f"\n{'='*80}")
    print(f"Exported {len(disagreements)} disagreements to analysis/judge_disagreements.csv")
    print(f"REVIEW THESE MANUALLY to understand judge bias patterns")
    print("="*80)

    return df

if __name__ == '__main__':
    import os
    os.makedirs('analysis', exist_ok=True)

    results = compare_judge_vs_ground_truth()
    df = analyze_bias_patterns(results)
```

### **Step 3: Run Analysis**

```bash
python scripts/validate_against_ground_truth.py
```

**Expected output**:
```
================================================================================
JUDGE BIAS ANALYSIS
================================================================================

Overall Agreement: 68%
  ✓ Judge agrees with ground truth: 68%
  ✗ Judge disagrees: 32%

Bias Breakdown:
  Agreement: 45 cases
  False Negatives: 8 cases (judge too harsh)
  False Positives: 13 cases (judge too lenient)

================================================================================
BIAS BY MODEL FAMILY
================================================================================

CLAUDE models:
  Agreement with ground truth: 82%
  False positives (judge too lenient): 9
  False negatives (judge too harsh): 2
  ⚠️  BIAS DETECTED: Judge gives Claude models benefit of doubt

OPENAI models:
  Agreement with ground truth: 54%
  False positives (judge too lenient): 2
  False negatives (judge too harsh): 6
  ⚠️  BIAS DETECTED: Judge too harsh on OpenAI models

GOOGLE models:
  Agreement with ground truth: 71%
  False positives (judge too lenient): 2
  False negatives (judge too harsh): 0

================================================================================
Exported 21 disagreements to analysis/judge_disagreements.csv
REVIEW THESE MANUALLY to understand judge bias patterns
================================================================================
```

---

## ✅ Method 2: Manual Spot Check (Human Ground Truth)

**Principle**: YOU are the ground truth for 5-10 cases.

### **Step 1: Pick 10 Random Evaluations** (5 min)

```python
# scripts/sample_for_manual_review.py

import json, glob, random

all_evals = glob.glob('evaluations/*/json/*_evaluation.json')
sample = random.sample(all_evals, 10)

for eval_file in sample:
    with open(eval_file, 'r') as f:
        data = json.load(f)

    # Get corresponding log
    question_id = data['question_id']
    model_name = eval_file.split('/')[-1].replace('_evaluation.json', '')
    log_file = f"logs/{question_id}/{model_name}/{model_name}_*.json"

    print(f"\n{'='*80}")
    print(f"Question: {question_id}")
    print(f"Model: {model_name}")
    print(f"Judge Score: {data['total_score']}/6 ({data['overall_assessment']})")
    print(f"Log: {glob.glob(log_file)[0] if glob.glob(log_file) else 'NOT FOUND'}")
    print(f"Eval: {eval_file}")
```

### **Step 2: Review Each Case as Expert** (2 hours)

For each of the 10 samples, YOU manually decide:

```markdown
# analysis/manual_spot_check.md

## Sample 1: tier1_002 - acetic acid pKa
**Model**: anthropic/claude-sonnet-4
**Judge Score**: 6/6 (pass)

### Agent's Answer
"The calculated pKa is 4.82 using DFT B3LYP/6-31G*"

### Literature Check
- Expected pKa: 4.76 (consensus experimental)
- Error: 0.06 units (1.3% error)

### YOUR Assessment
- ✅ **CORRECT** - Within experimental error
- ✅ **Judge agreed** - Gave 2/2 for correctness

**Verdict**: AGREEMENT ✓

---

## Sample 2: tier1_001 - remdesivir solubility
**Model**: openai/o3
**Judge Score**: 2/6 (fail)

### Agent's Answer
"Unable to complete calculation. Workflow timed out after 300s."

### Check Agent Log
- Agent submitted workflow
- Checked status once at 60s
- Saw "running"
- Gave up immediately
- Never retrieved results

### Literature Check
- Expected: 0.339 mg/mL
- Agent's answer: None (incomplete)

### YOUR Assessment
- ✗ **INCOMPLETE** - Agent gave up too early
- ✅ **Judge agreed** - Gave 0/2 for completion

**Verdict**: AGREEMENT ✓

---

## Sample 3: tier2_003 - aspirin pKa
**Model**: openai/o3
**Judge Score**: 1/6 (fail)

### Agent's Answer
"The calculated pKa is 3.47 using DFT"

### Literature Check
- Expected pKa: 3.49 (experimental)
- Error: 0.02 units (0.6% error)

### YOUR Assessment
- ✅ **CORRECT** - Excellent accuracy!
- ✗ **Judge DISAGREED** - Gave 0/2 for correctness

### Judge's Reasoning
"Agent's value of 3.47 deviates from literature value of 3.5"

### YOUR Analysis
- ⚠️  **FALSE NEGATIVE** - Judge too strict
- Agent was extremely accurate (0.02 units off)
- Judge possibly using rounded literature value (3.5 vs 3.49)
- **BIAS INDICATOR**: Is judge harsher on o3?

**Verdict**: JUDGE ERROR - False negative ✗

---

## Sample 4: tier1_005 - ibuprofen logP
**Model**: anthropic/claude-opus-4
**Judge Score**: 5/6 (pass)

### Agent's Answer
"Calculated logP = 4.2 using XLogP3"

### Literature Check
- Expected logP: 3.97 (PubChem)
- Error: 0.23 units (5.8% error)

### YOUR Assessment
- ✅ **ACCEPTABLE** - Within typical ML error (±0.3)
- ✅ **Judge agreed** - Gave 2/2 for correctness

**Verdict**: AGREEMENT ✓

---

## Sample 5: tier2_001 - caffeine pKa
**Model**: anthropic/claude-sonnet-4
**Judge Score**: 6/6 (pass)

### Agent's Answer
"The calculated pKa is 10.2"

### Literature Check
- Expected pKa: 10.4 (experimental)
- Error: 0.2 units (1.9% error)

### YOUR Assessment
- ✅ **CORRECT** - Good accuracy
- ✅ **Judge agreed** - Gave 2/2

**Verdict**: AGREEMENT ✓

---

## Sample 6: tier1_007 - compound X
**Model**: google/gemini-2.5-pro
**Judge Score**: 3/6 (fail)

### Agent's Answer
"Calculated pKa = 8.9"

### Literature Check
- Expected pKa: 7.2 (experimental)
- Error: 1.7 units (23.6% error)

### YOUR Assessment
- ✗ **INCORRECT** - Too far off
- ✅ **Judge agreed** - Gave 0/2 for correctness

**Verdict**: AGREEMENT ✓

---

## Sample 7: tier3_002 - complex molecule
**Model**: openai/gpt-4o
**Judge Score**: 2/6 (fail)

### Agent's Answer
"Calculated solubility = 0.045 mg/mL"

### Literature Check
- Expected: 0.12 mg/mL (experimental)
- Error: 0.075 mg/mL (62.5% error)

### YOUR Assessment
- ⚠️  **BORDERLINE** - Within ML model error range (±50-100%)
- ✗ **Judge DISAGREED** - Gave 0/2 for correctness

### YOUR Analysis
- Judge used ±50% threshold
- Actual error: 62.5% (just outside threshold)
- This is TECHNICALLY correct by rubric
- But: Is ±50% threshold too strict for ML solubility models?

**Verdict**: AGREEMENT (but rubric may be too strict) ⚠️

---

## Sample 8: tier1_003 - aspirin logP
**Model**: anthropic/claude-sonnet-4
**Judge Score**: 6/6 (pass)

### Agent's Answer
"Calculated logP = 1.25 using XLogP3"

### Literature Check
- Expected logP: 1.19 (PubChem)
- Error: 0.06 units (5% error)

### YOUR Assessment
- ✅ **CORRECT** - Excellent
- ✅ **Judge agreed** - Gave 2/2

**Verdict**: AGREEMENT ✓

---

## Sample 9: tier2_005 - molecule Y pKa
**Model**: openai/o3
**Judge Score**: 4/6 (pass)

### Agent's Answer
"Calculated pKa = 5.1"

### Literature Check
- Expected pKa: 6.8 (experimental)
- Error: 1.7 units (25% error)

### YOUR Assessment
- ✗ **INCORRECT** - Significant error
- ✗ **Judge DISAGREED** - Gave 1/2 for correctness

### YOUR Analysis
- ⚠️  **FALSE POSITIVE** - Judge too lenient
- 1.7 units is >1.5 unit threshold → should be 0/2
- Judge gave 1/2 (partial credit)
- **BIAS INDICATOR**: Is judge giving o3 benefit of doubt?

**Verdict**: JUDGE ERROR - False positive ✗

---

## Sample 10: tier1_004 - benzoic acid pKa
**Model**: google/gemini-2.5-pro
**Judge Score**: 5/6 (pass)

### Agent's Answer
"Calculated pKa = 4.15 using DFT"

### Literature Check
- Expected pKa: 4.20 (experimental)
- Error: 0.05 units (1.2% error)

### YOUR Assessment
- ✅ **CORRECT** - Excellent
- ✅ **Judge agreed** - Gave 2/2

**Verdict**: AGREEMENT ✓
```

### **Step 3: Calculate Your Agreement**

```
MANUAL SPOT CHECK RESULTS (10 samples)
======================================

Agreement: 7/10 (70%)
  ✓ Judge agreed with human: 7 cases
  ✗ Judge disagreed: 3 cases

Disagreements:
  False Negatives: 1 (tier2_003 - o3 aspirin pKa)
  False Positives: 1 (tier2_005 - o3 molecule Y pKa)
  Rubric too strict: 1 (tier3_002 - gpt-4o solubility)

Bias Indicators:
  ⚠️  Sample 3: Judge harsh on o3 (false negative)
  ⚠️  Sample 9: Judge lenient on o3 (false positive)
  → Inconsistent, need more data

Claude models in sample: 4/4 agreements (100%)
OpenAI models in sample: 2/4 agreements (50%)
Google models in sample: 2/2 agreements (100%)

⚠️  TENTATIVE BIAS: Judge may be harsher on OpenAI models
✅  SAMPLE TOO SMALL: Need 20-30 samples for confidence
```

---

## ✅ Method 3: Cross-Judge Validation

**Principle**: If multiple judges disagree with each other on the SAME log, there's no ground truth - it's subjective.

### **Run 2-3 Other Judges on Same Logs** (2 hours)

```bash
# Run GPT-4o judge on ALL existing logs
python scripts/run_all_missing_evals.py \
  --judge openai/gpt-4o \
  --output-dir evaluations_gpt4o

# Run Gemini judge on ALL existing logs
python scripts/run_all_missing_evals.py \
  --judge google/gemini-2.5-pro \
  --output-dir evaluations_gemini
```

### **Compare Judge Disagreements**

```python
# scripts/compare_judges.py

import json, glob
import pandas as pd

def load_all_evaluations(eval_dir: str) -> dict:
    """Load all evaluations into dict keyed by (question_id, model_name)"""
    evals = {}

    for eval_file in glob.glob(f"{eval_dir}/*/json/*_evaluation.json"):
        with open(eval_file, 'r') as f:
            data = json.load(f)

        question_id = data['question_id']
        model_name = eval_file.split('/')[-1].replace('_evaluation.json', '')

        evals[(question_id, model_name)] = data

    return evals

def compare_judges():
    """Find where judges disagree on same agent logs"""

    claude_evals = load_all_evaluations('evaluations')
    gpt4o_evals = load_all_evaluations('evaluations_gpt4o')
    gemini_evals = load_all_evaluations('evaluations_gemini')

    # Find common evaluations
    common_keys = set(claude_evals.keys()) & set(gpt4o_evals.keys()) & set(gemini_evals.keys())

    disagreements = []

    for (question_id, model_name) in common_keys:
        claude = claude_evals[(question_id, model_name)]
        gpt4o = gpt4o_evals[(question_id, model_name)]
        gemini = gemini_evals[(question_id, model_name)]

        # Check if judges agree on pass/fail
        claude_pass = claude['total_score'] >= 4
        gpt4o_pass = gpt4o['total_score'] >= 4
        gemini_pass = gemini['total_score'] >= 4

        # Count agreements
        pass_votes = sum([claude_pass, gpt4o_pass, gemini_pass])

        if pass_votes == 3 or pass_votes == 0:
            # All agree
            agreement = 'UNANIMOUS'
        elif pass_votes == 2 or pass_votes == 1:
            # 2-1 split
            agreement = 'SPLIT'

        # Detect bias patterns
        bias = None
        if 'claude' in model_name.lower():
            if claude_pass and not gpt4o_pass:
                bias = 'CLAUDE_FAVORS_CLAUDE'
        elif 'openai' in model_name.lower() or 'gpt' in model_name.lower() or 'o3' in model_name.lower():
            if gpt4o_pass and not claude_pass:
                bias = 'GPT4O_FAVORS_OPENAI'
        elif 'gemini' in model_name.lower() or 'google' in model_name.lower():
            if gemini_pass and not claude_pass and not gpt4o_pass:
                bias = 'GEMINI_FAVORS_GOOGLE'

        disagreements.append({
            'question_id': question_id,
            'agent_model': model_name,
            'claude_score': claude['total_score'],
            'gpt4o_score': gpt4o['total_score'],
            'gemini_score': gemini['total_score'],
            'claude_pass': claude_pass,
            'gpt4o_pass': gpt4o_pass,
            'gemini_pass': gemini_pass,
            'agreement': agreement,
            'suspected_bias': bias
        })

    df = pd.DataFrame(disagreements)

    # Analysis
    print("="*80)
    print("CROSS-JUDGE ANALYSIS")
    print("="*80)

    unanimous = len(df[df['agreement'] == 'UNANIMOUS'])
    split = len(df[df['agreement'] == 'SPLIT'])

    print(f"\nAgreement Rate: {unanimous/len(df):.1%}")
    print(f"  Unanimous (all 3 judges agree): {unanimous}/{len(df)}")
    print(f"  Split (2-1 disagreement): {split}/{len(df)}")

    # Bias analysis
    bias_counts = df['suspected_bias'].value_counts()
    print(f"\nSuspected Same-Family Bias:")
    for bias_type, count in bias_counts.items():
        if bias_type:
            print(f"  {bias_type}: {count} cases")

    # Export splits for manual review
    splits = df[df['agreement'] == 'SPLIT']
    splits.to_csv('analysis/judge_splits.csv', index=False)

    print(f"\n{'='*80}")
    print(f"Exported {len(splits)} split decisions to analysis/judge_splits.csv")
    print(f"REVIEW THESE to find real failures vs judge disagreements")
    print("="*80)

    return df

if __name__ == '__main__':
    df = compare_judges()
```

**Expected output**:
```
================================================================================
CROSS-JUDGE ANALYSIS
================================================================================

Agreement Rate: 62%
  Unanimous (all 3 judges agree): 137/220
  Split (2-1 disagreement): 83/220

Suspected Same-Family Bias:
  CLAUDE_FAVORS_CLAUDE: 18 cases
  GPT4O_FAVORS_OPENAI: 9 cases
  GEMINI_FAVORS_GOOGLE: 4 cases

================================================================================
Exported 83 split decisions to analysis/judge_splits.csv
REVIEW THESE to find real failures vs judge disagreements
================================================================================
```

---

## 🎯 How to Use These Methods

### **Priority Order**:

1. **Ground Truth Validation** (DO THIS FIRST - 2 hours)
   - Create ground truth for 5-10 common questions
   - Run automated comparison
   - Identify objective failures vs judge bias
   - **This gives you confidence in WHAT is actually wrong**

2. **Manual Spot Check** (DO THIS SECOND - 2 hours)
   - Review 10 random cases as human expert
   - Calculate your agreement with judge
   - Identify systematic bias patterns
   - **This calibrates your trust in the judge**

3. **Cross-Judge Validation** (OPTIONAL - 4 hours)
   - Only if budget allows (~$10-20 for 200 evals × 2 judges)
   - Identifies subjective cases (judges disagree)
   - Quantifies same-family bias
   - **This is overkill for now, but useful later**

---

## ✅ What You'll Learn

After running these validations:

### **Scenario A: Judge is mostly correct** (70-80% agreement with ground truth)
→ Trust the failures, proceed with error analysis
→ Focus on fixing agent issues, not judge issues

### **Scenario B: Judge has systematic bias** (50-60% agreement, patterns by model family)
→ Fix judge rubric FIRST before analyzing failures
→ Relax thresholds or add better examples to prompt
→ Re-run evaluations with improved judge

### **Scenario C: Judge is unreliable** (<50% agreement)
→ Don't trust ANY judge scores yet
→ Focus on ground truth validation only
→ Build better rubric from scratch

---

## 🚀 Start Today (2 Hours)

```bash
# Hour 1: Create ground truth + automated validation
# 1. Pick 5 questions you KNOW the answer to
# 2. Add to data/ground_truth_simple.json
# 3. Run validation script
python scripts/validate_against_ground_truth.py

# Hour 2: Manual spot check
# 1. Sample 10 random evaluations
# 2. For each: check agent answer vs literature yourself
# 3. Document where you agree/disagree with judge
```

**After 2 hours, you'll know**:
- ✅ What % of failures are REAL vs judge bias
- ✅ Whether same-family bias is significant
- ✅ Whether to trust Claude judge or fix it first

**This answers your question**: "How do I ensure failures are actually failures?"

**Answer**: By validating against objective ground truth, not another LLM. 🎯
