# 07 Sep 2025 // first eval treatise

## Intro and Motivation
I've spent some time reading on how to evaluate agentic tool-use and asking others in the field how they do it. This exploration has revealed just how nuanced this area is, and that there's no one-size-fits-all solution.  

The intersection of LLMs and computational biology/chemistry presents unique evaluation challenges. Software evaluations typically have seemingly clear metrics: hallucination rates, politeness scores, completeness, and sometimes correctness. On the other hand, chemistry benchmarks like ChemIQ [1], ChemBench [2], and other evaluations [3] focus on a model's ability to understand, reason and explain chemistry tasks.

A natural next step that emerged from discussions is evaluating agentic tool-use specifically for computational chemistry tasks. ChemCrow lies in sits nicely in this intersection, but systematic evaluation frameworks remain scarce. Unlike pure software evaluations, bio/chem evaluations deal with scientific correctness with some margin of error, requiring both computational accuracy and domain expertise validation. It wouldn't be enough to check if the model called the right function with the right parameters and gave you a polite response; it needs to understand the science. 

This project aims to develop a preliminary evaluation framework for assessing how well foundation models can agentically use computational chemsitry tools, specifically using Rowan for multi-step scientific reasoning and workflow orchestration.

## Questions and Task Hierarchy

Using deep research features on ChatGPT and Claude, 20 questions were generated spanning three tiers of complexity:

1. **Tier 1: Single Tool-Use**. Basic tasks requiring on computational tool or db lookup. These represent foudnational interactions with chemistry software.
 
2. **Tier 2: Multi-Tool Orchestration**. Tasks requiring workflow planning and independent calculations across multiple tools. Models must orchestrate differnet computational methods and synthesize results for a "final answer".

3. **Tier 3: Scientific Planning and Conditional Logic**. Complex tasks where outputs from oe workflow become inputs of another. Requires scientific reasoning, hypothesis generation, and adaptation during the workflow. 

For the initial evaluation, five Tier 2 and five Tier 3 questions were assessed.

## Evaluation Methodology

### Correctness: LLM-as-a-Judge
Used Claude Sonnet as an evaluator to assess the scientific accuracy and completeness of the final answers. I included literature-validated expected answers and allowed for the model to use external sources. 

### Function Calling: Code-Based Evaluation
Had a list of expected tools and implemented a code-based evaluation to check whether the models called all expected tools in any order, allowing for extra function calls. This assessment focuses purely on tool selection completeness rather than sequence and repetitiveness, so there's room for optimization (i.e. adding convergence scores to measure frivolous tool-calling). 

## Scoring System
A weighted scoring system was used, where Tier 2 tasks are worth 2 pts and Tier 3 tasks are worth 4 pts (max of 30 pts). The weights reflect increased complexity, though a more systematic approach could be used here since it was somewhat arbitrary. Difficulty assessment was based a bit off "vibes" rather than empirical validation. Models were evalauted both on correctness and function calling. 

## Results

![Correctness Evaluation Results](figures/weighted_performance_eval.png)

*Figure 1. Comparison of correctness across 8 popular foundation models on computational chemistry tasks. Results show GPT-5 leading, followed by Claude-4-sonnet, o3, Grok-4, Gemini-2.5-pro, Grok-code-fast-1, Claude-4.1-opus, and Deepseek-v3.1. Evaluation done using LLM-as-a-judge methodology with Claude Sonnet assessing scientific accuracy.*

![Function Calling Evaluation Results](figures/tool_selection_eval.png)

*Figure 2. Assessment of tool selection completeness across models. Claude 4 Sonnet achieved the highest score, calling all expected tools for most tasks. Evaluation was done with a code-based assessment, resulting in binary scoring: 1 for complete set of expected tool calls and 0 for incomplete.*

## There and back again (what I learned)

This is... very far from complete. 

*The art and science of evals:* running evaluations in this space truly exists at this intersection. On one hand, there exists objective correct and incorrect answers in chemistry; on the other hand, it feels like selecting meaningful metrics (and knowing when metrics start yielding diminishing returns) requires some intuition. 

*Data collection gaps:* you know what they say - hindsight is 20/20. Beyond user queries and end results, future work needs consistent and detailed recording of parameter extraction, individual function call results, intermediate agent responses, and time tracking. Logging was inconsistent, sometimes capturing all tool calls, and sometimes missing important interactions. 

*Model behavior surprises*: Some models arrived at the right answer without calling expected and crucial workflows (i.e. Claude 4.1 Opus gave an accurate pKa prediction without calling the one and only pKa tool). Indicative of model shortcuts/room for improvement in prompts. 

And beyond all of these, there's an entire layer within parameters I haven't touched - does the agent choose scientifically sound engines or methods?

## Future plans

**Better scoring methods**. I still need to noodle on this a bit more, even madness needs its method. Otherwise, it's just lousy for reproducibility. 

**Data collection**. Systematic logging of all intermediate steps, parameter choices, error recovery attempts, reasoning chains. A plus: time tracking and computational resource usage across the different models.  

**Eval-as-you-go**. Rather than batch eval after data collection, can a real-time assessment be used? Can it catch edge cases and model behaviors as they emerge? And can new problems be generated dynamically as a response? 

**Gamification and community engagement**. An LMArena-style platform for biology/chemistry AI would be fun, where the community can submit challenging questions in real-time and see head-to-head comparisons. Getting public input on question difficulty and having researchers give genuinely hard problems at the system could create a dynamic benchmark that evolves with the field's needs.

## References
[1] Runcie, N. T., Deane, C. M., & Imrie, F. "Assessing the Chemical Intelligence of Large Language Models." *arXiv preprint arXiv:2505.07735*, 2025. https://arxiv.org/abs/2505.07735

[2] Mirza, A., Alampara, N., Kunchapu, S. et al. "A framework for evaluating the chemical knowledge and reasoning abilities of large language models against the expertise of chemists." *Nature Chemistry* 17, 1027–1034, 2025. https://www.nature.com/articles/s41557-025-01815-x

[3] Guo, T., Guo, K., Nan, B., Liang, Z., Guo, Z., Chawla, N. V., Wiest, O., & Zhang, X. "What can Large Language Models do in chemistry? A comprehensive benchmark on eight tasks." *arXiv preprint arXiv:2305.18365*, 2023. https://arxiv.org/abs/2305.18365