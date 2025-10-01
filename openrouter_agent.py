"""
MCP OpenRouter test with simple focused logging
Captures: question, tools called, parameters, timestamps, thinking steps, results
"""

from openai import OpenAI
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

# Import our simple logger
from scripts.simple_structured_logger import SimpleLogger
from system_prompt_template import create_system_prompt
from scripts.questions import get_questions_by_tier, ALL_QUESTIONS
from scripts.log_compressor import compress_log_file

# Suppress pydantic warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

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

        # Step 2: Set up OpenRouter client (no logging - this is system setup)
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

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

            # Get response from AI with the determined model
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    extra_body={"usage": {"include": True}}  # Enable native tokenizer usage accounting
                )
                message = completion.choices[0].message
            except json.JSONDecodeError as e:
                # OpenRouter returned malformed JSON - log raw error and move on
                error_msg = f"OpenRouter API returned malformed JSON: {str(e)}"
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
                # Other API errors (rate limits, timeouts, etc)
                error_msg = f"OpenRouter API error: {str(e)}"
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

            # Log API call with comprehensive usage info from response
            generation_id = completion.id
            usage = completion.usage

            # Extract detailed usage information
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens

            # Get native tokenizer counts and costs (available when usage={"include": True})
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
                cost=cost
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
        "anthropic/claude-opus-4.1",
        "anthropic/claude-sonnet-4",
        "openai/gpt-5",
        "openai/o3",
        "x-ai/grok-4-fast:free",
        "google/gemini-2.5-pro",
        "deepseek/deepseek-chat-v3.1:free",
        "x-ai/grok-code-fast-1"
    ]

    # Budget models exclude expensive opus model
    BUDGET_MODELS = [
        "anthropic/claude-sonnet-4",
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