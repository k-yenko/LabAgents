# Opus Model Cost Analysis - Excessive Polling Issue

## Summary
This document analyzes the high costs associated with Claude Opus 4.1 model runs on computational chemistry questions. The primary issue identified was excessive polling at 300-second intervals instead of using proper exponential backoff, leading to unnecessarily high API costs.

## Total Costs Overview
| Question ID | Total Cost (USD) | Execution Time (min) | API Calls | Tokens | Status | Main Issue |
|-------------|------------------|---------------------|-----------|---------|--------|------------|
| **tier1_001** | $2.17 | 2.5 | 8 | 139,758 | ✅ Completed | Moderate polling |
| **tier1_002** | $2.93 | 12.2 | 10 | 188,017 | ✅ Completed | Long polling (666s) |
| **tier1_003** | $3.03 | 4.1 | 10 | 195,337 | ✅ Completed | Moderate polling (163s) |
| **tier1_004** | $1.73 | 1.6 | 5 | 108,881 | ✅ Completed | Quick completion |
| **tier3_004** | $4.81 | 13.6 | 15 | 309,771 | ✅ Completed | Excessive polling (641s) |
| **tier1_005** | **~$60.00** | **~60+ min** | **100+** | **~3M** | ❌ **Killed** | **EXCESSIVE POLLING BUG** |

**TOTAL COST: ~$74.67 across 6 questions**

## Critical Issue: tier1_005 - The $60 Runaway Process

### What Happened
- **Cost**: Approximately $60 in API calls
- **Duration**: Over 1 hour of continuous execution
- **API Calls**: 100+ iterations of workflow polling
- **Problem**: Agent got stuck polling every 300 seconds instead of using exponential backoff

### Polling Pattern Analysis
**Expected exponential backoff:**
```
10s → 20s → 40s → 80s → 160s → 300s (max)
```

**What actually happened:**
```
IMMEDIATELY jumped to 300s and stayed there for 100+ iterations
"Waiting another 300 seconds..." (repeated endlessly)
```

### Cost Breakdown for tier1_005
- **Iterations 1-100+**: ~$0.58 per API call × 100+ calls = $58+
- **Token usage**: ~38,000 tokens per iteration (massive context)
- **Time wasted**: 300s × 100+ = 30,000+ seconds (8+ hours of polling time)

## Root Cause Analysis

### System Prompt Issue
The agent was not properly tracking which polling check it was on, causing it to:
1. Skip the exponential backoff sequence entirely
2. Jump straight to maximum wait time (300s)
3. Repeat maximum wait time indefinitely
4. Burn through API credits with no progress

### Context Bloat
Each iteration added more context:
- Previous workflow status responses
- Repeated reasoning about waiting
- Growing conversation history
- Led to 38,000+ tokens per API call

## Fix Applied

### Enhanced System Prompt
Updated the system prompt to explicitly track polling attempts:

```
- MANDATORY SMART POLLING - you MUST follow this exact pattern and track your count:
  * Submit workflow → "I'll check status in 10 seconds (check #1)"
  * 1st check: Wait EXACTLY 10 seconds → call workflow_get_status
  * If still running: "I'll wait 20 seconds before next check (check #2)"
  * 2nd check: Wait EXACTLY 20 seconds → call workflow_get_status
  * If still running: "I'll wait 40 seconds before next check (check #3)"
  * 3rd check: Wait EXACTLY 40 seconds → call workflow_get_status
  * If still running: "I'll wait 80 seconds before next check (check #4)"
  * 4th check: Wait EXACTLY 80 seconds → call workflow_get_status
  * If still running: "I'll wait 160 seconds before next check (check #5)"
  * 5th check: Wait EXACTLY 160 seconds → call workflow_get_status
  * If still running: "I'll wait 300 seconds before next check (check #6+)"
  * 6th+ checks: Always wait EXACTLY 300 seconds between checks
- CRITICAL: You must TRACK which check number you're on and use the correct wait time
```

## Cost Per Question Analysis

### Successful Completions
- **tier1_001** ($2.17): Aqueous solubility calculation - reasonable cost
- **tier1_002** ($2.93): pKa calculation with careful mode - acceptable for complexity
- **tier1_003** ($3.03): Tautomer enumeration - moderate cost
- **tier1_004** ($1.73): Simple descriptors - most efficient
- **tier3_004** ($4.81): Complex multi-workflow analysis - high but justified

### Failed Execution
- **tier1_005** (~$60): Simple molecular property question that should have cost ~$2-3

## Lessons Learned

1. **Smart polling is critical** for cost control on long-running workflows
2. **Opus model is expensive** (~$0.58 per complex API call)
3. **Context management** is crucial to prevent token bloat
4. **Process monitoring** is needed to catch runaway executions
5. **Exponential backoff** must be explicitly enforced in prompts

## Recommendations Going Forward

1. **Use Claude Sonnet 4** for remaining questions (much cheaper)
2. **Test smart polling** on a simple question first
3. **Monitor costs** in real-time during execution
4. **Set budget limits** or timeouts for expensive model runs
5. **Always kill runaway processes** immediately

## Financial Impact

The tier1_005 runaway execution cost approximately **30x more** than it should have, turning a $2 question into a $60 expense. This highlights the critical importance of proper polling logic in computational workflows using expensive LLM models.

---
*Analysis date: September 24, 2025*
*Total financial impact: ~$74.67 for 6 questions (expected cost: ~$15)*