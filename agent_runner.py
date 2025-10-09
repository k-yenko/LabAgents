"""
agent_runner.py - runs chemistry benchmark questions against ai models (anthropic direct api or openrouter)

what this does:
- takes a question id (e.g., tier1_007) and model name (e.g., anthropic/claude-opus-4.1)
- automatically routes anthropic models to direct anthropic api (cheaper, avoids openrouter)
- routes all other models through openrouter (openai, google, deepseek, etc.)
- manages the full conversation loop: question → api call → tool execution → answer
- implements optimizations: message pruning after iteration 5, proactive rate limiting, smart retries
- uses execution_logger.py to record everything that happens to json log files
- saves final results to: logs/{question_id}/{model_name}/{model_name}_{timestamp}.json

use this when: you want to run a single question against a model and get a complete execution log
"""

from openai import OpenAI
import anthropic
import os
import json
import warnings
import subprocess
import sys
import time
import re
import asyncio
import requests
from contextlib import contextmanager, asynccontextmanager
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from collections import deque
from datetime import datetime, timedelta

# Import our execution logger
from scripts.execution_logger import SimpleLogger
from system_prompt_template import create_system_prompt
from scripts.questions import get_questions_by_tier, ALL_QUESTIONS

# Suppress pydantic warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Token rate limiter for Anthropic API
class TokenRateLimiter:
    """Rate limiter to prevent hitting Anthropic's 30k tokens/minute limit"""
    def __init__(self, tokens_per_minute=30000, buffer_ratio=0.8):
        self.max_tokens = int(tokens_per_minute * buffer_ratio)  # Use 80% to be safe
        self.window_seconds = 60
        self.requests = deque()  # Store (timestamp, token_count) tuples

    def wait_if_needed(self, estimated_tokens):
        """Wait if adding this request would exceed rate limit"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)

        # Remove old requests outside the window
        while self.requests and self.requests[0][0] < cutoff:
            self.requests.popleft()

        # Calculate tokens used in current window
        tokens_in_window = sum(tokens for _, tokens in self.requests)

        # If adding this request would exceed limit, wait
        if tokens_in_window + estimated_tokens > self.max_tokens:
            # Calculate how long to wait
            if self.requests:
                oldest_timestamp, oldest_tokens = self.requests[0]
                wait_seconds = (oldest_timestamp + timedelta(seconds=self.window_seconds) - now).total_seconds()
                if wait_seconds > 0:
                    print(f"⏱️  Rate limit prevention: waiting {wait_seconds:.1f}s (current window: {tokens_in_window:,} tokens)")
                    time.sleep(wait_seconds + 1)  # Add 1 second buffer
                    # Recursively check again after waiting
                    return self.wait_if_needed(estimated_tokens)

        # Record this request
        self.requests.append((now, estimated_tokens))

    def reset(self):
        """Reset the rate limiter"""
        self.requests.clear()

# Global rate limiter instance
anthropic_rate_limiter = TokenRateLimiter()

def prune_conversation_history(messages, max_recent_exchanges=3, always_keep_first=True):
    """
    Prune conversation history to reduce token usage while maintaining context.

    Preserves tool_use/tool_result pairs to avoid breaking OpenAI/Anthropic API requirements.
    CRITICAL: Never removes a tool_result without its corresponding tool_use, and vice versa.

    Args:
        messages: List of message dictionaries
        max_recent_exchanges: Keep only the last N exchanges (user+assistant pairs)
        always_keep_first: Always keep the first user message (the original question)

    Returns:
        Pruned list of messages
    """
    if len(messages) <= 6:  # Too short to prune (need at least a few exchanges)
        return messages

    # Build a map of tool_use_id -> message_index for tool_use blocks
    tool_use_map = {}
    for i, msg in enumerate(messages):
        if msg["role"] == "assistant":
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_use_map[block.get("id")] = i

    # Build a set of message indices we MUST keep (tool dependencies)
    must_keep_indices = set()

    # For each tool_result, find its corresponding tool_use and mark BOTH as must-keep
    for i, msg in enumerate(messages):
        if msg["role"] == "user":
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        tool_use_id = block.get("tool_use_id")
                        if tool_use_id and tool_use_id in tool_use_map:
                            # CRITICAL: Mark both the tool_use and tool_result messages as must-keep
                            must_keep_indices.add(tool_use_map[tool_use_id])
                            must_keep_indices.add(i)

    # Calculate cutoff for recent messages
    exchanges_to_keep = max_recent_exchanges * 3  # Rough estimate: user, assistant, tool result
    cutoff_index = max(1, len(messages) - exchanges_to_keep)  # Never cut before message 1

    # Build keep_indices: messages we want to keep
    keep_indices = set()

    # Always keep first message if requested
    if always_keep_first:
        keep_indices.add(0)

    # Keep all recent messages (after cutoff)
    for i in range(cutoff_index, len(messages)):
        keep_indices.add(i)

    # Add all must-keep tool dependency messages
    keep_indices.update(must_keep_indices)

    # CRITICAL FIX: If we're keeping a tool_result but not its tool_use (or vice versa),
    # we MUST keep both to avoid API errors
    for i in list(keep_indices):  # Iterate over copy since we'll modify the set
        msg = messages[i]

        # Check if this is a tool_result
        if msg["role"] == "user":
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        tool_use_id = block.get("tool_use_id")
                        if tool_use_id and tool_use_id in tool_use_map:
                            # Ensure the corresponding tool_use is also kept
                            keep_indices.add(tool_use_map[tool_use_id])

        # Check if this is a tool_use
        elif msg["role"] == "assistant":
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_use_id = block.get("id")
                        # Find the corresponding tool_result
                        for j, other_msg in enumerate(messages):
                            if other_msg["role"] == "user":
                                other_content = other_msg.get("content", [])
                                if isinstance(other_content, list):
                                    for other_block in other_content:
                                        if isinstance(other_block, dict) and \
                                           other_block.get("type") == "tool_result" and \
                                           other_block.get("tool_use_id") == tool_use_id:
                                            # Ensure the corresponding tool_result is also kept
                                            keep_indices.add(j)

    # Build pruned list in order
    pruned = [messages[i] for i in sorted(keep_indices)]

    # Log pruning
    if len(pruned) < len(messages):
        tokens_saved = sum(len(str(msg.get("content", ""))) for msg in messages if messages.index(msg) not in keep_indices) // 4
        print(f"📉 Pruned conversation: {len(messages)} → {len(pruned)} messages (~{tokens_saved:,} tokens saved)")

    return pruned

@contextmanager
def suppress_output():
    """Context manager to suppress stdout and stderr"""
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = devnull
            sys.stderr = devnull
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

# Custom StdioServerParameters that redirects stderr
class SilentStdioServerParameters(StdioServerParameters):
    def __init__(self, command, args=None, env=None, cwd=None):
        if args is None:
            args = []

        super().__init__(
            command="bash",
            args=["-c", f"exec {command} {' '.join(args)} 2>/dev/null"],
            env=env,
            cwd=cwd
        )

load_dotenv()

def extract_wait_time(text: str) -> int:
    """Extract wait time in seconds from agent's message"""
    text = text.lower()

    # Patterns to match wait announcements
    patterns = [
        r"i'll wait (\d+) seconds",
        r"wait (\d+) seconds",
        r"waiting (\d+) seconds",
        r"i'll check.* in (\d+) seconds",
        r"check status in (\d+) seconds"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    return 0

async def smart_wait(seconds: int, logger: SimpleLogger):
    """Actually wait the specified time with progress updates"""
    if seconds <= 0:
        return

    print(f"⏳ Actually waiting {seconds} seconds for smart polling...")
    logger.log_thinking(f"System: Actually waiting {seconds} seconds as requested by agent", "analysis")

    # Wait in chunks to show progress for long waits
    if seconds <= 30:
        await asyncio.sleep(seconds)
    else:
        # For longer waits, show progress every 30 seconds
        remaining = seconds
        while remaining > 0:
            chunk = min(30, remaining)
            await asyncio.sleep(chunk)
            remaining -= chunk
            if remaining > 0:
                print(f"⏳ Still waiting... {remaining} seconds remaining")

    print(f"✅ Wait complete! Proceeding after {seconds} seconds")

def query_generation_stats_sync(generation_id: str, api_key: str):
    """Query OpenRouter generation stats for cost and native token counts (synchronous)"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Use requests for synchronous call since we need the results immediately
        response = requests.get(
            f"https://openrouter.ai/api/v1/generation?id={generation_id}",
            headers=headers
        )

        if response.status_code == 200:
            stats = response.json()
            return {
                "native_tokens_prompt": stats.get("usage", {}).get("native_tokens_prompt", 0),
                "native_tokens_completion": stats.get("usage", {}).get("native_tokens_completion", 0),
                "total_cost": stats.get("usage", {}).get("total_cost", 0.0)
            }
        else:
            print(f"Failed to query generation stats: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error querying generation stats: {e}")
        return None

async def get_mcp_tools():
    """Connect to Rowan MCP server and get list of available tools"""
    rowan_mcp_dir = "/Users/katherineyenko/Desktop/sandbox/rowan-mcp"
    venv_python = os.path.join(rowan_mcp_dir, ".venv", "bin", "python")

    env = dict(os.environ)
    env["PYTHONWARNINGS"] = "ignore"
    env["FASTMCP_QUIET"] = "1"
    env["LOGGING_LEVEL"] = "ERROR"

    server_params = SilentStdioServerParameters(
        command=venv_python,
        args=["-m", "rowan_mcp.server"],
        env=env,
        cwd=rowan_mcp_dir
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()

            tools = []
            for tool in tools_result.tools:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {"type": "object", "properties": {}}
                    }
                })
            return tools

async def call_mcp_tool(tool_name, arguments):
    """Execute a specific tool on the Rowan MCP server"""
    rowan_mcp_dir = "/Users/katherineyenko/Desktop/sandbox/rowan-mcp"
    venv_python = os.path.join(rowan_mcp_dir, ".venv", "bin", "python")

    env = dict(os.environ)
    env["PYTHONWARNINGS"] = "ignore"
    env["FASTMCP_QUIET"] = "1"
    env["LOGGING_LEVEL"] = "ERROR"

    server_params = SilentStdioServerParameters(
        command=venv_python,
        args=["-m", "rowan_mcp.server"],
        env=env,
        cwd=rowan_mcp_dir
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)

            if hasattr(result, 'content') and result.content:
                content_text = ""
                for content_item in result.content:
                    if hasattr(content_item, 'text'):
                        content_text += content_item.text
                    else:
                        content_text += str(content_item)
                return content_text
            else:
                return str(result)

def openai_to_anthropic_tools(openai_tools):
    """Convert OpenAI tool format to Anthropic tool format"""
    anthropic_tools = []
    for tool in openai_tools:
        if tool.get("type") == "function":
            func = tool["function"]
            anthropic_tool = {
                "name": func["name"],
                "description": func.get("description", ""),
                "input_schema": func.get("parameters", {})
            }
            anthropic_tools.append(anthropic_tool)
    return anthropic_tools

class ToolCallWrapper:
    """Wrapper for tool call dict to provide attribute access"""
    def __init__(self, tool_call_dict):
        self.id = tool_call_dict.get("id")
        self.type = tool_call_dict.get("type")
        self.function = type('obj', (object,), {
            'name': tool_call_dict.get("function", {}).get("name"),
            'arguments': tool_call_dict.get("function", {}).get("arguments")
        })()

class MessageWrapper:
    """Simple wrapper to make dict behave like OpenRouter message object"""
    def __init__(self, message_dict):
        self.role = message_dict.get("role")
        self.content = message_dict.get("content")

        # Wrap tool_calls to provide attribute access
        tool_calls = message_dict.get("tool_calls")
        if tool_calls:
            self.tool_calls = [ToolCallWrapper(tc) for tc in tool_calls]
        else:
            self.tool_calls = None

def anthropic_to_openai_message(anthropic_message):
    """Convert Anthropic message format to OpenAI format for logging consistency"""
    openai_message = {
        "role": "assistant",
        "content": ""
    }

    # Handle content and tool calls
    if anthropic_message.content:
        text_content = ""
        tool_calls = []

        for content_block in anthropic_message.content:
            if content_block.type == "text":
                text_content += content_block.text
            elif content_block.type == "tool_use":
                tool_call = {
                    "id": content_block.id,
                    "type": "function",
                    "function": {
                        "name": content_block.name,
                        "arguments": json.dumps(content_block.input)
                    }
                }
                tool_calls.append(tool_call)

        openai_message["content"] = text_content
        if tool_calls:
            openai_message["tool_calls"] = tool_calls

    # Return wrapped object that behaves like OpenRouter message
    return MessageWrapper(openai_message)

async def test_with_simple_logging(main_question: str, question_id: str, model_name: str = "anthropic/claude-sonnet-4", enable_web_search: bool = True):
    """Test with simple focused logging"""

    # Create complete prompt using template
    user_question = create_system_prompt(main_question, enable_web_search)

    # Initialize logger
    logger = SimpleLogger(
        question_id=question_id,
        user_question=main_question,  # Store the clean question in logs
        model_name=model_name
    )

    try:
        # Step 1: Get available tools (no logging - this is system setup)
        tools = await get_mcp_tools()
        print(f"Retrieved {len(tools)} available tools")

        # Step 2: Set up API client (no logging - this is system setup)
        # Auto-route all Anthropic models to direct API
        use_anthropic_direct = model_name.startswith("anthropic/") or model_name.startswith("anthropic-direct/")

        if use_anthropic_direct:
            # Use Anthropic's direct API
            anthropic_client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
            )

            # Map OpenRouter model names to official Claude API names
            model_mapping = {
                "anthropic/claude-opus-4.1": "claude-opus-4-1-20250805",
                "anthropic/claude-sonnet-4": "claude-3-5-sonnet-20241022",
                "anthropic/claude-sonnet-4.5": "claude-sonnet-4-5-20250929",
                "anthropic-direct/claude-3-5-sonnet-20241022": "claude-3-5-sonnet-20241022",
                "anthropic-direct/claude-3-5-sonnet-20250106": "claude-3-5-sonnet-20250106",
                "anthropic-direct/claude-opus-4-1-20250805": "claude-opus-4-1-20250805",
                "anthropic-direct/claude-sonnet-4-5-20250929": "claude-sonnet-4-5-20250929"
            }

            actual_model_name = model_mapping.get(model_name, model_name.replace("anthropic/", "").replace("anthropic-direct/", ""))
            client = None  # We'll use anthropic_client instead
            print(f"🔄 Auto-routing {model_name} → Anthropic API ({actual_model_name})")
        else:
            # Use OpenRouter API for non-Anthropic models
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )
            anthropic_client = None
            actual_model_name = model_name

        # Step 3: Main conversation loop
        messages = [
            {
                "role": "user",
                "content": user_question
            }
        ]

        iteration = 0

        while True:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")

            # Prune conversation history after iteration 5 to reduce token usage
            # DISABLED for GPT-5 due to tool call chain breaking issues with OpenRouter
            if iteration > 5 and "gpt-5" not in model_name.lower():
                messages = prune_conversation_history(messages, max_recent_exchanges=3)

            # Get response from AI with the determined model
            # Retry logic for transient errors (SSL, timeouts, etc)
            max_retries = 3
            retry_count = 0
            last_error = None

            while retry_count < max_retries:
                try:
                    if use_anthropic_direct:
                        # Use Anthropic direct API
                        anthropic_tools = openai_to_anthropic_tools(tools)

                        # Convert messages to Anthropic format (system message separate)
                        system_message = None
                        anthropic_messages = []

                        for msg in messages:
                            if msg["role"] == "system":
                                system_message = msg["content"]
                            else:
                                anthropic_messages.append(msg)

                        # Build API call parameters
                        api_params = {
                            "model": actual_model_name,
                            "max_tokens": 4096,
                            "messages": anthropic_messages,
                        }

                        # Only add system message if it exists
                        if system_message:
                            api_params["system"] = system_message

                        # Only add tools if they exist
                        if anthropic_tools:
                            api_params["tools"] = anthropic_tools

                        # Estimate tokens in the request (rough approximation)
                        estimated_tokens = 0
                        for msg in anthropic_messages:
                            content = msg.get("content", "")
                            if isinstance(content, str):
                                estimated_tokens += len(content) // 4  # ~4 chars per token
                            elif isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and "text" in item:
                                        estimated_tokens += len(item["text"]) // 4
                        if system_message:
                            estimated_tokens += len(system_message) // 4

                        # Wait if needed to avoid rate limit
                        anthropic_rate_limiter.wait_if_needed(estimated_tokens)

                        response = anthropic_client.messages.create(**api_params)

                        # Convert back to OpenAI format for consistent logging
                        message = anthropic_to_openai_message(response)
                    else:
                        # Use OpenRouter API
                        completion = client.chat.completions.create(
                            model=actual_model_name,
                            messages=messages,
                            tools=tools,
                            tool_choice="auto",
                            extra_body={"usage": {"include": True}}  # Enable native tokenizer usage accounting
                        )
                        message = completion.choices[0].message

                    # Success - break out of retry loop
                    break

                except json.JSONDecodeError as e:
                    # API returned malformed JSON - this is not retryable
                    api_name = "Anthropic" if use_anthropic_direct else "OpenRouter"
                    error_msg = f"{api_name} API returned malformed JSON: {str(e)}"
                    print(f"❌ API Error: {error_msg}")
                    logger.set_final_answer(error_msg, success=False)

                    # Create logs directory structure: logs/{question_id}/
                    log_dir = os.path.join("logs", question_id)
                    os.makedirs(log_dir, exist_ok=True)

                    # Save error log with raw error details
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    clean_model_name = model_name.replace("/", "_")
                    log_filename = os.path.join(log_dir, f"{clean_model_name}_api_error_{timestamp}.json")
                    log_entry = logger.save_to_file(log_filename, format="json")

                    return log_entry

                except Exception as e:
                    # Potentially retryable errors (SSL, timeouts, rate limits)
                    last_error = e
                    retry_count += 1

                    api_name = "Anthropic" if use_anthropic_direct else "OpenRouter"

                    if retry_count < max_retries:
                        # Detect rate limit errors (429) - need longer wait time
                        error_str = str(e).lower()
                        is_rate_limit = '429' in str(e) or 'rate_limit' in error_str or 'rate limit' in error_str

                        if is_rate_limit:
                            # Rate limits are per-minute, so wait for window to reset
                            # Add exponential backoff for repeated rate limits
                            base_wait = 60
                            wait_time = base_wait + (retry_count * 15)  # 60, 75, 90 seconds
                            print(f"⚠️  {api_name} rate limit hit (attempt {retry_count}/{max_retries})")
                            print(f"   Waiting {wait_time} seconds for rate limit window to reset...")

                            # Reset the rate limiter to start fresh
                            if use_anthropic_direct:
                                anthropic_rate_limiter.reset()
                        else:
                            # Other transient errors - exponential backoff: 2, 4, 8 seconds
                            wait_time = 2 ** retry_count
                            print(f"⚠️  {api_name} API error (attempt {retry_count}/{max_retries}): {str(e)}")
                            print(f"   Retrying in {wait_time} seconds...")

                        time.sleep(wait_time)
                    else:
                        # Max retries exceeded
                        error_msg = f"{api_name} API error after {max_retries} attempts: {str(e)}"
                        print(f"❌ API Error: {error_msg}")

                        # Add more debugging info for Anthropic API errors
                        if use_anthropic_direct:
                            print(f"   Model: {actual_model_name}")
                            print(f"   API Key exists: {bool(os.getenv('ANTHROPIC_API_KEY'))}")
                            print(f"   Full error: {repr(e)}")

                        logger.set_final_answer(error_msg, success=False)

                        # Create logs directory structure: logs/{question_id}/
                        log_dir = os.path.join("logs", question_id)
                        os.makedirs(log_dir, exist_ok=True)

                        # Save error log with raw error details
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        clean_model_name = model_name.replace("/", "_")
                        log_filename = os.path.join(log_dir, f"{clean_model_name}_api_error_{timestamp}.json")
                        log_entry = logger.save_to_file(log_filename, format="json")

                        return log_entry

            # If we got here after retry loop without success, handle it
            if retry_count >= max_retries and last_error:
                continue  # This return was already handled in the except block above

            # Log API call with comprehensive usage info from response
            if use_anthropic_direct:
                # Anthropic API response structure
                generation_id = response.id
                usage = response.usage if hasattr(response, 'usage') else None

                if usage:
                    prompt_tokens = usage.input_tokens
                    completion_tokens = usage.output_tokens
                    total_tokens = usage.input_tokens + usage.output_tokens
                else:
                    prompt_tokens = completion_tokens = total_tokens = 0
            else:
                # OpenRouter API response structure
                generation_id = completion.id
                usage = completion.usage

                prompt_tokens = usage.prompt_tokens
                completion_tokens = usage.completion_tokens
                total_tokens = usage.total_tokens

            # Get native tokenizer counts and costs
            if use_anthropic_direct:
                # Anthropic doesn't provide native tokenizer details the same way
                native_prompt_tokens = prompt_tokens
                native_completion_tokens = completion_tokens

                # Estimate cost using Anthropic's pricing (as of Jan 2025)
                # Opus 4.1: $15/M input, $75/M output
                # Sonnet 4/4.5: $3/M input, $15/M output
                if "opus" in actual_model_name.lower():
                    input_cost_per_m = 15.0
                    output_cost_per_m = 75.0
                elif "sonnet" in actual_model_name.lower():
                    input_cost_per_m = 3.0
                    output_cost_per_m = 15.0
                else:
                    # Default to Sonnet pricing for unknown models
                    input_cost_per_m = 3.0
                    output_cost_per_m = 15.0

                cost = (prompt_tokens / 1_000_000 * input_cost_per_m) + (completion_tokens / 1_000_000 * output_cost_per_m)
                reasoning_tokens = 0
                cached_tokens = 0
            else:
                # OpenRouter provides detailed usage (available when usage={"include": True})
                native_prompt_tokens = getattr(usage, 'prompt_tokens', prompt_tokens)
                native_completion_tokens = getattr(usage, 'completion_tokens', completion_tokens)
                cost = getattr(usage, 'cost', 0.0)

                # Check for additional detailed usage information
                reasoning_tokens = 0
                cached_tokens = 0

                if hasattr(usage, 'completion_tokens_details'):
                    reasoning_tokens = getattr(usage.completion_tokens_details, 'reasoning_tokens', 0)

                if hasattr(usage, 'prompt_tokens_details'):
                    cached_tokens = getattr(usage.prompt_tokens_details, 'cached_tokens', 0)

            # Log API call with all available information
            logger.log_api_call(
                model=model_name,
                generation_id=generation_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                reasoning_tokens=reasoning_tokens,
                cached_tokens=cached_tokens
            )

            # Update with native tokenizer counts and cost immediately
            logger.update_api_call_costs(
                generation_id=generation_id,
                native_prompt_tokens=native_prompt_tokens,
                native_completion_tokens=native_completion_tokens,
                cost=cost,
                is_estimated=use_anthropic_direct  # Anthropic direct API has estimated costs
            )

            if reasoning_tokens > 0:
                print(f"🧠 Reasoning tokens: {reasoning_tokens}")
            if cached_tokens > 0:
                print(f"⚡ Cached tokens: {cached_tokens}")

            # Check for web search annotations and log them
            if hasattr(message, 'annotations') and message.annotations:
                citations = []
                web_content = []
                for annotation in message.annotations:
                    if annotation.type == "url_citation":
                        citations.append(annotation.url_citation.url)
                        if hasattr(annotation.url_citation, 'content'):
                            web_content.append(annotation.url_citation.content or "")

                if citations:
                    logger.log_web_search(citations, " | ".join(web_content))

            # Log AI's thinking if it provided reasoning
            if message.content:
                logger.log_thinking(
                    f"Agent reasoning: {message.content}",
                    reasoning_type="decision"
                )

                # Check if agent announced a wait time and actually wait
                wait_seconds = extract_wait_time(message.content)
                if wait_seconds > 0:
                    await smart_wait(wait_seconds, logger)

            # If no tool calls, we have our final answer
            if not message.tool_calls:
                print("\n--- Final Answer ---")
                print(message.content)

                print("Agent provided final answer without more tool calls")
                logger.set_final_answer(message.content, success=True)

                # Create logs directory structure: logs/{question_id}/
                log_dir = os.path.join("logs", question_id)
                os.makedirs(log_dir, exist_ok=True)

                # Save log as JSON with model_name_timestamp.json format
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                # Clean model name for filename (replace / with _)
                clean_model_name = model_name.replace("/", "_")
                log_filename = os.path.join(log_dir, f"{clean_model_name}_{timestamp}.json")
                log_entry = logger.save_to_file(log_filename, format="json")

                return log_entry

            # Add AI's message to conversation
            # Convert MessageWrapper back to dict for message list
            if hasattr(message, 'role'):
                if use_anthropic_direct:
                    # Anthropic API format: content is array with text and tool_use blocks
                    content_blocks = []
                    if message.content:
                        content_blocks.append({
                            "type": "text",
                            "text": message.content
                        })
                    if message.tool_calls:
                        for tc in message.tool_calls:
                            content_blocks.append({
                                "type": "tool_use",
                                "id": tc.id,
                                "name": tc.function.name,
                                "input": json.loads(tc.function.arguments) if tc.function.arguments else {}
                            })

                    message_dict = {
                        "role": message.role,
                        "content": content_blocks
                    }
                else:
                    # OpenRouter/OpenAI format: separate content and tool_calls fields
                    message_dict = {
                        "role": message.role,
                        "content": message.content
                    }
                    if message.tool_calls:
                        message_dict["tool_calls"] = [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            } for tc in message.tool_calls
                        ]
                messages.append(message_dict)
            else:
                messages.append(message)

            # Execute all tool calls
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name or "unknown_tool"

                # Handle malformed JSON arguments
                try:
                    tool_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                except json.JSONDecodeError:
                    tool_args = {"error": "malformed_arguments", "raw": tool_call.function.arguments}

                # Ensure tool_args is always a dict
                if not isinstance(tool_args, dict):
                    tool_args = {"error": "non_dict_arguments", "raw": str(tool_args)}

                logger.log_thinking(
                    f"Agent decided to call {tool_name} with parameters: {tool_args}",
                    reasoning_type="decision"
                )

                print(f"Executing tool: {tool_name} with args: {tool_args}")

                # Start tracking tool call
                call_id = logger.start_tool_call(tool_name, tool_args)

                try:
                    # Execute the MCP tool
                    tool_result = await call_mcp_tool(tool_name, tool_args)

                    # Complete tool call tracking
                    logger.complete_tool_call(call_id, tool_result, success=True)

                    print(f"Tool {tool_name} completed successfully")

                    # Add tool result to conversation
                    if use_anthropic_direct:
                        # Anthropic API format: tool results go in user message with tool_result content blocks
                        messages.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_call.id,
                                    "content": tool_result
                                }
                            ]
                        })
                    else:
                        # OpenRouter/OpenAI format: use "tool" role
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result
                        })

                    print(f"Tool result: {tool_result[:200]}...")

                except Exception as e:
                    # Complete tool call with error
                    error_msg = str(e)
                    logger.complete_tool_call(call_id, "", success=False, error_message=error_msg)

                    print(f"Tool {tool_name} failed with error: {error_msg}")

                    # Add error to conversation
                    if use_anthropic_direct:
                        # Anthropic API format: tool results go in user message with tool_result content blocks
                        messages.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_call.id,
                                    "content": f"Error: {error_msg}"
                                }
                            ]
                        })
                    else:
                        # OpenRouter/OpenAI format: use "tool" role
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": f"Error: {error_msg}"
                        })

        # This point should never be reached with proper system prompts
        # If we get here, something went wrong with the conversation flow

    except Exception as e:
        # Log error
        print(f"Error during execution: {e}")
        logger.set_final_answer(f"Error: {e}", success=False)

        # Create logs directory structure: logs/{question_id}/
        log_dir = os.path.join("logs", question_id)
        os.makedirs(log_dir, exist_ok=True)

        # Save error log
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        clean_model_name = model_name.replace("/", "_")
        log_filename = os.path.join(log_dir, f"{clean_model_name}_error_{timestamp}.json")
        log_entry = logger.save_to_file(log_filename, format="json")

        raise

if __name__ == "__main__":
    import asyncio
    import argparse

    parser = argparse.ArgumentParser(description="Run computational chemistry evaluation")
    parser.add_argument("target", help="Specify 'tier1', 'tier2', 'tier3', or specific question ID (e.g., 'tier2_002')")
    parser.add_argument("--model", "-m", default="anthropic/claude-sonnet-4",
                       help="Model to use (default: anthropic/claude-sonnet-4)")
    parser.add_argument("--all-models", action="store_true",
                       help="Run with all 8 recommended models (ignores --model)")
    parser.add_argument("--budget-models", action="store_true",
                       help="Run with budget models only (excludes expensive Anthropic models)")
    parser.add_argument("--force", action="store_true",
                       help="Force rerun even if logs already exist")

    args = parser.parse_args()
    target = args.target.lower()

    # Define all models for --all-models option
    ALL_MODELS = [
        "anthropic/claude-opus-4.1",      # Auto-routes to claude-opus-4-1-20250805
        "anthropic/claude-sonnet-4",      # Auto-routes to claude-3-5-sonnet-20241022
        "anthropic/claude-sonnet-4.5",    # Auto-routes to claude-sonnet-4-5-20250929
        "openai/gpt-5",
        "openai/o3",
        "x-ai/grok-4-fast:free",
        "google/gemini-2.5-pro",
        "deepseek/deepseek-chat-v3.1:free",
        "x-ai/grok-code-fast-1"
    ]

    # Budget models exclude expensive opus model
    BUDGET_MODELS = [
        "anthropic/claude-sonnet-4",      # Auto-routes to claude-3-5-sonnet-20241022
        "anthropic/claude-sonnet-4.5",    # Auto-routes to claude-sonnet-4-5-20250929
        "openai/gpt-5",
        "openai/o3",
        "x-ai/grok-4-fast:free",
        "google/gemini-2.5-pro",
        "deepseek/deepseek-chat-v3.1:free",
        "x-ai/grok-code-fast-1"
    ]

    # Determine which models to run
    if args.all_models:
        models_to_run = ALL_MODELS
        print(f"🚀 Running with all {len(ALL_MODELS)} models")
    elif args.budget_models:
        models_to_run = BUDGET_MODELS
        print(f"💰 Running with {len(BUDGET_MODELS)} budget models (excluding expensive Anthropic models)")
    else:
        models_to_run = [args.model]
        print(f"🤖 Using model: {args.model}")

    # Determine which questions to run
    if target == "tier1":
        questions = get_questions_by_tier(1)
        print(f"Running all Tier 1 questions ({len(questions)} questions)")
    elif target == "tier2":
        questions = get_questions_by_tier(2)
        print(f"Running all Tier 2 questions ({len(questions)} questions)")
    elif target == "tier3":
        questions = get_questions_by_tier(3)
        print(f"Running all Tier 3 questions ({len(questions)} questions)")
    elif target in ALL_QUESTIONS:
        questions = {target: ALL_QUESTIONS[target]}
        print(f"Running single question: {target}")
    else:
        print(f"Error: '{target}' not found")
        print("Available options:")
        print("  - tier1 (run all tier 1 questions)")
        print("  - tier2 (run all tier 2 questions)")
        print("  - tier3 (run all tier 3 questions)")
        print("  - Specific question IDs:", ", ".join(sorted(ALL_QUESTIONS.keys())))
        sys.exit(1)

    # Show what will be run
    for qid, question in questions.items():
        print(f"  {qid}: {question}")
    print()

    # Run each question with each model
    for question_id, question_text in questions.items():
        for model_name in models_to_run:
            # Check if log already exists to avoid rerunning
            log_dir = os.path.join("logs", question_id)
            # Directory uses full cleaning (both / and :)
            dir_clean_model_name = model_name.replace("/", "_").replace(":", "_")
            model_log_dir = os.path.join(log_dir, dir_clean_model_name)
            # Files only replace / (to match log creation logic)
            file_clean_model_name = model_name.replace("/", "_")
            existing_logs = []
            if os.path.exists(model_log_dir):
                import glob
                existing_logs = glob.glob(os.path.join(model_log_dir, f"{file_clean_model_name}_*.json"))

            if existing_logs and not args.force:
                print(f"⏭️  Skipping {question_id} with {model_name} (log already exists: {os.path.basename(existing_logs[0])})")
                continue

            print(f"Starting evaluation for {question_id} with {model_name}")
            asyncio.run(test_with_simple_logging(question_text, question_id, model_name))
            print(f"✅ Completed {question_id} with {model_name}\n")