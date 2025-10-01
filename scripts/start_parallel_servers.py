#!/usr/bin/env python3
"""
Start multiple eval tracker servers for parallel model evaluation
Each model gets its own server instance to avoid session conflicts
"""
import subprocess
import time
import os
import signal
import sys

# Model to port mapping
MODEL_SERVERS = {
    "claude-4.1-opus": 6277,
    "claude-4-sonnet": 6278,
    "gpt-5": 6279,
    "o3": 6280,
    "grok-4": 6281,
    "gemini-2.5-pro": 6282,
    "deepseek-v3.1": 6283,
    "grok-code-fast-1": 6284
}

servers = []

def cleanup_servers():
    """Kill all server processes"""
    print("🛑 Shutting down all eval servers...")
    for proc in servers:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

def signal_handler(signum, frame):
    cleanup_servers()
    sys.exit(0)

def main():
    # Set up signal handlers for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Starting parallel eval tracker servers...")
    print("Each model will have its own server instance to avoid conflicts.\n")
    
    # Start servers for each model
    for model, port in MODEL_SERVERS.items():
        print(f"📡 Starting server for {model} on port {port}...")
        
        env = os.environ.copy()
        env["EVAL_MCP_PORT"] = str(port)
        
        proc = subprocess.Popen([
            "python3", "eval_tracker_server.py"
        ], env=env, cwd=".", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        servers.append(proc)
        time.sleep(1)  # Stagger startup
    
    print(f"\n✅ Started {len(servers)} eval servers!")
    print("\n📋 Server Mapping:")
    for model, port in MODEL_SERVERS.items():
        print(f"  • {model:<20} → http://127.0.0.1:{port}/sse")
    
    print(f"\n💡 Usage:")
    print(f"  1. Open {len(MODEL_SERVERS)} Claude Code workspaces")
    print(f"  2. In each workspace, connect to different MCP server port")
    print(f"  3. Run eval commands with appropriate model name")
    print(f"  4. Press Ctrl+C to stop all servers")
    
    try:
        # Keep main process alive
        while True:
            time.sleep(1)
            # Check if any server died
            for i, proc in enumerate(servers):
                if proc.poll() is not None:
                    model = list(MODEL_SERVERS.keys())[i]
                    print(f"⚠️  Server for {model} died, restarting...")
                    # Restart the server
                    env = os.environ.copy()
                    env["EVAL_MCP_PORT"] = str(MODEL_SERVERS[model])
                    servers[i] = subprocess.Popen([
                        "python3", "eval_tracker_server.py"
                    ], env=env, cwd=".")
    except KeyboardInterrupt:
        cleanup_servers()

if __name__ == "__main__":
    main()