# Rowan MCP Computational Chemistry Task Evaluation Rubric

## Overview

This rubric evaluates AI agent performance on computational chemistry tasks using the Rowan MCP platform. The evaluation uses a 5-point scale (1-5) across multiple dimensions critical for scientific computational work.

## Evaluation Instructions for Judge

**IMPORTANT: Think through your reasoning first before assigning scores.**

For each evaluation:

1. **Read the task requirements carefully** - What specific calculations were requested?
2. **Analyze the execution timeline** - Review all steps taken by the agent
3. **Examine workflow completion** - Did all submitted workflows finish successfully?
4. **Assess scientific validity** - Are the methods and results scientifically sound?
5. **Consider efficiency** - Was the approach optimal for the given task?

Use the following format:

```
<thinking>
[Your detailed reasoning about the agent's performance across all dimensions]
</thinking>

<evaluation>
Dimension 1: X/5
Dimension 2: X/5
...
Overall Score: X/5
</evaluation>
```

---

## Evaluation Dimensions

### 1. Task Completion (25% weight)

**Measures:** Whether the agent successfully completed all requested computational chemistry tasks

**5 - Excellent**
- All requested calculations completed successfully
- All workflows reached completion status (status = 1)
- All results properly retrieved and presented
- No submitted workflows left incomplete or failed

**4 - Good**
- Most requested calculations completed (≥80%)
- Minor gaps in task completion that don't affect core objectives
- All critical workflows completed successfully
- Occasional minor workflow monitoring issues

**3 - Satisfactory**
- Core calculations completed but some secondary tasks missed
- 60-79% of requested calculations completed
- Some workflow completion issues but eventual success
- Basic requirements met with room for improvement

**2 - Needs Improvement**
- Significant gaps in task completion (40-59% completed)
- Multiple failed workflows or incomplete monitoring
- Core objectives partially met but with notable deficiencies
- Agent gave up prematurely or missed critical steps

**1 - Inadequate**
- Failed to complete core computational tasks (<40% completed)
- Workflows not properly monitored or retrieved
- Fundamental misunderstanding of task requirements
- No meaningful computational results obtained

### 2. Scientific Accuracy (25% weight)

**Measures:** Correctness of computational methods and reasonableness of results

**5 - Excellent**
- All computational methods scientifically appropriate
- Results within expected ranges for given molecules/conditions
- Proper consideration of molecular properties and constraints
- Accurate interpretation of computational outputs

**4 - Good**
- Methods generally appropriate with minor methodological issues
- Results mostly reasonable with occasional outliers explained
- Good understanding of chemical principles applied
- Minor errors in interpretation that don't affect conclusions

**3 - Satisfactory**
- Basic methods correct but not optimally chosen
- Results generally reasonable but some unexplained outliers
- Adequate application of chemical knowledge
- Some methodological gaps but core approach sound

**2 - Needs Improvement**
- Some inappropriate method selections or parameter choices
- Results questionable or outside reasonable ranges
- Limited demonstration of chemical understanding
- Significant errors in interpretation of outputs

**1 - Inadequate**
- Fundamentally inappropriate computational approaches
- Results clearly unreasonable or impossible
- Poor understanding of basic chemical principles
- Major errors that invalidate conclusions

### 3. Workflow Management (20% weight)

**Measures:** Proper use of Rowan MCP workflow system and monitoring practices

**5 - Excellent**
- Perfect implementation of smart polling (10s → 20s → 40s → 80s intervals)
- All workflows properly submitted, monitored, and retrieved
- Efficient use of status checking with appropriate wait times
- No unnecessary or excessive polling

**4 - Good**
- Good workflow monitoring with minor timing issues
- Proper workflow submission and retrieval
- Mostly efficient status checking patterns
- Occasional minor polling inefficiencies

**3 - Satisfactory**
- Basic workflow management functional
- Some issues with polling frequency or timing
- Workflows eventually completed but suboptimal monitoring
- Adequate but not optimal resource utilization

**2 - Needs Improvement**
- Significant workflow management issues
- Poor polling patterns (too frequent or too infrequent)
- Some workflows not properly monitored or retrieved
- Inefficient use of computational resources

**1 - Inadequate**
- Failed to properly use workflow system
- No evidence of proper status monitoring
- Workflows submitted but not tracked to completion
- Major misunderstanding of MCP workflow patterns

### 4. Tool Selection and Usage (15% weight)

**Measures:** Appropriate selection and usage of Rowan MCP tools and computational modes

**5 - Excellent**
- Optimal tool selection for each calculation type
- Appropriate computational modes chosen (rapid/careful/meticulous)
- Efficient molecule lookup and structure handling
- Proper use of specialized tools (conformer search, optimization, etc.)

**4 - Good**
- Generally appropriate tool choices
- Minor suboptimal selections that don't significantly impact results
- Good understanding of available computational options
- Effective use of most relevant tools

**3 - Satisfactory**
- Basic tool usage adequate for task completion
- Some suboptimal choices but functional approach
- Limited exploration of available computational options
- Core tools used correctly but missed optimization opportunities

**2 - Needs Improvement**
- Poor tool selection affecting result quality
- Inefficient computational mode choices
- Limited understanding of available options
- Frequent use of inappropriate tools for given tasks

**1 - Inadequate**
- Fundamentally wrong tool selections
- No evidence of understanding tool capabilities
- Failure to utilize appropriate computational resources
- Major inefficiencies in approach selection

### 5. Result Interpretation and Communication (15% weight)

**Measures:** Quality of result presentation and scientific interpretation

**5 - Excellent**
- Clear, comprehensive presentation of all calculated values
- Results properly contextualized with chemical significance
- Appropriate units and precision for reported values
- Excellent scientific communication of findings

**4 - Good**
- Good presentation of key results
- Most results properly interpreted and explained
- Generally appropriate formatting and units
- Clear communication with minor gaps

**3 - Satisfactory**
- Basic result presentation adequate
- Some interpretation provided but could be more thorough
- Acceptable formatting and units
- Functional communication of key findings

**2 - Needs Improvement**
- Limited result presentation or interpretation
- Poor formatting or inappropriate units
- Minimal scientific context provided
- Unclear communication of findings

**1 - Inadequate**
- Failed to properly present calculated results
- No meaningful interpretation or context
- Major formatting or unit errors
- Incomprehensible or missing final output

---

## Overall Scoring Guidelines

**Overall Score Calculation:**
- Task Completion: 25%
- Scientific Accuracy: 25%
- Workflow Management: 20%
- Tool Selection: 15%
- Result Communication: 15%

**Overall Score Interpretation:**

**5 (4.5-5.0):** Exceptional performance demonstrating mastery of computational chemistry workflows
**4 (3.5-4.4):** Strong performance with minor areas for improvement
**3 (2.5-3.4):** Adequate performance meeting basic requirements
**2 (1.5-2.4):** Below expectations with significant improvement needed
**1 (1.0-1.4):** Inadequate performance requiring fundamental changes

---

## Special Considerations

### Web Search Usage Penalties
Deduct 0.5-1.0 points from relevant dimensions if agent:
- Uses web search to find calculated values instead of computing them
- Searches computational databases for results rather than performing calculations
- Relies on literature values when computational results were requested

### Context-Specific Adjustments
Consider task complexity when scoring:
- Simple single-property calculations: Higher expectations for efficiency and accuracy
- Complex multi-step workflows: More tolerance for minor inefficiencies if overall approach is sound
- Novel or challenging molecular systems: Adjust accuracy expectations based on computational difficulty

---

## Example Evaluation Scenarios

### High-Quality Performance (Score: 4-5)
```
Task: "Calculate pKa and logP for caffeine"
Agent: Successfully submits workflows, implements smart polling, retrieves accurate results (pKa ~0.6, logP ~-0.07), provides proper chemical context.
```

### Medium-Quality Performance (Score: 2-3)
```
Task: "Optimize aspirin geometry and calculate HOMO-LUMO gap"
Agent: Completes optimization but fails to properly monitor second workflow, retrieves partial results, minimal scientific interpretation.
```

### Poor Performance (Score: 1-2)
```
Task: "Find major tautomers of warfarin and calculate pKa values"
Agent: Submits workflows but doesn't wait for completion, uses web search to find literature pKa values instead of computational results, fails to address tautomers.
```