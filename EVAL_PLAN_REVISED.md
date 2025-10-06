# Rigorous Evaluation Plan (Revised Based on Hamel's Principles)

**Key insight from Hamel**: "The abuse of generic metrics is endemic. Spend 60-80% of development time on error analysis, not building complex evaluation infrastructure."

---

## 🎯 What We Have vs What We Actually Need

### ✅ What's Working
1. **Web search validation** - Judge validates against real literature (DONE)
2. **Concrete rubric** - Specific thresholds, auditable reasoning (DONE)
3. **Full execution logs** - Can trace every tool call
4. **22 chemistry questions** - Specific domain, clear success criteria

### ❌ What's Missing (Per Hamel)
1. **Systematic error analysis** - Haven't categorized WHY models fail
2. **Human ground truth** - No expert-annotated "correct" answers
3. **Iterative improvement loop** - No process to learn from failures
4. **Domain-specific insights** - Generic "pass/fail" hides chemistry-specific issues

---

## 🚨 Critical Corrections to Current Plan

### **Phase 2-7 from EVAL_PLAN.md are PREMATURE**

Hamel's principle: **"Don't build evaluators for hypothetical failures"**

Current plan jumps to:
- ❌ Multi-judge ensemble (Phase 4)
- ❌ Expert calibration with Cohen's kappa (Phase 5)
- ❌ Complex error taxonomy infrastructure (Phase 6)
- ❌ Weekly automation workflows (Phase 7)

**Problem**: You haven't done error analysis yet! You're building infrastructure before understanding what actually fails.

---

## ✅ What You SHOULD Do (Hamel-Aligned)

### **Phase 1: Web Search ✅ DONE**
- Real literature validation
- Citations with URLs
- Objective correctness scoring

**Keep this. It's good.**

---

### **Phase 2: Manual Error Analysis (DO THIS NEXT - 1 week)**

**Hamel quote**: "Spend 60-80% of development time on error analysis."

#### **Step 1: Review 20-50 Failures Manually** (2-3 days)

```bash
# Get all failures (score < 4)
python -c "
import json, glob, os

failures = []
for eval_file in glob.glob('evaluations/*/json/*_evaluation.json'):
    with open(eval_file) as f:
        data = json.load(f)
        if data['total_score'] < 4:
            failures.append({
                'file': eval_file,
                'question': data['question_id'],
                'model': eval_file.split('/')[-1].replace('_evaluation.json', ''),
                'score': data['total_score']
            })

print(f'Found {len(failures)} failures')
for f in failures[:20]:  # First 20
    print(f\"{f['question']}: {f['model']} (score {f['score']})\")
"
```

**For each failure, manually review**:
1. Read the agent's execution log
2. Read the judge's reasoning
3. Read the cited literature
4. **Write notes**: What SPECIFICALLY went wrong?

**Create**: `analysis/manual_error_review.md`

```markdown
# Manual Error Review Notes

## tier1_001: remdesivir solubility
**Model**: anthropic/claude-sonnet-4
**Score**: 4/6 (Completion: 2, Correctness: 0, Tool: 2)

### What Actually Happened
- Agent used FastSolv ML model
- Predicted 15.0 mg/mL
- Literature value: 0.339 mg/mL
- Error: 4400%

### Why Did This Fail?
- FastSolv model known to be inaccurate for complex drug molecules
- Agent didn't validate SMILES complexity before choosing method
- No sanity check against "poorly water-soluble drug" descriptor

### Chemistry Insight
- Remdesivir has large molecular weight (602 g/mol)
- Multiple functional groups → high polarity
- Should have triggered DFT method, not ML

### Pattern?
- Check if other tier1 drug molecules also failed with ML methods
- May need to add "molecular complexity → method selection" guidance

---

## tier2_003: aspirin pKa
**Model**: google/gemini-2.5-pro
**Score**: 2/6 (Completion: 0, Correctness: 0, Tool: 2)

### What Actually Happened
- Agent selected correct tools (pKa workflow)
- Submitted workflow successfully
- **Never retrieved results** - workflow timed out
- Gave up and said "cannot complete"

### Why Did This Fail?
- Workflow status showed "running" for 180+ seconds
- Agent checked status once, saw "running", assumed failure
- Never implemented exponential backoff for status checking

### Pattern?
- Is this gemini-specific? Or workflow-specific?
- Check other gemini failures - may be impatience with long computations
- Or: tier2 workflows genuinely slower?

---

[Continue for 20-50 failures...]
```

---

#### **Step 2: Open Coding - Identify Patterns** (1-2 days)

After reviewing 20-50 failures, group them:

```markdown
# Failure Pattern Categories (Discovered from Manual Review)

## Category 1: Wrong Method Selection (8 failures)
**What**: Agent chose inappropriate computational method for molecule complexity
**Examples**:
- tier1_001 (remdesivir): Used ML instead of DFT for large drug
- tier1_005 (ibuprofen): Used semiempirical for charged molecule
- tier2_001 (caffeine): Used ML for aromatic system

**Root Cause**: No guidance on method selection based on molecular features
**Fix**: Add method selection flowchart to system prompt

---

## Category 2: Workflow Timeout Impatience (5 failures)
**What**: Agent gave up on running workflows after 1 status check
**Examples**:
- tier2_003 (aspirin): Checked once at 60s, saw "running", quit
- tier3_001 (complex): Checked once at 120s, quit

**Root Cause**: No exponential backoff for workflow status
**Fix**: Already implemented in system_prompt_template.py (may need to re-run)

---

## Category 3: SMILES Validation Errors (3 failures)
**What**: Invalid SMILES passed to workflow, calculation failed
**Examples**:
- tier1_007: Used ionized form SMILES, should be neutral
- tier2_005: Wrong tautomer selected

**Root Cause**: Agent doesn't understand protonation states
**Fix**: Add SMILES validation examples to prompt

---

## Category 4: Result Interpretation Errors (2 failures)
**What**: Agent correctly computed but misinterpreted units
**Examples**:
- tier1_003: Reported pKa = 14 (actually was Ka = 10^-14, pKa = 14)
- tier2_002: Confused logP with logD

**Root Cause**: Unclear output format from workflows
**Fix**: Clarify unit expectations in prompt

---

## Category 5: Judge Errors (4 failures)
**What**: Agent was actually correct, but judge scored wrong
**Examples**:
- tier1_002: Agent got 4.8, literature 4.76, judge gave 0/2 (should be 2/2)
- tier3_002: Judge couldn't find literature, guessed wrong

**Root Cause**: Judge rubric too strict OR web search failed
**Fix**: Review judge threshold, improve web search queries

---

[THIS is your actual error taxonomy - discovered, not assumed]
```

---

#### **Step 3: Prioritize Fixes** (1 day)

**Hamel quote**: "Don't build evaluators for hypothetical failures."

Based on discovered patterns above, prioritize:

```markdown
# Fix Priority (Based on Frequency & Impact)

## 🔥 Immediate (This Week)
1. **Method Selection Guidance** (8 failures, 40% of reviewed)
   - Add to system prompt: "For MW > 500 Da, use DFT not ML"
   - Add: "For charged molecules, avoid semiempirical"
   - **Test on**: tier1_001, tier1_005, tier2_001
   - **Expected**: 6-8 failures → passes

2. **Judge Threshold Tuning** (4 failures, 20%)
   - Relax pKa threshold from ±0.5 to ±0.6 units
   - Clarify "close enough" vs "wrong"
   - **Test on**: tier1_002, tier3_002
   - **Expected**: 3-4 failures → passes

## 📅 Next Week
3. **SMILES Protonation Guidance** (3 failures, 15%)
   - Add examples of neutral form selection
   - **Test on**: tier1_007, tier2_005

4. **Result Interpretation Examples** (2 failures, 10%)
   - Add Ka vs pKa clarification
   - Add logP vs logD examples

## ⏸️ Maybe Later
5. **Workflow Timeout** - Already fixed in system prompt, needs re-run
6. **Multi-judge ensemble** - NOT NEEDED yet, judge errors are fixable
7. **Expert calibration** - DEFER until we fix obvious issues first
```

---

### **Phase 3: Implement Top Fixes & Re-Evaluate** (3-5 days)

#### **3.1 Add Method Selection Guidance** (2 hours)

```python
# In system_prompt_template.py, add to computational chemistry section:

COMPUTATIONAL METHOD SELECTION:

Before submitting any calculation, check molecular features:

1. **Molecular Weight Check**:
   - MW < 300 Da → ML methods (FastSolv, XLogP) acceptable
   - MW 300-500 Da → Prefer DFT but ML acceptable
   - MW > 500 Da → MUST use DFT/high-level methods

   Example: Remdesivir (MW 602) → Use DFT, not FastSolv

2. **Charge State Check**:
   - Neutral molecule → Any method
   - Charged/ionized → MUST use DFT (semiempirical fails)

   Example: Protonated amine → Use DFT B3LYP, not AM1

3. **Complexity Check**:
   - Simple organics (alkanes, alcohols) → ML acceptable
   - Aromatics, heterocycles → Prefer DFT
   - Drugs, natural products → MUST use DFT

   Example: Aspirin (aromatic + carboxyl) → DFT preferred

**CRITICAL**: If in doubt, use DFT. It's slower but more accurate.
```

**Test this**:
```bash
# Re-run the 8 "wrong method" failures
python openrouter_agent.py tier1_001 --model anthropic/claude-sonnet-4
python openrouter_agent.py tier1_005 --model anthropic/claude-sonnet-4
# ... etc

# Then re-evaluate
python llm_judge_evaluator.py tier1_001 --single logs/tier1_001/...
```

**Track improvement**:
```bash
# Before fix: 8 failures
# After fix: ? failures
# Delta: X failures fixed
```

---

#### **3.2 Adjust Judge Rubric** (1 hour)

```python
# In llm_judge_evaluator.py, update CORRECTNESS section:

Score 2/2 IF:
  ✓ pKa: within ±0.6 units (was ±0.5) ← RELAXED based on error analysis
  ✓ logP: within ±0.4 units (was ±0.3) ← RELAXED
  ✓ Solubility: within ±60% (was ±50%) ← RELAXED

# Justification from error analysis:
# - tier1_002: Agent got 4.8, lit 4.76, diff 0.04 → was scored 0, should be 2
# - DFT methods typically ±0.5 units, ML methods ±0.8 units
# - Being TOO strict creates false negatives
```

**Re-evaluate ALL evaluations** (judge scores may change):
```bash
# Archive old evaluations
mv evaluations evaluations_v1_strict

# Re-run with relaxed rubric
python scripts/run_all_missing_evals.py
```

**Compare before/after**:
```python
import json, glob

old = [json.load(open(f)) for f in glob.glob('evaluations_v1_strict/*/json/*.json')]
new = [json.load(open(f)) for f in glob.glob('evaluations/*/json/*.json')]

old_pass_rate = sum(1 for e in old if e['total_score'] >= 4) / len(old)
new_pass_rate = sum(1 for e in new if e['total_score'] >= 4) / len(new)

print(f"Pass rate change: {old_pass_rate:.1%} → {new_pass_rate:.1%}")
print(f"False negatives fixed: {(new_pass_rate - old_pass_rate) * len(old):.0f}")
```

---

#### **3.3 Document What You Learned** (1 hour)

```markdown
# analysis/iteration_1_learnings.md

## Iteration 1: Manual Error Analysis + Targeted Fixes

### What We Did
1. Manually reviewed 20 failure cases
2. Discovered 5 actual failure categories (not hypothetical!)
3. Implemented 2 highest-impact fixes:
   - Method selection guidance
   - Relaxed judge thresholds

### Results
**Before fixes**:
- Pass rate: 65% (143/220 model-question pairs)
- Common failures: Wrong method (8), Judge too strict (4)

**After fixes**:
- Pass rate: 78% (172/220)
- Failures fixed: 29 → 12 new passes
- Remaining failures: Need next iteration

### Key Insights
1. **FastSolv ML fails for drugs** - MW > 500 Da needs DFT
2. **Judge was too strict** - ±0.5 pKa too tight for DFT accuracy
3. **Most failures are fixable** - Not model capability issues, but guidance issues

### Next Iteration Focus
- SMILES protonation errors (3 remaining)
- Result interpretation (2 remaining)
- Actually hard questions (identify which are genuinely difficult)
```

---

### **Phase 4: Iterate (Ongoing, 2-week cycles)**

**Hamel quote**: "Typical review cycles: 2-4 weeks"

Every 2 weeks:

#### **Week 1: Run & Review**
```bash
# Monday: Run any new models or questions
python scripts/run_all_missing.py

# Tuesday-Thursday: Manual review of NEW failures
# - Pick 10-20 new failures
# - Read logs, take notes
# - Identify patterns

# Friday: Document learnings
```

#### **Week 2: Fix & Validate**
```bash
# Monday-Wednesday: Implement targeted fixes
# - Update prompts
# - Adjust rubrics
# - Add examples

# Thursday: Re-run evaluations
python scripts/run_all_missing_evals.py

# Friday: Measure improvement, document
```

**Track progress**:
```markdown
# analysis/improvement_tracking.md

| Iteration | Date | Pass Rate | Fixes Applied | Notes |
|-----------|------|-----------|---------------|-------|
| 0 (baseline) | 2025-10-05 | 65% | None | Initial with strict judge |
| 1 | 2025-10-19 | 78% | Method selection, judge tuning | +13% from 2 fixes |
| 2 | 2025-11-02 | 84% | SMILES validation, units | +6% from 2 fixes |
| 3 | 2025-11-16 | 89% | ... | ... |
```

---

## 🎯 Revised Success Metrics (Hamel-Aligned)

### ❌ Don't Measure
- ~~Cohen's kappa~~ (premature without expert annotations)
- ~~Inter-judge agreement~~ (don't need ensemble yet)
- ~~Complex error taxonomy~~ (discover organically, don't impose)

### ✅ DO Measure
1. **Understanding of failures** - Can you explain each failure category?
2. **Fix velocity** - How fast can you go from failure → fix → validation?
3. **Improvement trajectory** - Is pass rate increasing iteration-over-iteration?
4. **Failure diversity** - Are failures spreading across categories or clustering?

**Good signs**:
- Pass rate increasing by 5-15% per iteration
- New failure categories discovered → fix → disappear
- After 3-4 iterations, failures cluster in "genuinely hard" questions

**Bad signs**:
- Pass rate stuck at same level
- Same failures recurring despite fixes
- Don't understand WHY failures happen

---

## 📋 Implementation Checklist (Revised)

### **Phase 1: Web Search ✅ DONE**
- [x] OpenRouter `:online` for literature validation
- [x] Citations extracted and enriched
- [x] Concrete rubric with thresholds
- [x] Tested on tier1_001

### **Phase 2: Manual Error Analysis (THIS WEEK)**
- [ ] Export all failures to CSV/JSON
- [ ] Manually review 20-50 failure cases
- [ ] Take detailed notes for each (use template above)
- [ ] Open coding: Identify 3-7 failure categories
- [ ] Prioritize by frequency & impact

### **Phase 3: Targeted Fixes (NEXT WEEK)**
- [ ] Implement top 2 fixes (method selection + judge tuning)
- [ ] Re-run affected evaluations
- [ ] Measure improvement (expect +10-15% pass rate)
- [ ] Document learnings

### **Phase 4: Iteration Cycle (ONGOING)**
- [ ] Set up 2-week review cadence
- [ ] Each cycle: review → fix → validate → document
- [ ] Track improvement trajectory
- [ ] Stop when diminishing returns (<5% improvement per cycle)

### **Phase 5: Expert Validation (LATER - After 3+ Iterations)**
- [ ] ONLY after you've exhausted obvious fixes
- [ ] Select 25 samples (mix of passes and remaining failures)
- [ ] Expert annotates: "Would I trust this answer?"
- [ ] Calculate agreement → identifies remaining blind spots

### **Phase 6: Multi-Judge (MAYBE - Only if Judge Errors Persist)**
- [ ] ONLY if >20% of failures are judge errors after fixes
- [ ] Try 1-2 other judges (GPT-4o, Gemini)
- [ ] Compare disagreements → reveals judge biases
- [ ] Decide: fix judge prompts OR use ensemble

---

## 🚨 What NOT to Do (Hamel's Warnings)

### ❌ Don't Build Infrastructure First
> "Don't build evaluators for hypothetical failures"

**Bad**: Building ensemble judges, error taxonomy systems, automation workflows

**Good**: Manually reviewing failures, taking notes, implementing targeted fixes

### ❌ Don't Optimize for High Pass Rates
> "A 70% pass rate might indicate more meaningful testing than 100%"

**Bad**: Relaxing rubric until everything passes

**Good**: Understanding WHY 30% fail, deciding if it's fixable or genuinely hard

### ❌ Don't Use Generic Metrics
> "The abuse of generic metrics is endemic"

**Bad**: "Agent uses tools efficiently" (vague)

**Good**: "Agent selected DFT for MW > 500 Da molecules" (specific, chemistry-relevant)

### ❌ Don't Skip Error Analysis
> "Spend 60-80% of development time on error analysis"

**Bad**: Running evaluations → implementing random fixes → hoping for improvement

**Good**: Running evaluations → manually reviewing failures → discovering patterns → targeted fixes

---

## 💡 Key Philosophy Shift

### Before (EVAL_PLAN.md)
- Build complex infrastructure (ensemble, expert calibration, automation)
- Assume generic evaluation best practices apply
- Optimize for metrics (kappa, correlation, pass rate)

### After (Hamel-Aligned)
- **Understand your specific failures first**
- Discover patterns through manual review
- Implement targeted fixes iteratively
- Build infrastructure ONLY when patterns demand it

**Quote from Hamel**:
> "I'm generally wary of tooling or tutorials that promise to help you evaluate your system without much manual work. The manual work is the point!"

---

## 🎯 Success Looks Like (After 1 Month)

Not this:
- ❌ Cohen's kappa > 0.6
- ❌ Multi-judge ensemble deployed
- ❌ Automated weekly workflows

But this:
- ✅ You can explain every failure category
- ✅ Pass rate improved 20-30% through targeted fixes
- ✅ Failures cluster in "genuinely hard" chemistry problems
- ✅ You know which models are good at what
- ✅ You have a 2-week iteration rhythm

**The goal isn't perfect evaluation infrastructure. It's understanding your agents' chemistry failures well enough to improve them.**

---

## 🚀 Start Today (1 Hour)

```bash
# 1. Export failures (10 min)
python -c "
import json, glob

failures = []
for f in glob.glob('evaluations/*/json/*_evaluation.json'):
    data = json.load(open(f))
    if data['total_score'] < 4:
        failures.append({
            'question': data['question_id'],
            'model': f.split('/')[-1].replace('_evaluation.json', ''),
            'completion': data['completion_score'],
            'correctness': data['correctness_score'],
            'tool_use': data['tool_use_score'],
            'total': data['total_score'],
            'log_file': f.replace('evaluations/', 'logs/').replace('json/', '').replace('_evaluation.json', '.json')
        })

import pandas as pd
pd.DataFrame(failures).to_csv('analysis/failures.csv', index=False)
print(f'Exported {len(failures)} failures to analysis/failures.csv')
"

# 2. Pick 5 failures to review (5 min)
head -6 analysis/failures.csv

# 3. Review first failure manually (30 min)
# - Read agent log
# - Read judge reasoning
# - Read literature citations
# - Write notes: What SPECIFICALLY went wrong?

# 4. Document your notes (15 min)
# Create analysis/manual_error_review.md with template above
```

**After 1 hour, you'll have**:
- List of all failures
- Deep understanding of 1 specific failure
- Notes template for the next 19

**Tomorrow**: Review 4 more failures (2 hours)

**End of week**: 20 failures reviewed, patterns identified, top 2 fixes implemented

**This is how you actually improve evaluations.** 🎯
