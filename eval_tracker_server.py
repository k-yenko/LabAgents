"""
Simple MCP Server for Eval Session Tracking
Runs alongside the main Rowan MCP server to capture eval metrics.
"""

import os
import sys
import json
import time
from datetime import datetime
from fastmcp import FastMCP

# Initialize FastMCP server for eval tracking
mcp = FastMCP("Eval Tracker MCP Server")

# Session storage - now supports multiple concurrent sessions by model
active_sessions = {}  # model_name -> session_data

# Simple event logging for model behavior
model_events = []  # List of all events that happen

def log_event(event_type: str, model: str, question_id: str = None, details: dict = None) -> None:
    """Log any event that happens during evaluation"""
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "model": model,
        "question_id": question_id,
        "details": details or {}
    }
    model_events.append(event)
    
    # Also append to a simple log file
    with open("model_events.jsonl", "a") as f:
        f.write(json.dumps(event) + '\n')

def update_v2_results(eval_entry: dict) -> None:
    """Update the v2_results.jsonl file with completed eval results"""
    v2_results_path = "results/v2_results.jsonl"
    
    if not os.path.exists(v2_results_path):
        print(f"⚠️ v2_results.jsonl not found at {v2_results_path}")
        return
    
    # Read all entries from v2_results.jsonl
    entries = []
    with open(v2_results_path, 'r') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line.strip()))
    
    # Find and update the matching entry
    updated = False
    for entry in entries:
        if (entry.get("question_id") == eval_entry.get("question_id") and 
            entry.get("model") == eval_entry.get("model")):
            # Update the empty fields with our results
            entry["answer"] = eval_entry.get("answer", "")
            entry["tools_called"] = [tool["tool"] for tool in eval_entry.get("rowan_tools_used", [])]
            entry["correctness"] = eval_entry.get("correctness")
            entry["notes"] = eval_entry.get("notes", "")
            updated = True
            print(f"✅ Updated v2_results.jsonl entry for {entry['question_id']} - {entry['model']}")
            break
    
    if not updated:
        print(f"⚠️ No matching entry found in v2_results.jsonl for {eval_entry.get('question_id')} - {eval_entry.get('model')}")
        return
    
    # Write back to file
    with open(v2_results_path, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

@mcp.tool()
def start_eval_session(question_id: str, model: str, question: str) -> str:
    """Start a new evaluation session"""
    global active_sessions
    
    # Check if this is a restart (session already existed for this model+question)
    is_restart = any(event.get("event_type") == "session_start" and 
                    event.get("model") == model and 
                    event.get("question_id") == question_id 
                    for event in model_events)
    
    # Log session start event
    log_event("session_start", model, question_id, {
        "is_restart": is_restart,
        "question_text": question[:100] + "..." if len(question) > 100 else question
    })
    
    session_data = {
        "question_id": question_id,
        "question": question,
        "model": model,
        "session_start": datetime.now().isoformat(),
        "tools_called": [],
        "answer_text": "",
        "rowan_tools_used": []
    }
    
    active_sessions[model] = session_data
    
    restart_msg = " (RESTART)" if is_restart else ""
    print(f"🔬 Started eval session{restart_msg}: {question_id} - {model}")
    return f"Started eval session for {question_id} with model {model}{restart_msg}"

@mcp.tool()
def log_rowan_tool_call(tool_name: str, model: str = None) -> str:
    """Log that a Rowan chemistry tool was called"""
    global active_sessions
    
    # Try to determine model from active sessions if not provided
    if not model:
        if len(active_sessions) == 1:
            model = list(active_sessions.keys())[0]
        else:
            return "Error: Multiple active sessions, please specify model parameter"
    
    if model not in active_sessions:
        return f"Error: No active session for model {model}"
    
    tool_call_info = {
        "tool": tool_name,
        "timestamp": datetime.now().isoformat()
    }
    
    active_sessions[model]["rowan_tools_used"].append(tool_call_info)
    print(f"🔧 Logged Rowan tool: {tool_name} for {model}")
    return f"Logged tool call: {tool_name} for {model}"

@mcp.tool()
def end_eval_session(answer_text: str, model: str = None) -> str:
    """End the evaluation session for a specific model"""
    global active_sessions
    
    # Try to determine model from active sessions if not provided
    if not model:
        if len(active_sessions) == 1:
            model = list(active_sessions.keys())[0]
        else:
            return "Error: Multiple active sessions, please specify model parameter"
    
    if model not in active_sessions:
        return f"Error: No active session for model {model}"
    
    session = active_sessions[model]
    session["answer_text"] = answer_text
    session["session_end"] = datetime.now().isoformat()
    
    # Auto-detect Rowan tools from answer text if not manually logged
    if len(session.get("rowan_tools_used", [])) == 0:
        rowan_tools = [
            "rowan_conformers", "rowan_pka", "rowan_solubility", "rowan_tautomers",
            "rowan_admet", "rowan_descriptors", "rowan_redox_potential", "rowan_fukui",
            "rowan_multistage_opt", "rowan_electronic_properties", "rowan_spin_states",
            "rowan_molecular_dynamics", "rowan_scan", "rowan_irc", "rowan_docking",
            "rowan_molecule_lookup", "rowan_workflow_management"
        ]
        detected_tools = []
        for tool in rowan_tools:
            if tool in answer_text.lower() or tool.replace("rowan_", "mcp_rowan_") in answer_text.lower():
                detected_tools.append({
                    "tool": tool,
                    "timestamp": datetime.now().isoformat()
                })
        session["rowan_tools_used"] = detected_tools
        if detected_tools:
            print(f"🔍 Auto-detected {len(detected_tools)} Rowan tools for {model}")
    
    # Calculate time elapsed
    start_time = datetime.fromisoformat(session.get("session_start"))
    end_time = datetime.fromisoformat(session.get("session_end"))
    time_elapsed = (end_time - start_time).total_seconds()
    
    # Save to JSONL file
    eval_log_path = "rowan_eval_results.jsonl"
    
    eval_entry = {
        "question_id": session.get("question_id"),
        "question": session.get("question"),
        "model": session.get("model"),
        "answer": session.get("answer_text"),
        "rowan_tools_used": session.get("rowan_tools_used", []),
        "num_tools_called": len(session.get("rowan_tools_used", [])),
        "session_start": session.get("session_start"),
        "session_end": session.get("session_end"),
        "time_elapsed_seconds": round(time_elapsed, 2),
        "correctness": None,
        "notes": ""
    }
    
    # Append to JSONL file
    with open(eval_log_path, "a") as f:
        f.write(json.dumps(eval_entry) + "\n")
    
    # Log successful completion
    start_time = datetime.fromisoformat(session.get("session_start"))
    end_time = datetime.fromisoformat(session.get("session_end"))
    duration = (end_time - start_time).total_seconds()
    
    log_event("session_complete", model, session.get("question_id"), {
        "duration_seconds": round(duration, 1),
        "tools_used": len(session.get("rowan_tools_used", [])),
        "answer_length": len(answer_text)
    })
    
    # Update v2_results.jsonl if it exists
    update_v2_results(eval_entry)
    
    print(f"📊 Logged eval result for {eval_entry['question_id']} - {eval_entry['model']}")
    print(f"    Tools used: {[tool['tool'] for tool in eval_entry['rowan_tools_used']]}")
    
    result = f"Logged eval for {session['question_id']} - {session['model']}"
    
    # Remove completed session
    del active_sessions[model]
    
    return result

@mcp.tool()
def log_connection_failure(model: str, reason: str = "Connection timeout or server not found") -> str:
    """Log when a model has connection failures"""
    # Get the current question_id from active session if available
    question_id = None
    if model in active_sessions:
        question_id = active_sessions[model].get("question_id")
    
    log_event("connection_failure", model, question_id, {"reason": reason})
    print(f"❌ Connection failure logged for {model}: {reason}")
    return f"Logged connection failure for {model}: {reason}"

@mcp.tool() 
def log_tool_failure(model: str, tool_name: str, reason: str = "Tool call failed") -> str:
    """Log when a Rowan tool call fails"""
    # Get the current question_id from active session
    question_id = None
    if model in active_sessions:
        question_id = active_sessions[model].get("question_id")
    
    log_event("tool_failure", model, question_id, {
        "tool_name": tool_name,
        "reason": reason
    })
    print(f"❌ Tool failure logged for {model}: {tool_name} - {reason}")
    return f"Logged tool failure for {model}: {tool_name}"

@mcp.tool()
def get_event_log(model: str = None, event_type: str = None) -> list:
    """Get logged events, optionally filtered by model and/or event type"""
    events = model_events
    
    if model:
        events = [e for e in events if e.get("model") == model]
    
    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]
    
    return events[-50:]  # Return last 50 events

@mcp.tool()
def get_current_session_status() -> dict:
    """Get current session status for debugging"""
    global active_sessions
    return {
        "active_sessions": len(active_sessions),
        "sessions": {
            model: {
                "question_id": session.get("question_id"),
                "tools_called_so_far": len(session.get("rowan_tools_used", []))
            } for model, session in active_sessions.items()
        }
    }

@mcp.tool()
def auto_end_session_with_timeout(timeout_minutes: int = 30) -> str:
    """Auto-end session after timeout with placeholder answer"""
    global current_session
    
    if not current_session.get("question_id"):
        return "No active session to auto-end"
    
    # Check if session has exceeded timeout
    start_time = datetime.fromisoformat(current_session.get("session_start"))
    elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
    
    if elapsed_minutes >= timeout_minutes:
        auto_answer = f"[AUTO-ENDED: Session exceeded {timeout_minutes} minutes. Tools used: {[tool['tool'] for tool in current_session.get('rowan_tools_used', [])]}]"
        return end_eval_session(auto_answer)
    
    return f"Session still active ({elapsed_minutes:.1f}/{timeout_minutes} min)"

def main() -> None:
    """Main entry point for the eval tracker MCP server."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Eval Tracker MCP Server")
        print("Usage: python eval_tracker_server.py")
        print("Environment variables:")
        print("  EVAL_MCP_HOST   # Optional: HTTP host (default: 127.0.0.1)")
        print("  EVAL_MCP_PORT   # Optional: HTTP port (default: 6277)")
        return
    
    host = os.getenv("EVAL_MCP_HOST", "127.0.0.1")
    port = int(os.getenv("EVAL_MCP_PORT", "6277"))
    
    # Debug: print registered tools
    print(f"Registered tools: {list(mcp._tools.keys()) if hasattr(mcp, '_tools') else 'Unknown'}")
    print(f"Starting Eval Tracker MCP Server at http://{host}:{port}/sse")
    
    mcp.run(transport="sse", host=host, port=port)

if __name__ == "__main__":
    main()