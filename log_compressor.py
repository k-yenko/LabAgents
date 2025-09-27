#!/usr/bin/env python3
"""
Log Compression Script for LabAgents Evaluation Framework

Compresses existing log files by:
1. Removing null fields
2. Consolidating workflow polling sequences
3. Compressing repeated error patterns

Usage:
    python log_compressor.py logs/tier1_001/model_name/log_file.json
    python log_compressor.py logs/tier1_001/  # compress all logs in directory
"""

import json
import os
import sys
import glob
import argparse
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional


def remove_null_fields(obj: Any) -> Any:
    """Recursively remove null/None fields from dictionaries and lists."""
    if isinstance(obj, dict):
        return {k: remove_null_fields(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, list):
        return [remove_null_fields(item) for item in obj]
    else:
        return obj


def consolidate_workflow_polling(timeline: List[Dict]) -> List[Dict]:
    """Consolidate repeated workflow_get_status calls into summary objects."""

    # First pass: identify all workflow polling tool calls and mark them
    workflow_polls = {}  # workflow_id -> list of (index, event) tuples

    for i, event in enumerate(timeline):
        if (event and event.get("event_type") == "tool_call" and
            event.get("tool_name") == "workflow_get_status"):

            # Try both workflow_id and workflow_uuid parameter names
            params = event.get("parameters", {})
            workflow_id = params.get("workflow_id") or params.get("workflow_uuid")

            if workflow_id:
                if workflow_id not in workflow_polls:
                    workflow_polls[workflow_id] = []
                workflow_polls[workflow_id].append((i, event))

    # Second pass: create compressed timeline
    compressed_timeline = []
    skip_indices = set()

    for workflow_id, polls in workflow_polls.items():
        if len(polls) > 2:  # Only consolidate if 3+ polls
            # Mark all these indices to be skipped
            for poll_idx, _ in polls:
                skip_indices.add(poll_idx)

            # Create consolidated event
            first_poll = polls[0][1]
            last_poll = polls[-1][1]

            # Extract status progression
            status_progression = []
            for _, poll in polls:
                result = poll.get("result")
                if isinstance(result, str):
                    try:
                        result_dict = json.loads(result)
                        if "status_description" in result_dict:
                            status_progression.append(result_dict["status_description"])
                        elif "status" in result_dict:
                            status_progression.append(result_dict["status"])
                    except:
                        status_progression.append("unknown")

            # Calculate timing
            first_timestamp = first_poll.get("timestamp")
            last_timestamp = last_poll.get("timestamp")
            duration_seconds = None

            if first_timestamp and last_timestamp:
                try:
                    start = datetime.fromisoformat(first_timestamp.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
                    duration_seconds = (end - start).total_seconds()
                except:
                    pass

            # Create consolidated polling summary
            consolidated_event = {
                "timestamp": first_poll.get("timestamp"),
                "event_type": "workflow_polling_sequence",
                "workflow_id": workflow_id,
                "polling_summary": {
                    "total_polls": len(polls),
                    "duration_seconds": duration_seconds,
                    "status_progression": status_progression,
                    "final_status": status_progression[-1] if status_progression else None,
                    "final_result": last_poll.get("result")
                },
                "success": last_poll.get("success"),
                "execution_time_ms": sum(p.get("execution_time_ms", 0) for _, p in polls if p.get("execution_time_ms"))
            }

            # Add at the position of the first poll
            compressed_timeline.append((polls[0][0], consolidated_event))

    # Third pass: build final timeline, skipping consolidated events
    final_timeline = []
    for i, event in enumerate(timeline):
        if i not in skip_indices:
            final_timeline.append(event)
        else:
            # Check if this is the first poll in a sequence we consolidated
            for pos, consolidated in compressed_timeline:
                if i == pos:
                    final_timeline.append(consolidated)
                    break

    return final_timeline


def compress_repeated_errors(timeline: List[Dict]) -> List[Dict]:
    """Compress sequences of repeated error patterns."""
    compressed_timeline = []
    i = 0

    while i < len(timeline):
        event = timeline[i]

        # Check if this event has an error
        if event.get("success") is False and event.get("error_message"):
            error_message = event.get("error_message")
            tool_name = event.get("tool_name")

            # Look for consecutive similar errors
            error_sequence = [event]
            j = i + 1

            while j < len(timeline):
                next_event = timeline[j]
                if (next_event.get("success") is False and
                    next_event.get("error_message") == error_message and
                    next_event.get("tool_name") == tool_name):
                    error_sequence.append(next_event)
                    j += 1
                else:
                    break

            # If we found multiple consecutive similar errors, consolidate them
            if len(error_sequence) > 2:  # Only consolidate if 3+ similar errors
                first_error = error_sequence[0]
                last_error = error_sequence[-1]

                # Check if the sequence eventually succeeded
                resolution = "continued_failure"
                if j < len(timeline):
                    next_event = timeline[j]
                    if (next_event.get("tool_name") == tool_name and
                        next_event.get("success") is True):
                        resolution = "eventual_success"

                consolidated_error = {
                    "timestamp": first_error.get("timestamp"),
                    "event_type": "error_sequence",
                    "tool_name": tool_name,
                    "error_summary": {
                        "error_message": error_message,
                        "occurrences": len(error_sequence),
                        "resolution": resolution,
                        "total_execution_time_ms": sum(e.get("execution_time_ms", 0) for e in error_sequence if e.get("execution_time_ms"))
                    },
                    "success": False
                }

                compressed_timeline.append(consolidated_error)
                i = j  # Skip all the error events we just consolidated
            else:
                # Keep individual errors if sequence is short
                for error in error_sequence:
                    compressed_timeline.append(error)
                i = j
        else:
            compressed_timeline.append(event)
            i += 1

    return compressed_timeline


def compress_log_file(log_data: Dict) -> Dict:
    """Apply all compression techniques to a log file."""
    # Start with a copy of the original data
    compressed_data = log_data.copy()

    # Get the execution timeline
    timeline = compressed_data.get("execution_timeline", [])

    if not timeline:
        # If no timeline, just remove null fields
        return remove_null_fields(compressed_data)

    print(f"  Original timeline events: {len(timeline)}")

    # Apply compression steps
    timeline = consolidate_workflow_polling(timeline)
    print(f"  After workflow consolidation: {len(timeline)}")

    timeline = compress_repeated_errors(timeline)
    print(f"  After error compression: {len(timeline)}")

    # Update the timeline
    compressed_data["execution_timeline"] = timeline

    # Remove null fields from the entire structure
    compressed_data = remove_null_fields(compressed_data)

    # Add compression metadata
    compressed_data["compression_metadata"] = {
        "compressed_at": datetime.now().isoformat(),
        "original_timeline_length": len(log_data.get("execution_timeline", [])),
        "compressed_timeline_length": len(timeline),
        "compression_ratio": round(len(timeline) / len(log_data.get("execution_timeline", [])), 3) if log_data.get("execution_timeline") else 1.0
    }

    return compressed_data


def compress_single_file(input_path: str, output_path: Optional[str] = None) -> None:
    """Compress a single log file."""
    if not output_path:
        # Create output filename by adding _compressed suffix
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_compressed{ext}"

    print(f"Compressing: {input_path}")

    try:
        with open(input_path, 'r') as f:
            log_data = json.load(f)

        compressed_data = compress_log_file(log_data)

        with open(output_path, 'w') as f:
            json.dump(compressed_data, f, indent=2)

        original_size = os.path.getsize(input_path)
        compressed_size = os.path.getsize(output_path)
        size_reduction = round((1 - compressed_size / original_size) * 100, 1)

        print(f"  Output: {output_path}")
        print(f"  Size reduction: {size_reduction}% ({original_size:,} → {compressed_size:,} bytes)")
        print(f"  Timeline compression: {compressed_data['compression_metadata']['compression_ratio']:.3f}")

    except Exception as e:
        print(f"  Error: {e}")


def compress_directory(directory_path: str) -> None:
    """Compress all JSON log files in a directory."""
    pattern = os.path.join(directory_path, "**", "*.json")
    log_files = glob.glob(pattern, recursive=True)

    # Filter out already compressed files
    log_files = [f for f in log_files if not f.endswith("_compressed.json")]

    if not log_files:
        print(f"No log files found in {directory_path}")
        return

    print(f"Found {len(log_files)} log files to compress")

    for log_file in log_files:
        compress_single_file(log_file)
        print()


def main():
    parser = argparse.ArgumentParser(description="Compress LabAgents log files")
    parser.add_argument("path", help="Path to log file or directory to compress")
    parser.add_argument("-o", "--output", help="Output file path (for single file compression)")

    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"Error: Path {args.path} does not exist")
        sys.exit(1)

    if os.path.isfile(args.path):
        compress_single_file(args.path, args.output)
    elif os.path.isdir(args.path):
        if args.output:
            print("Warning: --output ignored when compressing directory")
        compress_directory(args.path)
    else:
        print(f"Error: {args.path} is neither a file nor directory")
        sys.exit(1)


if __name__ == "__main__":
    main()