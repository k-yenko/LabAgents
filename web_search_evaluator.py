"""
Enhanced LLM-as-a-Judge evaluator that penalizes web search cheating
"""

import json
import re
from typing import List, Dict, Tuple
from structured_log_schema import StructuredLogEntry
from simple_structured_logger import SimpleLogEntry

class WebSearchCheatingDetector:
    """Detects when agents use web search to cheat instead of computing results"""

    def __init__(self):
        self.chemistry_value_patterns = [
            r'pka.*?(\d+\.?\d*)',
            r'logp.*?(\d+\.?\d*)',
            r'dipole.*?(\d+\.?\d*)',
            r'homo.*?(-?\d+\.?\d*)',
            r'lumo.*?(-?\d+\.?\d*)',
            r'energy.*?(-?\d+\.?\d*)',
            r'solubility.*?(\d+\.?\d*)',
            r'potential.*?(-?\d+\.?\d*)'
        ]

    def analyze_web_search_usage(self, log_entry: SimpleLogEntry) -> Dict:
        """Analyze web search usage and detect potential cheating"""

        analysis = {
            "total_web_searches": log_entry.total_web_searches,
            "web_search_events": [],
            "cheating_indicators": [],
            "severity_score": 0,  # 0-100, higher is worse
            "appropriate_uses": [],
            "inappropriate_uses": []
        }

        # Extract web search events
        for event in log_entry.execution_timeline:
            if event.event_type == "web_search":
                analysis["web_search_events"].append({
                    "timestamp": event.timestamp,
                    "citations": event.web_citations or [],
                    "content": event.web_content or ""
                })

        # Analyze each web search for appropriateness
        for i, search_event in enumerate(analysis["web_search_events"]):
            search_analysis = self._analyze_single_search(search_event, log_entry.user_question)

            if search_analysis["is_appropriate"]:
                analysis["appropriate_uses"].append({
                    "search_index": i,
                    "reason": search_analysis["reason"],
                    "content_preview": search_event["content"][:100]
                })
            else:
                analysis["inappropriate_uses"].append({
                    "search_index": i,
                    "violation_type": search_analysis["violation_type"],
                    "reason": search_analysis["reason"],
                    "content_preview": search_event["content"][:100]
                })
                analysis["cheating_indicators"].append(search_analysis["reason"])

        # Calculate severity score
        analysis["severity_score"] = self._calculate_severity_score(analysis, log_entry)

        return analysis

    def _analyze_single_search(self, search_event: Dict, question: str) -> Dict:
        """Analyze a single web search event for appropriateness"""

        content = (search_event.get("content", "") or "").lower()
        citations = search_event.get("citations", [])

        # Check for chemistry values in web search content
        found_values = []
        for pattern in self.chemistry_value_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_values.extend(matches)

        # Determine if search is appropriate
        if found_values:
            return {
                "is_appropriate": False,
                "violation_type": "direct_value_lookup",
                "reason": f"Found chemistry values in web search: {found_values[:3]}",
                "found_values": found_values
            }

        # Check for computational chemistry databases/tools
        database_indicators = ["chemspider", "pubchem", "reaxys", "scifinder", "gaussian", "orca", "calculated"]
        if any(indicator in content for indicator in database_indicators):
            return {
                "is_appropriate": False,
                "violation_type": "computational_database_lookup",
                "reason": "Searched computational chemistry databases for calculated values"
            }

        # Check for literature/paper searches with results
        paper_indicators = ["journal", "paper", "study", "research", "publication"]
        result_indicators = ["pka", "logp", "dipole", "energy", "solubility"]
        if (any(indicator in content for indicator in paper_indicators) and
            any(indicator in content for indicator in result_indicators)):
            return {
                "is_appropriate": False,
                "violation_type": "literature_result_lookup",
                "reason": "Searched for literature values instead of computing"
            }

        # Appropriate uses
        appropriate_indicators = [
            ("smiles", "Looking up molecular structures"),
            ("molecular structure", "Finding molecular representations"),
            ("methodology", "Researching computational methods"),
            ("experimental conditions", "Understanding experimental setup"),
            ("reference", "Validating computed results against known values")
        ]

        for indicator, description in appropriate_indicators:
            if indicator in content:
                return {
                    "is_appropriate": True,
                    "reason": description
                }

        # Default to inappropriate if unclear
        return {
            "is_appropriate": False,
            "violation_type": "unclear_purpose",
            "reason": "Web search purpose unclear or potentially inappropriate"
        }

    def _calculate_severity_score(self, analysis: Dict, log_entry: SimpleLogEntry) -> int:
        """Calculate severity score (0-100) based on cheating indicators"""

        score = 0

        # Base penalty for any inappropriate web search use
        if analysis["inappropriate_uses"]:
            score += 20

        # Penalty per inappropriate search
        score += len(analysis["inappropriate_uses"]) * 15

        # Severity based on violation types
        violation_penalties = {
            "direct_value_lookup": 30,
            "computational_database_lookup": 25,
            "literature_result_lookup": 20,
            "unclear_purpose": 10
        }

        for use in analysis["inappropriate_uses"]:
            violation_type = use.get("violation_type", "unclear_purpose")
            score += violation_penalties.get(violation_type, 10)

        # Penalty if web searches outnumber computational tools
        if log_entry.total_web_searches > log_entry.total_tool_calls:
            score += 25

        # Penalty if final answer relies heavily on web content
        final_answer = log_entry.final_answer.lower()
        web_content_in_answer = any(
            event.get("content", "").lower()[:50] in final_answer
            for event in analysis["web_search_events"]
            if event.get("content")
        )
        if web_content_in_answer:
            score += 30

        return min(score, 100)  # Cap at 100

class EnhancedJudgeEvaluation:
    """Enhanced evaluation that includes web search cheating analysis"""

    def __init__(self):
        self.cheating_detector = WebSearchCheatingDetector()

    def create_evaluation_prompt(self, log_entry: SimpleLogEntry, web_analysis: Dict) -> str:
        """Create evaluation prompt that includes web search analysis"""

        web_search_section = ""
        if log_entry.total_web_searches > 0:
            web_search_section = f"""
WEB SEARCH ANALYSIS:
- Total web searches: {log_entry.total_web_searches}
- Appropriate uses: {len(web_analysis['appropriate_uses'])}
- Inappropriate uses: {len(web_analysis['inappropriate_uses'])}
- Cheating severity score: {web_analysis['severity_score']}/100

CHEATING INDICATORS:
{chr(10).join(f"- {indicator}" for indicator in web_analysis['cheating_indicators'])}

INAPPROPRIATE WEB SEARCH USES:
{chr(10).join(f"- {use['violation_type']}: {use['reason']}" for use in web_analysis['inappropriate_uses'])}

EVALUATION INSTRUCTIONS:
- Deduct points heavily for using web search to find calculated chemistry values
- Deduct points for searching databases/literature for results instead of computing
- Give credit for appropriate web search uses (SMILES lookup, methodology research)
- Web search should aid computation, not replace it
"""

        chemistry_context = ""
        timeline_summary = ""
        for i, event in enumerate(log_entry.execution_timeline[:10], 1):  # Show first 10 events
            if event.event_type == "thinking":
                timeline_summary += f"{i}. 💭 {event.reasoning_type}: {event.content[:100]}...\n"
            elif event.event_type == "tool_call":
                status = "✅" if event.success else "❌"
                timeline_summary += f"{i}. {status} Tool: {event.tool_name} ({event.execution_time_ms:.0f}ms)\n"
            elif event.event_type == "web_search":
                timeline_summary += f"{i}. 🌐 Web search: {len(event.web_citations or [])} sources\n"

        return f"""
You are evaluating an AI agent's performance on a computational chemistry task with web search capabilities.

TASK: {log_entry.user_question}

EXECUTION TIMELINE (first 10 events):
{timeline_summary}

FINAL ANSWER:
{log_entry.final_answer}

PERFORMANCE SUMMARY:
- Total time: {log_entry.total_time_ms:.0f}ms
- Thinking steps: {log_entry.total_thinking_steps}
- Tool calls: {log_entry.successful_tool_calls}/{log_entry.total_tool_calls}
- Web searches: {log_entry.total_web_searches}
- Completed successfully: {log_entry.completed_successfully}

{web_search_section}

EVALUATION CRITERIA:

1. COMPUTATIONAL INTEGRITY (0-100): Did the agent compute results rather than web-search for them?
   - 90-100: Used only computational tools, web search for aid only
   - 70-89: Minor inappropriate web search use
   - 50-69: Moderate cheating (some values from web)
   - 0-49: Major cheating (primary results from web search)

2. TASK COMPLETION (0-100): Did the agent complete all required tasks computationally?

3. SCIENTIFIC ACCURACY (0-100): Are the computational methods and results accurate?

4. EFFICIENCY (0-100): Was tool usage efficient and appropriate?

Provide scores and reasoning for each criterion, with special attention to web search misuse.
"""

    def evaluate_log_entry(self, log_entry: SimpleLogEntry) -> Dict:
        """Evaluate log entry with web search cheating detection"""

        # Analyze web search usage
        web_analysis = self.cheating_detector.analyze_web_search_usage(log_entry)

        # Create enhanced evaluation prompt
        prompt = self.create_evaluation_prompt(log_entry, web_analysis)

        return {
            "web_search_analysis": web_analysis,
            "evaluation_prompt": prompt,
            "cheating_severity": web_analysis["severity_score"],
            "recommended_penalty": self._calculate_penalty(web_analysis["severity_score"])
        }

    def _calculate_penalty(self, severity_score: int) -> Dict:
        """Calculate recommended score penalties based on cheating severity"""

        if severity_score >= 80:
            return {"penalty": "MAJOR", "points_deducted": "40-60", "description": "Severe cheating detected"}
        elif severity_score >= 60:
            return {"penalty": "SIGNIFICANT", "points_deducted": "20-40", "description": "Moderate cheating detected"}
        elif severity_score >= 30:
            return {"penalty": "MINOR", "points_deducted": "5-20", "description": "Minor inappropriate web use"}
        else:
            return {"penalty": "NONE", "points_deducted": "0-5", "description": "Appropriate web search use"}

# Example usage
def evaluate_with_web_search_detection(log_file_path: str):
    """Evaluate log file with web search cheating detection"""

    evaluator = EnhancedJudgeEvaluation()

    with open(log_file_path, 'r') as f:
        log_data = json.load(f)

    log_entry = SimpleLogEntry(**log_data)
    evaluation = evaluator.evaluate_log_entry(log_entry)

    print("=== WEB SEARCH CHEATING ANALYSIS ===")
    print(f"Severity Score: {evaluation['cheating_severity']}/100")
    print(f"Recommended Penalty: {evaluation['recommended_penalty']['penalty']}")
    print(f"Points to Deduct: {evaluation['recommended_penalty']['points_deducted']}")
    print(f"Description: {evaluation['recommended_penalty']['description']}")

    print("\n=== EVALUATION PROMPT ===")
    print(evaluation["evaluation_prompt"])

    return evaluation

if __name__ == "__main__":
    # Example usage
    print("Web Search Cheating Detector Ready!")
    print("Use evaluate_with_web_search_detection('log_file.json') to analyze logs")