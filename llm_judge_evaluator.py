"""
llm_judge_evaluator.py - automatically grades agent performance using an llm as judge

what this does:
- reads log files created by agent_runner.py (via execution_logger.py)
- extracts: question, final answer, tools used, execution metrics
- sends to a judge llm (default: claude sonnet 4 via openrouter) with a detailed rubric
- scores on 3 dimensions (0-2 each, total 0-6): completion, correctness, tool use
- pass = 4+ points, fail = 3 or fewer
- saves evaluations to: evaluations/{question_id}/json/{model_name}_evaluation.json
- generates markdown reports: evaluations/{question_id}/md/{model_name}_evaluation.md

use this when: after running agent_runner.py, run this to grade how well the agent answered
example: python llm_judge_evaluator.py tier1_007
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
    """Results from LLM judge evaluation"""
    question_id: str
    completion_score: int  # 0-2 scale
    correctness_score: int  # 0-2 scale
    tool_use_score: int  # 0-2 scale
    total_score: int  # 0-6 scale
    overall_assessment: str  # "pass" or "fail"
    reasoning: str
    specific_feedback: List[str]
    chemistry_validation: Dict[str, Any]
    web_citations: List[Dict[str, str]] = None  # Optional web search citations


class ComputationalChemistryJudge:
    """LLM-based evaluator for computational chemistry agent performance"""

    def __init__(self, openrouter_api_key: str, judge_model: str = "anthropic/claude-sonnet-4", output_dir: str = "evaluations", enable_web_search: bool = True):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key
        )
        self.judge_model = judge_model
        self.output_dir = output_dir
        self.enable_web_search = enable_web_search

    def extract_log_summary(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key information from agent log for evaluation"""

        # Extract tool usage patterns
        tools_called = []
        tool_execution_times = []
        successful_tools = 0
        failed_tools = 0

        for event in log_data.get("execution_timeline", []):
            if event.get("event_type") == "tool_call":
                tools_called.append(event.get("tool_name", ""))
                if event.get("execution_time_ms"):
                    tool_execution_times.append(event["execution_time_ms"])
                if event.get("success", True):
                    successful_tools += 1
                else:
                    failed_tools += 1

        # Extract reasoning quality - count thinking steps
        thinking_steps = [
            event for event in log_data.get("execution_timeline", [])
            if event.get("event_type") == "thinking"
        ]

        return {
            "question_id": log_data.get("question_id"),
            "user_question": log_data.get("user_question"),
            "final_answer": log_data.get("final_answer", ""),
            "completed_successfully": log_data.get("completed_successfully", False),
            "total_time_minutes": log_data.get("total_time_ms", 0) / (1000 * 60),
            "tools_called": tools_called,
            "unique_tools": list(set(tools_called)),
            "total_tool_calls": len(tools_called),
            "successful_tools": successful_tools,
            "failed_tools": failed_tools,
            "tool_success_rate": successful_tools / max(len(tools_called), 1),
            "thinking_steps": len(thinking_steps),
            "total_cost": log_data.get("total_cost_usd", 0),
            "total_tokens": log_data.get("total_tokens", 0)
        }

    def create_evaluation_prompt(self, log_summary: Dict[str, Any]) -> str:
        """Create evaluation prompt following Anthropic's principles"""

        tools_list = ", ".join(log_summary["unique_tools"])

        return f"""You are an expert evaluator for AI agents performing computational chemistry tasks.

TASK: {log_summary['user_question']}

AGENT EXECUTION SUMMARY:
- Completion Status: {"✅ Completed" if log_summary['completed_successfully'] else "❌ Failed"}
- Tools Used: {tools_list}
- Total Tool Calls: {log_summary['total_tool_calls']}
- Tool Success Rate: {log_summary['tool_success_rate']:.2f}
- Execution Time: {log_summary['total_time_minutes']:.1f} minutes
- Thinking Steps: {log_summary['thinking_steps']}

FINAL ANSWER:
{log_summary['final_answer']}

EVALUATION RUBRIC:
Evaluate the agent across 3 dimensions using a 0-2 scale. Focus ONLY on actual execution and results, not plans or intentions.

1. COMPLETION (0-2):
   - 2: Fully completed the requested task with a final answer
   - 1: Made meaningful progress but did not finish
   - 0: Did not complete the task or minimal progress

2. CORRECTNESS (0-2):
   **You have web search access - USE IT to validate answers against literature!**

   - 2: Computed results are within reasonable range of published scientific literature values (±0.3 units for pKa, ±0.2 for logP, ±10% for other properties)
   - 1: Results are somewhat close to literature but with notable deviations (0.3-1.0 units off)
   - 0: Results significantly deviate from literature (>1.0 units off), are impossible, or no computational results provided

3. TOOL USE (0-2):
   - 2: Used tools correctly with appropriate parameters and efficient workflow
   - 1: Good tool use with minor parameter or efficiency issues
   - 0: Poor tool selection, incorrect parameters, or failed tool execution

SCIENTIFIC VALIDATION REQUIREMENT:
For correctness scoring, you MUST use web search to:
1. **Search for literature values** (e.g., "acetic acid pKa experimental value")
2. **Search PubChem** for the molecule (e.g., "PubChem acetic acid")
3. **Find computational benchmarks** if available (e.g., "DFT pKa calculation benchmark")
4. **Compare agent's result to literature** and cite specific sources
5. If no literature values exist, assess chemical plausibility using fundamental principles
6. **IMPORTANT**: If agent used web search to find literature values instead of computing them, automatically score 0/2 for correctness

You will have access to web search - use it to provide real citations with URLs.

SCORING: Pass = 4+ total points, Fail = 3 or fewer points

INSTRUCTIONS:
Think through your evaluation step by step, then provide your assessment in this exact format:

<thinking>
[Your detailed reasoning for each dimension, including:
- For CORRECTNESS: Specific literature values researched with publication references
- Comparison between computed results and literature benchmarks
- Assessment of whether results fall within reasonable ranges]
</thinking>

<evaluation>
Completion: [0/1/2]
Correctness: [0/1/2]
Tool Use: [0/1/2]
Total Score: [0-6]
Overall Assessment: [pass/fail]
</evaluation>

<literature_validation>
[Required for correctness scoring: Cite specific publications and values used for comparison]
</literature_validation>

<feedback>
- [Brief specific feedback on execution and results]
</feedback>"""

    async def evaluate_log(self, log_file_path: str) -> ChemistryEvaluation:
        """Evaluate a single log file"""

        # Load and parse log
        with open(log_file_path, 'r') as f:
            log_data = json.load(f)

        log_summary = self.extract_log_summary(log_data)
        prompt = self.create_evaluation_prompt(log_summary)

        try:
            # Build model name with web search if enabled
            model_name = self.judge_model
            if self.enable_web_search and ":online" not in model_name:
                model_name = f"{self.judge_model}:online"

            # Get evaluation from judge
            completion = self.client.chat.completions.create(
                model=model_name,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.1  # Low temperature for consistent evaluation
            )

            judge_response = completion.choices[0].message.content

            # Extract web search citations if available
            citations = []
            if hasattr(completion.choices[0].message, 'annotations') and completion.choices[0].message.annotations:
                for annotation in completion.choices[0].message.annotations:
                    # OpenAI API returns Annotation objects with attributes, not dicts
                    if hasattr(annotation, 'type') and annotation.type == 'url_citation':
                        url_citation = annotation.url_citation
                        citations.append({
                            'url': url_citation.url if hasattr(url_citation, 'url') else None,
                            'title': url_citation.title if hasattr(url_citation, 'title') else None,
                            'content': url_citation.content if hasattr(url_citation, 'content') else None
                        })

            # Parse the structured response
            evaluation = self.parse_judge_response(judge_response, log_summary, citations)
            return evaluation

        except Exception as e:
            print(f"Error during evaluation: {e}")
            return ChemistryEvaluation(
                question_id=log_summary["question_id"],
                completion_score=0,
                correctness_score=0,
                tool_use_score=0,
                total_score=0,
                overall_assessment="fail",
                reasoning=f"Evaluation failed due to error: {e}",
                specific_feedback=["Evaluation failed"],
                chemistry_validation={"error": str(e)}
            )

    def _enrich_citations_with_content(self, citations: List[Dict[str, str]], reasoning: str, lit_validation: str) -> List[Dict[str, str]]:
        """Extract relevant quotes from judge's reasoning and match them to citations"""
        import re

        # Combine all judge text for searching
        full_text = f"{reasoning}\n\n{lit_validation}"

        # Find all quoted text (text in quotes)
        quoted_pattern = r'["""\'](.*?)["""\']'
        quotes = re.findall(quoted_pattern, full_text)

        # Find numbered references like "1.", "2.", etc. with following text
        numbered_refs = re.findall(r'(\d+)\.\s*([^0-9\n]{10,200})', full_text)

        # For each citation, try to find relevant content
        enriched_citations = []
        for i, citation in enumerate(citations, 1):
            content_snippets = []

            # Look for quotes that might be from this source
            for quote in quotes:
                # If quote is substantial (>20 chars) and mentions chemical terms
                if len(quote) > 20 and any(word in quote.lower() for word in ['solubility', 'mg/ml', 'pka', 'logp', 'experimental', 'literature']):
                    content_snippets.append(quote)

            # Look for numbered references matching this citation index
            for ref_num, ref_text in numbered_refs:
                if int(ref_num) == i:
                    content_snippets.append(ref_text.strip())

            # Create enriched citation
            enriched = citation.copy()
            if content_snippets:
                # Join unique snippets, limit to first 3 most relevant
                unique_snippets = list(dict.fromkeys(content_snippets))[:3]
                enriched['content'] = " | ".join(unique_snippets)

            enriched_citations.append(enriched)

        return enriched_citations

    def parse_judge_response(self, response: str, log_summary: Dict[str, Any], citations: List[Dict[str, str]] = None) -> ChemistryEvaluation:
        """Parse judge response into structured evaluation"""

        import re

        # Extract thinking section
        thinking_match = re.search(r'<thinking>(.*?)</thinking>', response, re.DOTALL)
        reasoning = thinking_match.group(1).strip() if thinking_match else "No reasoning provided"

        # Extract literature validation section
        lit_validation_match = re.search(r'<literature_validation>(.*?)</literature_validation>', response, re.DOTALL)
        lit_validation = lit_validation_match.group(1).strip() if lit_validation_match else ""

        # Enrich citations with content from judge's reasoning
        if citations:
            citations = self._enrich_citations_with_content(citations, reasoning, lit_validation)

        # Extract evaluation scores
        eval_match = re.search(r'<evaluation>(.*?)</evaluation>', response, re.DOTALL)
        eval_text = eval_match.group(1) if eval_match else ""

        # Extract scores (0-2 scale)
        completion_match = re.search(r'completion:\s*(\d)', eval_text.lower())
        correctness_match = re.search(r'correctness:\s*(\d)', eval_text.lower())
        tool_use_match = re.search(r'tool use:\s*(\d)', eval_text.lower())
        total_match = re.search(r'total score:\s*(\d)', eval_text.lower())

        completion_score = int(completion_match.group(1)) if completion_match else 0
        correctness_score = int(correctness_match.group(1)) if correctness_match else 0
        tool_use_score = int(tool_use_match.group(1)) if tool_use_match else 0
        total_score = int(total_match.group(1)) if total_match else (completion_score + correctness_score + tool_use_score)

        overall_assessment = "pass" if "overall assessment: pass" in eval_text.lower() else "fail"

        # Extract feedback
        feedback_match = re.search(r'<feedback>(.*?)</feedback>', response, re.DOTALL)
        feedback_text = feedback_match.group(1) if feedback_match else ""

        # Simple feedback parsing
        specific_feedback = []
        if feedback_text:
            for line in feedback_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•')):
                    specific_feedback.append(line[1:].strip())

        # Add literature validation to feedback if present
        if lit_validation:
            specific_feedback.append(f"Literature validation: {lit_validation}")

        return ChemistryEvaluation(
            question_id=log_summary["question_id"],
            completion_score=completion_score,
            correctness_score=correctness_score,
            tool_use_score=tool_use_score,
            total_score=total_score,
            overall_assessment=overall_assessment,
            reasoning=reasoning,
            specific_feedback=specific_feedback,
            chemistry_validation={
                "tools_used": log_summary["unique_tools"],
                "success_rate": log_summary["tool_success_rate"],
                "execution_time": log_summary["total_time_minutes"]
            },
            web_citations=citations if citations else []
        )

    def save_evaluation(self, evaluation: ChemistryEvaluation, output_path: str):
        """Save evaluation results to JSON file"""

        evaluation_data = {
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
            "web_citations": evaluation.web_citations if evaluation.web_citations else [],
            "evaluator_type": "llm_judge"
        }

        with open(output_path, 'w') as f:
            json.dump(evaluation_data, f, indent=2)

    def generate_report(self, evaluation: ChemistryEvaluation) -> str:
        """Generate markdown evaluation report"""

        # Format web citations if available
        citations_section = ""
        if evaluation.web_citations and len(evaluation.web_citations) > 0:
            citations_section = "\n### Web Search Citations:\n"
            for i, citation in enumerate(evaluation.web_citations, 1):
                citations_section += f"{i}. [{citation.get('title', 'Source')}]({citation.get('url', '#')})\n"

        return f"""# LLM Judge Evaluation Report: {evaluation.question_id}

## Overall Assessment: {evaluation.overall_assessment.upper()}

### Evaluation Scores:
- **Completion**: {evaluation.completion_score}/2
- **Correctness**: {evaluation.correctness_score}/2
- **Tool Use**: {evaluation.tool_use_score}/2
- **Total Score**: {evaluation.total_score}/6

### Judge Reasoning:
{evaluation.reasoning}

### Specific Feedback:
{chr(10).join(f"- {feedback}" for feedback in evaluation.specific_feedback) if evaluation.specific_feedback else "- No specific feedback provided"}
{citations_section}
### Execution Metrics:
- **Tools Used**: {', '.join(evaluation.chemistry_validation.get('tools_used', []))}
- **Tool Success Rate**: {evaluation.chemistry_validation.get('success_rate', 0):.2f}
- **Execution Time**: {evaluation.chemistry_validation.get('execution_time', 0):.1f} minutes

---
*Evaluated using LLM Judge with Web Search*
"""


# Example usage
async def evaluate_single_log(log_file_path: str, output_dir: str = "evaluations", judge_model: str = "anthropic/claude-sonnet-4", enable_web_search: bool = True):
    """Evaluate a single log file and save results"""

    evaluator = ComputationalChemistryJudge(
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        judge_model=judge_model,
        output_dir=output_dir,
        enable_web_search=enable_web_search
    )

    # Extract question_id from filename or log
    with open(log_file_path, 'r') as f:
        log_data = json.load(f)
    question_id = log_data.get("question_id", "unknown")

    # Evaluate
    evaluation = await evaluator.evaluate_log(log_file_path)

    # Create json/md subfolder structure using output_dir
    question_dir = os.path.join(output_dir, question_id)
    json_dir = os.path.join(question_dir, "json")
    md_dir = os.path.join(question_dir, "md")
    archive_dir = os.path.join(question_dir, "archives")

    # Create directories
    os.makedirs(json_dir, exist_ok=True)
    os.makedirs(md_dir, exist_ok=True)

    # Extract model name from log and clean for filename
    with open(log_file_path, 'r') as f:
        log_data = json.load(f)
    model_name_raw = log_data.get("model_name", "unknown")
    model_name = model_name_raw.replace("/", "_").replace(":", "_")  # Clean for filename

    # Define file paths
    json_output = os.path.join(json_dir, f"{model_name}_evaluation.json")
    md_output = os.path.join(md_dir, f"{model_name}_evaluation.md")

    # Archive existing files if they exist
    if os.path.exists(json_output) or os.path.exists(md_output):
        os.makedirs(archive_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if os.path.exists(json_output):
            archive_json = os.path.join(archive_dir, f"{model_name}_evaluation_{timestamp}.json")
            os.rename(json_output, archive_json)
            print(f"📁 Archived old JSON: {archive_json}")

        if os.path.exists(md_output):
            archive_md = os.path.join(archive_dir, f"{model_name}_evaluation_{timestamp}.md")
            os.rename(md_output, archive_md)
            print(f"📁 Archived old MD: {archive_md}")

    evaluator.save_evaluation(evaluation, json_output)

    # Save markdown report
    report = evaluator.generate_report(evaluation)
    with open(md_output, 'w') as f:
        f.write(report)

    print(f"✅ LLM Judge evaluation completed:")
    print(f"  - JSON: {json_output}")
    print(f"  - Report: {md_output}")
    print(f"  - Overall: {evaluation.overall_assessment}")
    print(f"  - Completion: {evaluation.completion_score}/2")
    print(f"  - Correctness: {evaluation.correctness_score}/2")
    print(f"  - Tool Use: {evaluation.tool_use_score}/2")

    return evaluation


async def evaluate_question_batch(question_id: str, logs_dir: str = "logs"):
    """Evaluate all model logs for a specific question"""

    import glob

    # Find all log files for this question (in model subdirectories)
    question_logs_pattern = os.path.join(logs_dir, question_id, "*", "*.json")
    log_files = glob.glob(question_logs_pattern)

    if not log_files:
        print(f"❌ No log files found for {question_id} in {question_logs_pattern}")
        return

    print(f"🚀 Evaluating {len(log_files)} model logs for {question_id}")

    evaluations = []
    for log_file in log_files:
        print(f"📊 Evaluating: {os.path.basename(log_file)}")
        evaluation = await evaluate_single_log(log_file)
        evaluations.append(evaluation)

    # Summary report
    print(f"\n✅ Completed evaluation for {question_id}")
    print(f"📁 Results saved to: evaluations/{question_id}/")
    print("\n📈 Summary:")

    passes = sum(1 for eval in evaluations if eval.overall_assessment == "pass")
    print(f"  - Models passing: {passes}/{len(evaluations)}")

    avg_completion = sum(eval.completion_score for eval in evaluations) / len(evaluations)
    avg_correctness = sum(eval.correctness_score for eval in evaluations) / len(evaluations)
    avg_tool_use = sum(eval.tool_use_score for eval in evaluations) / len(evaluations)
    avg_total = sum(eval.total_score for eval in evaluations) / len(evaluations)

    print(f"  - Average Completion: {avg_completion:.1f}/2")
    print(f"  - Average Correctness: {avg_correctness:.1f}/2")
    print(f"  - Average Tool Use: {avg_tool_use:.1f}/2")
    print(f"  - Average Total Score: {avg_total:.1f}/6")

    return evaluations


if __name__ == "__main__":
    import argparse

    load_dotenv()

    parser = argparse.ArgumentParser(description="Evaluate computational chemistry logs")
    parser.add_argument("question_id", nargs="?", default="tier3_004",
                       help="Question ID to evaluate (e.g., tier1_001, tier3_004)")
    parser.add_argument("--single", "-s",
                       help="Evaluate single log file instead of batch")
    parser.add_argument("--logs-dir", default="logs",
                       help="Directory containing logs (default: logs)")
    parser.add_argument("--judge", default="anthropic/claude-sonnet-4",
                       help="Judge model to use (default: anthropic/claude-sonnet-4)")
    parser.add_argument("--output-dir", default="evaluations",
                       help="Output directory for evaluations (default: evaluations)")
    parser.add_argument("--no-web-search", action="store_true",
                       help="Disable web search for judge (default: enabled)")

    args = parser.parse_args()

    if args.single:
        # Evaluate single file
        if os.path.exists(args.single):
            asyncio.run(evaluate_single_log(
                args.single,
                output_dir=args.output_dir,
                judge_model=args.judge,
                enable_web_search=not args.no_web_search
            ))
        else:
            print(f"Log file not found: {args.single}")
    else:
        # Batch evaluate all models for a question
        asyncio.run(evaluate_question_batch(args.question_id, args.logs_dir))