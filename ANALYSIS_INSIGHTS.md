# Analysis Insights: Model Performance Deep Dive

*Last updated: October 8, 2025*

---

## Executive Summary

Analysis of 191 agent runs across 9 models on 22 chemistry questions reveals surprising efficiency paradoxes and clear performance patterns. Key finding: **o3 is the fastest and most token-efficient model but scores the lowest**, using only 21% of average tool calls.

---

## 📊 Overall Performance Rankings

| Rank | Model | Weighted Score | Evaluations |
|------|-------|---------------|-------------|
| 🥇 1 | Claude Sonnet 4.5 | 87.0% | 22/22 |
| 🥈 2 | Claude Sonnet 4 | 86.0% | 20/22 |
| 🥉 3 | Claude Opus 4.1 | 85.1% | 22/22 |
| 4 | Gemini 2.5 Pro | 69.2% | 22/22 |
| 5 | GPT-5 | 63.6% | 20/22 |
| 6 | Grok Code Fast 1 | 59.9% | 21/22 |
| 7 | Grok 4 Fast | 54.7% | 25/22 |
| 8 | DeepSeek v3.1 | 51.9% | 27/22 |
| 9 | o3 | 33.7% | 22/22 |

---

## 🔍 The o3 Paradox

### Why Does o3 Score So Low Despite Being So Efficient?

**o3 Statistics:**
- ⚡ Fastest: 87.5s average (32% faster than next fastest)
- 💰 Cheap: $0.083 per question
- 🪙 Most token-efficient: 93,430 tokens (16% of average)
- 🔧 **Fewest tool calls: 4.6 average (21% of average)**
- ❌ **Lowest score: 33.7% weighted**

### The Root Cause: Tool Underutilization

o3 completes all tasks successfully (100% completion rate) but uses drastically fewer chemistry tools than other models:

| Model | Avg Tool Calls | Weighted Score |
|-------|---------------|---------------|
| GPT-5 | 22.4 | 63.6% |
| DeepSeek | 13.0 | 51.9% |
| Gemini | 12.5 | 69.2% |
| Claude models | 11-12 | 85-87% |
| **o3** | **4.6** | **33.7%** |

**Hypothesis:** o3's advanced reasoning capabilities allow it to provide plausible-sounding answers with minimal tool use, but in domain-specific tasks requiring computational validation (chemistry calculations), this leads to incorrect results. It's reasoning its way to answers instead of computing them.

### Evidence from Tool Success Rate

- o3 tool success rate: 95.5% (when it DOES call tools, they work)
- Problem: It just doesn't call tools often enough
- All other models: 100% tool success rate with 2-5x more tool calls

**Conclusion:** o3 needs prompt engineering to encourage more aggressive tool use in computational chemistry tasks.

---

## 💰 Cost Efficiency Analysis

### Cost per Question

| Model | Avg Cost | Total Cost (22 runs) | Cost Category |
|-------|----------|---------------------|---------------|
| DeepSeek v3.1 | $0.000 | $0.00 | FREE ✨ |
| Grok 4 Fast | $0.000 | $0.00 | FREE ✨ |
| Grok Code Fast 1 | $0.014 | $0.30 | Nearly Free |
| o3 | $0.083 | $1.82 | Budget |
| GPT-5 | $0.146 | $2.92 | Budget |
| Gemini 2.5 Pro | $0.176 | $3.86 | Budget |
| Claude Sonnet 4.5 | $0.492 | $10.83 | Mid-tier |
| Claude Sonnet 4 | $0.865 | $17.30 | Mid-tier |
| **Claude Opus 4.1** | **$5.284** | **$116.25** | **Premium** |

### Cost vs Performance

**Best Value (Performance per Dollar):**
1. **DeepSeek v3.1**: FREE with 51.9% score (decent for no cost)
2. **Grok 4 Fast**: FREE with 54.7% score
3. **Claude Sonnet 4.5**: $0.49 per question, 87.0% score = **177% per dollar**
4. Gemini 2.5 Pro: $0.18 per question, 69.2% score = 383% per dollar

**Worst Value:**
- Claude Opus 4.1: $5.28 per question, 85.1% score = 16% per dollar
- Still excellent quality, but 11x more expensive than Sonnet 4.5 for similar performance

**Recommendation:** For production chemistry workflows, Claude Sonnet 4.5 offers the best balance of performance and cost.

---

## ⚡ Speed Analysis

### Execution Time per Question

| Model | Avg Time | Median Time | Fastest Run | Slowest Run |
|-------|----------|-------------|-------------|-------------|
| **o3** | **87.5s** | **82.5s** | Fast | Fast |
| Grok 4 Fast | 240.2s | 70.5s | Very fast | Slow outliers |
| Grok Code Fast 1 | 319.9s | 93.4s | Fast | Variable |
| GPT-5 | 444.3s | 402.2s | Consistent | Consistent |
| Claude Opus 4.1 | 520.9s | 340.7s | Moderate | Variable |
| DeepSeek v3.1 | 542.6s | 193.3s | Moderate | Variable |
| Claude Sonnet 4.5 | 580.5s | 380.2s | Moderate | Moderate |
| Claude Sonnet 4 | 649.7s | 285.2s | Moderate | Slow |
| **Gemini 2.5 Pro** | **976.1s** | **255.7s** | Moderate | **Very slow** |

**Key Observations:**
- **o3 is consistently fast** - both mean and median are low
- **Gemini has high variance** - median is reasonable (255s) but mean is high (976s) due to slow outliers
- **Grok models are fast** when they work, but have variable performance
- **Claude models are consistent** - predictable execution times

---

## 🪙 Token Efficiency

### Average Tokens per Question

| Model | Avg Tokens | Token Efficiency Rank |
|-------|-----------|---------------------|
| **o3** | **93,430** | **🥇 Most Efficient** |
| Grok 4 Fast | 191,782 | 🥈 |
| Grok Code Fast 1 | 200,482 | 🥉 |
| Gemini 2.5 Pro | 207,386 | Good |
| DeepSeek v3.1 | 216,807 | Good |
| Claude Sonnet 4.5 | 259,621 | Moderate |
| Claude Sonnet 4 | 279,285 | Moderate |
| Claude Opus 4.1 | 343,129 | Lower |
| **GPT-5** | **576,013** | **⚠️ Least Efficient** |

**Analysis:**
- o3 uses **84% fewer tokens** than average
- GPT-5 uses **6.2x more tokens** than o3
- Claude models use moderate tokens but achieve highest scores

**Tokens vs Performance:**
- More tokens ≠ better performance
- GPT-5: highest tokens (576K), mid-tier score (63.6%)
- Claude Sonnet 4.5: moderate tokens (260K), highest score (87.0%)
- o3: lowest tokens (93K), lowest score (33.7%)

**Conclusion:** Token efficiency alone doesn't predict performance. Quality of tool usage matters more than quantity of tokens.

---

## 🔧 Tool Usage Patterns

### Tool Calls per Question

| Model | Avg Tool Calls | Tool Success Rate | Pattern |
|-------|---------------|------------------|---------|
| GPT-5 | 22.4 | 100% | **Over-user** 🔨 |
| DeepSeek v3.1 | 13.0 | 100% | Heavy user |
| Gemini 2.5 Pro | 12.5 | 100% | Balanced |
| Claude Sonnet 4.5 | 12.0 | 100% | Balanced ✓ |
| Claude Sonnet 4 | 11.5 | 100% | Balanced |
| Grok Code Fast 1 | 11.4 | 100% | Balanced |
| Claude Opus 4.1 | 11.2 | 100% | Balanced |
| Grok 4 Fast | 8.7 | 100% | Light user |
| **o3** | **4.6** | **95.5%** | **Under-user** ⚠️ |

### Tool Usage Patterns by Model Family

**Anthropic (Claude):**
- Consistent 11-12 tool calls per question
- 100% tool success rate
- Achieves highest scores (85-87%)
- **Pattern:** Balanced, effective tool orchestration

**OpenAI:**
- **GPT-5:** Calls 22.4 tools (2x average) - may be retrying or over-validating
- **o3:** Calls only 4.6 tools (42% of average) - relies on reasoning over computation
- Both have 95-100% success rates when tools are called

**Google (Gemini):**
- 12.5 tool calls (balanced)
- 100% success rate
- Mid-tier performance (69.2%)

**Open-source (DeepSeek, Grok):**
- DeepSeek: Heavy tool user (13 calls), good success
- Grok: Light tool usage (8.7-11.4 calls)
- Variable performance (52-60%)

### Insights

1. **More tools ≠ better scores:** GPT-5 uses most tools but scores mid-tier
2. **Too few tools = poor scores:** o3 uses fewest tools and scores lowest
3. **Sweet spot appears to be 11-12 tool calls** for chemistry tasks
4. **Tool success rate is universally high** (95-100%) - models know HOW to use tools, question is WHEN/HOW OFTEN

---

## 🧠 Reasoning Token Usage

Some models use explicit "reasoning tokens" (internal chain-of-thought):

| Model | Avg Reasoning Tokens | Has Explicit CoT |
|-------|---------------------|------------------|
| GPT-5 | 4,470 | ✓ Extended thinking |
| Grok Code Fast 1 | 2,728 | ✓ |
| Gemini 2.5 Pro | 2,419 | ✓ |
| Grok 4 Fast | 1,778 | ✓ |
| o3 | 1,059 | ✓ Compact |
| Claude models | 0 | ✗ (different architecture) |
| DeepSeek | 0 | ✗ |

**Observation:** GPT-5 uses the most reasoning tokens (4.5K) AND the most tool calls (22.4) - it's both thinking hard AND working hard, but still achieves only 63.6%.

---

## 📈 Performance by Tier

All models maintain high completion rates across difficulty tiers:

| Model | Tier 1 | Tier 2 | Tier 3 | Pattern |
|-------|--------|--------|--------|---------|
| Claude models | 100% | 100% | 100% | Consistent excellence |
| Gemini | 100% | 100% | 100% | Consistent |
| Grok models | 100% | 100% | 100% | Consistent |
| DeepSeek | 80% | 100% | 100% | Tier 1 struggles |
| GPT-5 | (incomplete data) | | | |
| o3 | 100% | 100% | 100% | Completes but scores low |

**Key Finding:** Completion rate is NOT the issue - all models finish tasks. The issue is **correctness** of results, which requires proper tool usage.

---

## 💡 Key Takeaways & Recommendations

### 1. **For Production Chemistry Workflows**
**Recommended:** Claude Sonnet 4.5
- Best balance: 87.0% score, $0.49/question
- Consistent performance across all tiers
- Reliable tool orchestration

**Budget Option:** DeepSeek v3.1 or Grok 4 Fast
- FREE or nearly free
- Decent performance (52-55%)
- Good for non-critical tasks

### 2. **The o3 Challenge**
o3 needs specialized prompting:
- Explicitly encourage tool usage
- Penalize reasoning-only answers
- Require computational validation
- Consider o3 for reasoning tasks, not computational chemistry

### 3. **Tool Usage Patterns**
- **Optimal range:** 11-12 tool calls per question
- **Under 5 tools:** Likely poor results (o3 pattern)
- **Over 20 tools:** Possibly inefficient (GPT-5 pattern)
- **Tool success rate is high across all models** - the key differentiator is frequency of use

### 4. **Cost-Performance Tradeoffs**
- Claude Opus 4.1: Premium pricing for 2% better performance than Sonnet 4.5 (not worth it)
- Claude Sonnet 4.5: Best value for high performance
- Free models (DeepSeek, Grok): Good for exploration or budget-constrained use cases

### 5. **Speed Requirements**
- **Need speed?** Use o3 (87s avg) - but validate results heavily
- **Need reliability?** Use Claude Sonnet 4.5 (580s avg) - consistent quality
- **Avoid:** Gemini if time-sensitive (976s avg with high variance)

---

## 🔮 Future Analysis Ideas

### Additional Visualizations Needed:

1. **Tool Call Success Rate vs Score** - scatter plot to show correlation
2. **Tier-Specific Performance Breakdown** - grouped bar chart by model and tier
3. **Token Breakdown Stacked Bar** - show prompt/completion/reasoning token allocation
4. **Cost per Point Scored** - efficiency metric: cost / weighted_score
5. **Time vs Tool Calls Correlation** - identify inefficient tool users
6. **Reasoning Token Usage vs Score** - does more thinking = better chemistry?

### Questions to Investigate:

1. **What specific tools is o3 NOT calling?**
   - Analyze tool call logs to see which chemistry calculations o3 skips

2. **Why does GPT-5 call so many tools?**
   - Is it retrying failed calls? Validating results multiple times?

3. **What makes tier1_001 (trick question) challenging?**
   - Deep dive into how models handled the water-insoluble drug question

4. **Judge agreement patterns**
   - Compare Claude vs Qwen judge scores - evidence of bias?

5. **Human validation**
   - Create golden dataset with expert-labeled answers for all 22 questions

---

## 📁 Data Files

All analysis data saved to `analysis/` directory:
- `model_efficiency_stats.csv` - Summary statistics by model
- `all_log_data.csv` - Full execution logs dataset
- `o3_analysis.csv` - Detailed o3 performance data
- `tool_use_stats.csv` - Tool usage patterns

All visualizations in `plots/` directory:
- `weighted_score_performance.png` - Main performance chart
- `cost_efficiency.png` - Cost per question
- `speed_comparison.png` - Execution time
- `token_usage.png` - Token efficiency
- `tool_usage.png` - Tool call patterns
- `o3_paradox.png` - The o3 efficiency paradox
- `cost_vs_performance.png` - Cost-performance scatter

---

*Analysis based on 191 agent execution logs across 22 chemistry benchmark questions.*
