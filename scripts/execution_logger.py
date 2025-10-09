"""
execution_logger.py - records everything that happens during an agent run to json log files

what this does:
- captures all events in chronological order: api calls, tool executions, thinking steps, web searches
- tracks metrics: tokens used, costs, execution times, success/failure rates
- compresses repetitive events (like repeated "workflow still running" checks) to reduce log file size
- preserves full details for important events (molecule lookups, workflow submissions, final results)
- saves structured json logs to: logs/{question_id}/{model_name}/{model_name}_{timestamp}.json
- these logs are later read by llm_judge_evaluator.py to grade agent performance

use this when: agent_runner.py imports this to log execution; you normally don't call this directly
"""

import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ToolCall(BaseModel):
    """Single tool execution with all details"""
    tool_name: str
    parameters: Dict[str, Any]
    timestamp_start: str
    timestamp_end: str
    execution_time_ms: float
    result: str
    success: bool
    error_message: Optional[str] = None

class ThinkingStep(BaseModel):
    """Agent's intermediate reasoning/thinking"""
    timestamp: str
    content: str
    reasoning_type: str  # "planning", "analysis", "decision", "reflection"

class ExecutionEvent(BaseModel):
    """Single event in chronological order - either thinking, tool execution, web search, or API call"""
    timestamp: str
    event_type: str  # "thinking", "tool_call", "web_search", or "api_call"
    content: Optional[str] = None  # For thinking steps
    reasoning_type: Optional[str] = None  # For thinking steps
    tool_name: Optional[str] = None  # For tool calls
    parameters: Optional[Dict[str, Any]] = None  # For tool calls
    execution_time_ms: Optional[float] = None  # For tool calls
    result: Optional[str] = None  # For tool calls
    success: Optional[bool] = None  # For tool calls
    error_message: Optional[str] = None  # For tool calls
    # Web search specific fields
    web_citations: Optional[List[str]] = None  # URLs found in web search
    web_content: Optional[str] = None  # Web search content
    # API call cost/token tracking
    api_model: Optional[str] = None  # Model used for API call
    generation_id: Optional[str] = None  # OpenRouter generation ID
    prompt_tokens: Optional[int] = None  # Tokens in prompt
    completion_tokens: Optional[int] = None  # Tokens in completion
    total_tokens: Optional[int] = None  # Total tokens used
    native_tokens_prompt: Optional[int] = None  # Native tokenizer prompt tokens
    native_tokens_completion: Optional[int] = None  # Native tokenizer completion tokens
    reasoning_tokens: Optional[int] = None  # Reasoning tokens (if applicable)
    cached_tokens: Optional[int] = None  # Cached tokens (if available)
    total_cost: Optional[float] = None  # Cost in USD/credits

class SimpleLogEntry(BaseModel):
    """Complete log entry with chronological execution flow"""
    # Basic info
    question_id: str
    model_name: str
    timestamp_start: str
    timestamp_end: str
    total_time_ms: float

    # User input
    user_question: str

    # Chronological execution flow
    execution_timeline: List[ExecutionEvent]

    # Final result
    final_answer: str

    # Success indicator
    completed_successfully: bool

    # Summary stats (for quick analysis)
    total_thinking_steps: int
    total_tool_calls: int
    successful_tool_calls: int
    total_web_searches: int
    total_api_calls: int

    # Cost and token totals
    total_cost_usd: float
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_native_prompt_tokens: int
    total_native_completion_tokens: int
    total_reasoning_tokens: int
    total_cached_tokens: int

class SimpleLogger:
    """Captures exactly what you want in the logs"""

    def __init__(self, question_id: str, user_question: str, model_name: str = "unknown"):
        self.question_id = question_id
        self.user_question = user_question
        self.model_name = model_name
        self.start_time = time.time()
        self.start_timestamp = datetime.now().isoformat()

        self.execution_timeline: List[ExecutionEvent] = []
        self.final_answer = ""
        self.completed_successfully = False

    def log_thinking(self, content: str, reasoning_type: str = "analysis"):
        """Log agent's intermediate thinking"""
        event = ExecutionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="thinking",
            content=content,
            reasoning_type=reasoning_type
        )
        self.execution_timeline.append(event)

        # Special formatting for polling wait messages
        if "wait" in content.lower() and ("second" in content.lower() or "minute" in content.lower()):
            print(f"⏱️  [{reasoning_type}] {content}")
        else:
            print(f"💭 [{reasoning_type}] {content}")

    def log_web_search(self, citations: List[str], content: str):
        """Log web search usage"""
        event = ExecutionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="web_search",
            web_citations=citations,
            web_content=content
        )
        self.execution_timeline.append(event)
        print(f"🌐 Web search used: {len(citations)} sources")

    def log_api_call(self, model: str, generation_id: str, prompt_tokens: int, completion_tokens: int, total_tokens: int, reasoning_tokens: int = 0, cached_tokens: int = 0):
        """Log API call with basic token info"""
        event = ExecutionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="api_call",
            api_model=model,
            generation_id=generation_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            reasoning_tokens=reasoning_tokens,
            cached_tokens=cached_tokens
        )
        self.execution_timeline.append(event)
        print(f"💰 API call: {model} - {prompt_tokens} input + {completion_tokens} output = {total_tokens} total tokens")

    def update_api_call_costs(self, generation_id: str, native_prompt_tokens: int, native_completion_tokens: int, cost: float, is_estimated: bool = False):
        """Update API call with cost and native token info"""
        # Find the most recent API call with this generation_id and update it
        for event in reversed(self.execution_timeline):
            if event.event_type == "api_call" and event.generation_id == generation_id:
                event.native_tokens_prompt = native_prompt_tokens
                event.native_tokens_completion = native_completion_tokens
                event.total_cost = cost

                # Show if cost is estimated (Anthropic direct API) or actual (OpenRouter)
                cost_label = "~$" if is_estimated else "$"
                estimate_note = " (estimated)" if is_estimated else ""
                print(f"💰 Updated API call costs: {cost_label}{cost:.6f} ({native_prompt_tokens + native_completion_tokens} native tokens){estimate_note}")
                break

    def start_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Start tracking a tool call, returns call_id for later completion"""
        call_id = f"{tool_name}_{len(self.execution_timeline)}_{int(time.time()*1000)}"

        # Add tool start event to timeline
        event = ExecutionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="tool_call",
            tool_name=tool_name,
            parameters=parameters
        )
        self.execution_timeline.append(event)
        print(f"🔧 Starting {tool_name} with parameters: {parameters}")

        return call_id

    def complete_tool_call(self, call_id: str, result: str, success: bool, error_message: str = None):
        """Complete a tool call with its result"""
        # Find the most recent tool call event and update it
        for i in range(len(self.execution_timeline) - 1, -1, -1):
            event = self.execution_timeline[i]
            if event.event_type == "tool_call" and event.result is None:
                # Calculate execution time
                start_time = datetime.fromisoformat(event.timestamp).timestamp()
                end_time = time.time()
                execution_time_ms = (end_time - start_time) * 1000

                # Update the event with results
                event.execution_time_ms = execution_time_ms
                event.result = result
                event.success = success
                event.error_message = error_message

                status = "✅" if success else "❌"
                print(f"{status} Tool completed in {execution_time_ms:.0f}ms")
                print(f"   Result: {result[:100]}{'...' if len(result) > 100 else ''}")
                break

    def set_final_answer(self, answer: str, success: bool = True):
        """Set the final answer"""
        self.final_answer = answer
        self.completed_successfully = success
        print(f"🎯 Final answer: {answer}")

    def compress_repetitive_events(self) -> List[ExecutionEvent]:
        """
        Intelligently compress repetitive events while preserving important details.

        Compression rules:
        1. Workflow status checks: Compress repeated "RUNNING" checks into one summary
        2. Wait periods: Compress multiple "waiting" messages into one
        3. Tool calls: Keep FULL details for:
           - Initial submissions (submit_*_workflow)
           - Final retrievals (retrieve_workflow)
           - Molecule lookups
           - Any tool that returns structured data (SMILES, results, etc.)
        4. Thinking steps: Keep all (they're usually concise)
        5. API calls: Keep all (for cost tracking)
        """
        if not self.execution_timeline:
            return []

        compressed = []
        i = 0

        while i < len(self.execution_timeline):
            event = self.execution_timeline[i]

            # Always keep: API calls, thinking steps (they're small)
            if event.event_type in ["api_call", "thinking"]:
                compressed.append(event)
                i += 1
                continue

            # For tool calls, apply smart compression
            if event.event_type == "tool_call":
                tool_name = event.tool_name or ""
                result_preview = (event.result or "")[:200].lower()

                # Check if this is a repetitive status check
                is_status_check = (
                    tool_name == "workflow_get_status" and
                    ("running" in result_preview or "is_running" in result_preview)
                )

                if is_status_check:
                    # Count consecutive status checks
                    consecutive_checks = 1
                    j = i + 1

                    while j < len(self.execution_timeline):
                        next_event = self.execution_timeline[j]

                        # Stop if not a tool call
                        if next_event.event_type != "tool_call":
                            break

                        # Stop if different tool or not a status check
                        if next_event.tool_name != "workflow_get_status":
                            break

                        next_result = (next_event.result or "")[:200].lower()
                        if "running" not in next_result and "is_running" not in next_result:
                            break  # Found the completion check

                        consecutive_checks += 1
                        j += 1

                    # Compress: Keep first check + summary
                    if consecutive_checks > 1:
                        # Keep first check with compressed result
                        compressed_event = ExecutionEvent(
                            timestamp=event.timestamp,
                            event_type="tool_call",
                            tool_name=event.tool_name,
                            parameters=event.parameters,
                            execution_time_ms=event.execution_time_ms,
                            result=f"[Compressed: Checked status {consecutive_checks} times - workflow still running]",
                            success=event.success
                        )
                        compressed.append(compressed_event)

                        # Skip to the last check (which should be the completion)
                        i = j
                        continue

                # Keep FULL details for important tool calls
                is_important_tool = (
                    "submit" in tool_name.lower() or           # Initial submissions
                    "retrieve" in tool_name.lower() or         # Final retrievals
                    "molecule_lookup" in tool_name.lower() or  # Molecule lookups
                    "smiles" in result_preview or              # Has SMILES data
                    "conformer" in result_preview or           # Conformer data
                    len(event.result or "") < 500              # Short results (likely important)
                )

                if is_important_tool:
                    # Keep full details
                    compressed.append(event)
                else:
                    # Truncate long results for other tools
                    if event.result and len(event.result) > 500:
                        truncated_event = ExecutionEvent(
                            timestamp=event.timestamp,
                            event_type=event.event_type,
                            tool_name=event.tool_name,
                            parameters=event.parameters,
                            execution_time_ms=event.execution_time_ms,
                            result=event.result[:500] + f"... [truncated {len(event.result) - 500} chars]",
                            success=event.success,
                            error_message=event.error_message
                        )
                        compressed.append(truncated_event)
                    else:
                        compressed.append(event)

            else:
                # Keep all other event types
                compressed.append(event)

            i += 1

        # Log compression stats
        original_count = len(self.execution_timeline)
        compressed_count = len(compressed)
        if compressed_count < original_count:
            print(f"  Original timeline events: {original_count}")
            print(f"  After workflow consolidation: {compressed_count}")

        return compressed

    def create_log_entry(self) -> SimpleLogEntry:
        """Create the final log entry with intelligent compression"""
        end_time = time.time()
        total_time = (end_time - self.start_time) * 1000

        # Compress repetitive events before creating log entry
        compressed_timeline = self.compress_repetitive_events()

        # Calculate summary stats from ORIGINAL timeline (for accuracy)
        thinking_steps = sum(1 for event in self.execution_timeline if event.event_type == "thinking")
        tool_calls = sum(1 for event in self.execution_timeline if event.event_type == "tool_call")
        successful_tools = sum(1 for event in self.execution_timeline
                             if event.event_type == "tool_call" and event.success == True)
        web_searches = sum(1 for event in self.execution_timeline if event.event_type == "web_search")
        api_calls = sum(1 for event in self.execution_timeline if event.event_type == "api_call")

        # Calculate cost and token totals from ORIGINAL timeline
        total_cost = sum(event.total_cost or 0 for event in self.execution_timeline if event.event_type == "api_call")
        total_prompt_tokens = sum(event.prompt_tokens or 0 for event in self.execution_timeline if event.event_type == "api_call")
        total_completion_tokens = sum(event.completion_tokens or 0 for event in self.execution_timeline if event.event_type == "api_call")
        total_tokens = sum(event.total_tokens or 0 for event in self.execution_timeline if event.event_type == "api_call")
        total_native_prompt = sum(event.native_tokens_prompt or 0 for event in self.execution_timeline if event.event_type == "api_call")
        total_native_completion = sum(event.native_tokens_completion or 0 for event in self.execution_timeline if event.event_type == "api_call")
        total_reasoning = sum(event.reasoning_tokens or 0 for event in self.execution_timeline if event.event_type == "api_call")
        total_cached = sum(event.cached_tokens or 0 for event in self.execution_timeline if event.event_type == "api_call")

        return SimpleLogEntry(
            question_id=self.question_id,
            model_name=self.model_name,
            timestamp_start=self.start_timestamp,
            timestamp_end=datetime.now().isoformat(),
            total_time_ms=total_time,
            user_question=self.user_question,
            execution_timeline=compressed_timeline,  # Use compressed timeline
            final_answer=self.final_answer,
            completed_successfully=self.completed_successfully,
            total_thinking_steps=thinking_steps,
            total_tool_calls=tool_calls,
            successful_tool_calls=successful_tools,
            total_web_searches=web_searches,
            total_api_calls=api_calls,
            total_cost_usd=total_cost,
            total_prompt_tokens=total_prompt_tokens,
            total_completion_tokens=total_completion_tokens,
            total_tokens=total_tokens,
            total_native_prompt_tokens=total_native_prompt,
            total_native_completion_tokens=total_native_completion,
            total_reasoning_tokens=total_reasoning,
            total_cached_tokens=total_cached
        )

    def save_to_file(self, filepath: str, format: str = "json"):
        """Save log entry to JSON or JSONL file, organized by model folders"""
        import os

        log_entry = self.create_log_entry()

        # Extract directory and filename
        log_dir = os.path.dirname(filepath)
        filename = os.path.basename(filepath)

        # Create model folder path - sanitize model name for filesystem
        model_folder = self.model_name.replace("/", "_").replace(":", "_")
        model_dir = os.path.join(log_dir, model_folder)

        # Create model directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)

        # Update filepath to include model folder
        filepath = os.path.join(model_dir, filename)

        # Get raw log data - exclude None/null fields
        compressed_log_data = log_entry.model_dump(exclude_none=True)

        if format == "json":
            # Save as pretty-printed JSON
            filepath = filepath.replace('.jsonl', '.json')
            with open(filepath, 'w') as f:
                json.dump(compressed_log_data, f, indent=2, ensure_ascii=False)
        else:
            # Save as JSONL (original format)
            with open(filepath, 'a') as f:
                f.write(json.dumps(compressed_log_data) + '\n')

        print(f"📝 Compressed log saved to {filepath}")

        # Print summary
        print(f"📊 Summary: {log_entry.successful_tool_calls}/{log_entry.total_tool_calls} tools successful, {log_entry.total_thinking_steps} thinking steps, {log_entry.total_time_ms:.0f}ms total")

        cost_summary = f"💰 API Usage: {log_entry.total_api_calls} calls, ${log_entry.total_cost_usd:.6f} cost, {log_entry.total_tokens} tokens"
        native_total = log_entry.total_native_prompt_tokens + log_entry.total_native_completion_tokens
        if native_total > 0:
            cost_summary += f" ({native_total} native)"
        if log_entry.total_reasoning_tokens > 0:
            cost_summary += f", {log_entry.total_reasoning_tokens} reasoning"
        if log_entry.total_cached_tokens > 0:
            cost_summary += f", {log_entry.total_cached_tokens} cached"
        print(cost_summary)

        return log_entry