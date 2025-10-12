"""
LLM Judge Evaluator - Grades agent chemistry task performance

Evaluates agent logs with LLM judge using web search for literature validation.
Scores: Completion (0-2), Correctness (0-2), Tool Use (0-2). Pass = 4+/6.
"""

import json
import asyncio
import os
from openai import OpenAI
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv


@dataclass
class ChemistryEvaluation:
    """Evaluation results"""
    question_id: str
    completion_score: int
    correctness_score: int
    tool_use_score: int
    total_score: int
    overall_assessment: str
    reasoning: str
    specific_feedback: List[str]
    chemistry_validation: Dict[str, Any]
    web_citations: List[Dict[str, str]] = None


class ComputationalChemistryJudge:
    """LLM-based evaluator"""

    def __init__(self, openrouter_api_key: str, judge_model: str = "openai/gpt-5",
                 output_dir: str = "evaluations", enable_web_search: bool = True):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key
        )
        self.judge_model = judge_model
        self.output_dir = output_dir
        self.enable_web_search = enable_web_search

    def create_evaluation_prompt(self, log_data: Dict[str, Any]) -> str:
        """Create evaluation prompt with FULL execution trace"""

        # Format complete execution timeline
        execution_trace = []
        for event in log_data.get("execution_timeline", []):
            event_type = event.get("event_type", "unknown")

            if event_type == "tool_call":
                tool_name = event.get("tool_name", "unknown")
                parameters = event.get("parameters", {})
                result = event.get("result", "")
                success = event.get("success", False)
                exec_time = event.get("execution_time_ms", 0)

                # Truncate very long results to avoid token explosion
                result_str = str(result)
                if len(result_str) > 500:
                    result_str = result_str[:500] + "... [truncated]"

                execution_trace.append(
                    f"  🔧 {tool_name}\n"
                    f"     Parameters: {parameters}\n"
                    f"     Result: {result_str}\n"
                    f"     Status: {'✓ Success' if success else '✗ Failed'} ({exec_time}ms)"
                )

            elif event_type == "thinking":
                content = event.get("content", "")
                if len(content) > 200:
                    content = content[:200] + "..."
                execution_trace.append(f"  💭 Thinking: {content}")

        execution_trace_str = "\n".join(execution_trace) if execution_trace else "  (No execution trace)"

        return f"""You are an expert evaluator for AI agents performing computational chemistry tasks.

TASK: {log_data.get('user_question')}

COMPLETE EXECUTION TRACE:
{execution_trace_str}

FINAL ANSWER:
{log_data.get('final_answer', '')}

EXECUTION SUMMARY:
- Completion Status: {"✅ Completed" if log_data.get('completed_successfully') else "❌ Failed"}
- Total Time: {log_data.get('total_time_ms', 0) / 60000:.1f} minutes
- Total Cost: ${log_data.get('total_cost_usd', 0):.4f}

EVALUATION RUBRIC:
Evaluate on 3 dimensions (0-2 scale each). Your scores must be AUDITABLE.

═══════════════════════════════════════════════════════════════════════════════
1. COMPLETION (0-2) - Did the computational workflow finish?
═══════════════════════════════════════════════════════════════════════════════

Score 2/2 IF ALL OF:
  ✓ Computational workflow reached completion status
  ✓ Final numerical result was retrieved and presented
  ✓ Agent provided interpretation of results

Score 1/2 IF:
  ⚠ Workflow started but didn't complete (timeout, error)

Score 0/2 IF:
  ✗ No computational workflow executed

⚠️  Don't trust agent claims - check execution trace.

═══════════════════════════════════════════════════════════════════════════════
2. CORRECTNESS (0-2) - Is the computed result accurate?
═══════════════════════════════════════════════════════════════════════════════

**YOU HAVE WEB SEARCH - USE IT TO VALIDATE ANSWERS**

STEP 1: Search for literature values
  → Search: "[molecule name] [property] experimental value"
  → Search: "PubChem [molecule name]"

STEP 2: Extract values and compare
  → Agent's value: X
  → Literature value: Y (from [source URL])
  → Absolute error: |X - Y|
  → Percent error: |X - Y| / Y × 100%

STEP 3: Score based on error magnitude

Score 2/2 IF:
  ✓ pKa: within ±0.5 units (±10% typical error)
  ✓ logP: within ±0.3 units (±20% typical error)
  ✓ Solubility: within ±50% (ML models vary)
  ✓ Bond lengths: within ±0.05 Å (±3% typical error)

Score 1/2 IF:
  ⚠ pKa: 0.5-1.5 units off (10-30% error)
  ⚠ logP: 0.3-0.8 units off (20-50% error)
  ⚠ Solubility: 50-150% error

Score 0/2 IF:
  ✗ pKa: >1.5 units off (>30% error)
  ✗ Solubility: >150% error (factor of 2.5+)
  ✗ Wrong by order of magnitude
  ✗ No numerical result provided
  ✗ CHEATING: Agent used web search to FIND answer instead of computing

REQUIRED OUTPUT:
  Include in <literature_validation>:
  1. Agent's computed value
  2. Literature value with source URL
  3. Absolute error
  4. Percent error
  5. Score justification

═══════════════════════════════════════════════════════════════════════════════
3. TOOL USE (0-2) - Were tools used correctly?
═══════════════════════════════════════════════════════════════════════════════

Score 2/2 IF ALL OF:
  ✓ Appropriate tools selected
  ✓ Correct parameters (valid SMILES, sensible workflow inputs)
  ✓ Logical sequence (lookup → validate → submit → check → retrieve)
  ✓ All tools executed successfully

Score 1/2 IF:
  ⚠ Correct tools but minor issues (inefficient, suboptimal parameters)

Score 0/2 IF:
  ✗ Wrong tool selection
  ✗ Invalid parameters
  ✗ Multiple critical failures

SCORING: Pass = 4+ total points, Fail = 3 or fewer

INSTRUCTIONS:
Provide your assessment in this exact format:

<thinking>
[Your reasoning for each dimension]
</thinking>

<evaluation>
Completion: [0/1/2]
Correctness: [0/1/2]
Tool Use: [0/1/2]
Total Score: [0-6]
Overall Assessment: [pass/fail]
</evaluation>

<literature_validation>
[Required: Cite specific publications and values]
</literature_validation>

<feedback>
- [Brief specific feedback]
</feedback>"""

    async def evaluate_log(self, log_file_path: str) -> ChemistryEvaluation:
        """Evaluate a single log file"""

        # Load log
        with open(log_file_path, 'r') as f:
            log_data = json.load(f)

        prompt = self.create_evaluation_prompt(log_data)

        # Call judge with web search
        model_name = self.judge_model
        if self.enable_web_search and ":online" not in model_name:
            model_name = f"{self.judge_model}:online"

        completion = self.client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )

        judge_response = completion.choices[0].message.content

        # Extract citations
        citations = []
        if hasattr(completion.choices[0].message, 'annotations') and completion.choices[0].message.annotations:
            for annotation in completion.choices[0].message.annotations:
                if hasattr(annotation, 'type') and annotation.type == 'url_citation':
                    url_citation = annotation.url_citation
                    citations.append({
                        'url': url_citation.url if hasattr(url_citation, 'url') else None,
                        'title': url_citation.title if hasattr(url_citation, 'title') else None,
                    })

        # Enrich citations with content from judge's reasoning
        citations = self._enrich_citations(citations, judge_response)

        # Parse response
        return self._parse_response(judge_response, log_data, citations)

    def _enrich_citations(self, citations: List[Dict], response: str) -> List[Dict]:
        """Extract quotes from judge's reasoning and add to citations as content"""
        import re

        # Find all quoted text in the response
        quotes = re.findall(r'["""\'](.*?)["""\']', response)

        # Filter for substantial quotes (>20 chars) that look like chemistry data
        chem_quotes = [q for q in quotes if len(q) > 20 and any(
            keyword in q.lower() for keyword in
            ['solubility', 'mg/ml', 'pka', 'logp', 'experimental', 'literature',
             'calculated', 'value', 'mol/l', 'kcal', 'angstrom']
        )]

        # Add content to citations
        enriched = []
        for i, citation in enumerate(citations):
            enriched_citation = citation.copy()
            # Try to match quotes to this citation by index or content
            if i < len(chem_quotes):
                enriched_citation['content'] = chem_quotes[i]
            elif chem_quotes:
                # Take first available relevant quote
                enriched_citation['content'] = chem_quotes[0]

            enriched.append(enriched_citation)

        return enriched

    def _parse_response(self, response: str, log_data: Dict, citations: List) -> ChemistryEvaluation:
        """Parse judge response"""
        import re

        # Extract sections
        thinking = re.search(r'<thinking>(.*?)</thinking>', response, re.DOTALL)
        reasoning = thinking.group(1).strip() if thinking else "No reasoning"

        lit_val = re.search(r'<literature_validation>(.*?)</literature_validation>', response, re.DOTALL)
        lit_validation = lit_val.group(1).strip() if lit_val else ""

        eval_section = re.search(r'<evaluation>(.*?)</evaluation>', response, re.DOTALL)
        eval_text = eval_section.group(1) if eval_section else ""

        feedback = re.search(r'<feedback>(.*?)</feedback>', response, re.DOTALL)
        feedback_text = feedback.group(1) if feedback else ""

        # Extract scores
        completion = re.search(r'completion:\s*(\d)', eval_text.lower())
        correctness = re.search(r'correctness:\s*(\d)', eval_text.lower())
        tool_use = re.search(r'tool use:\s*(\d)', eval_text.lower())

        completion_score = int(completion.group(1)) if completion else 0
        correctness_score = int(correctness.group(1)) if correctness else 0
        tool_use_score = int(tool_use.group(1)) if tool_use else 0
        total = completion_score + correctness_score + tool_use_score

        assessment = "pass" if total >= 4 else "fail"

        # Parse feedback
        feedback_lines = []
        if feedback_text:
            for line in feedback_text.split('\n'):
                line = line.strip()
                if line and line.startswith('-'):
                    feedback_lines.append(line[1:].strip())

        if lit_validation:
            feedback_lines.append(f"Literature validation: {lit_validation}")

        # Extract tool info
        tools_called = [e.get("tool_name", "") for e in log_data.get("execution_timeline", [])
                       if e.get("event_type") == "tool_call"]
        unique_tools = list(set(tools_called))

        return ChemistryEvaluation(
            question_id=log_data.get("question_id", "unknown"),
            completion_score=completion_score,
            correctness_score=correctness_score,
            tool_use_score=tool_use_score,
            total_score=total,
            overall_assessment=assessment,
            reasoning=reasoning,
            specific_feedback=feedback_lines,
            chemistry_validation={
                "tools_used": unique_tools,
                "total_time_minutes": log_data.get('total_time_ms', 0) / 60000
            },
            web_citations=citations if citations else []
        )

    def save_evaluation(self, evaluation: ChemistryEvaluation, log_file_path: str):
        """Save evaluation to JSON and MD files"""

        # Load log to get model name
        with open(log_file_path, 'r') as f:
            log_data = json.load(f)

        model_name = log_data.get("model_name", "unknown").replace("/", "_").replace(":", "_")
        question_id = evaluation.question_id

        # Create output paths
        json_dir = os.path.join(self.output_dir, question_id, "json")
        md_dir = os.path.join(self.output_dir, question_id, "md")
        archive_dir = os.path.join(self.output_dir, question_id, "archives")

        os.makedirs(json_dir, exist_ok=True)
        os.makedirs(md_dir, exist_ok=True)

        json_path = os.path.join(json_dir, f"{model_name}_evaluation.json")
        md_path = os.path.join(md_dir, f"{model_name}_evaluation.md")

        # Archive old files if exist
        if os.path.exists(json_path) or os.path.exists(md_path):
            os.makedirs(archive_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if os.path.exists(json_path):
                archive = os.path.join(archive_dir, f"{model_name}_evaluation_{timestamp}.json")
                os.rename(json_path, archive)

            if os.path.exists(md_path):
                archive = os.path.join(archive_dir, f"{model_name}_evaluation_{timestamp}.md")
                os.rename(md_path, archive)

        # Save JSON
        eval_data = {
            "evaluation_timestamp": datetime.now().isoformat(),
            "question_id": evaluation.question_id,
            "completion_score": evaluation.completion_score,
            "correctness_score": evaluation.correctness_score,
            "tool_use_score": evaluation.tool_use_score,
            "total_score": evaluation.total_score,
            "overall_assessment": evaluation.overall_assessment,
            "reasoning": evaluation.reasoning,
            "specific_feedback": evaluation.specific_feedback,
            "chemistry_validation": evaluation.chemistry_validation,
            "web_citations": evaluation.web_citations,
            "evaluator_type": "llm_judge"
        }

        with open(json_path, 'w') as f:
            json.dump(eval_data, f, indent=2)

        # Save markdown
        citations_md = ""
        if evaluation.web_citations:
            citations_md = "\n### Web Search Citations:\n"
            for i, cite in enumerate(evaluation.web_citations, 1):
                title = cite.get('title', 'Source')
                url = cite.get('url', '#')
                content = cite.get('content', '')
                if content:
                    citations_md += f"{i}. [{title}]({url})\n   > {content}\n"
                else:
                    citations_md += f"{i}. [{title}]({url})\n"

        md_content = f"""# LLM Judge Evaluation: {evaluation.question_id}

## Overall: {evaluation.overall_assessment.upper()}

### Scores:
- **Completion**: {evaluation.completion_score}/2
- **Correctness**: {evaluation.correctness_score}/2
- **Tool Use**: {evaluation.tool_use_score}/2
- **Total**: {evaluation.total_score}/6

### Reasoning:
{evaluation.reasoning}

### Feedback:
{chr(10).join(f"- {fb}" for fb in evaluation.specific_feedback) if evaluation.specific_feedback else "- No feedback"}
{citations_md}
### Execution:
- **Tools**: {', '.join(evaluation.chemistry_validation.get('tools_used', []))}
- **Time**: {evaluation.chemistry_validation.get('total_time_minutes', 0):.1f} min

---
*Evaluated with {self.judge_model}*
"""

        with open(md_path, 'w') as f:
            f.write(md_content)

        return json_path, md_path


async def evaluate_single_log(log_file_path: str, output_dir: str = "evaluations",
                              judge_model: str = "openai/gpt-5", enable_web_search: bool = True):
    """Evaluate a single log file - main entry point for batch scripts"""

    evaluator = ComputationalChemistryJudge(
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        judge_model=judge_model,
        output_dir=output_dir,
        enable_web_search=enable_web_search
    )

    evaluation = await evaluator.evaluate_log(log_file_path)
    json_path, md_path = evaluator.save_evaluation(evaluation, log_file_path)

    print(f"✅ Evaluated: {evaluation.overall_assessment} ({evaluation.total_score}/6)")
    print(f"   JSON: {json_path}")
    print(f"   MD: {md_path}")

    return evaluation


if __name__ == "__main__":
    import argparse

    load_dotenv()

    parser = argparse.ArgumentParser(description="Evaluate chemistry agent logs")
    parser.add_argument("--single", "-s", required=True, help="Log file to evaluate")
    parser.add_argument("--judge", default="openai/gpt-5", help="Judge model")
    parser.add_argument("--output-dir", default="evaluations", help="Output directory")
    parser.add_argument("--no-web-search", action="store_true", help="Disable web search")

    args = parser.parse_args()

    if os.path.exists(args.single):
        asyncio.run(evaluate_single_log(
            args.single,
            output_dir=args.output_dir,
            judge_model=args.judge,
            enable_web_search=not args.no_web_search
        ))
    else:
        print(f"❌ File not found: {args.single}")
