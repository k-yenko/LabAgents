#!/usr/bin/env python3
"""
Quick Leaderboard Viewer
View CSV leaderboard data in terminal
"""

import csv
import sys
from pathlib import Path

def print_csv_table(csv_path: str, title: str, limit: int = None):
    """Print a CSV file as a formatted table"""
    if not Path(csv_path).exists():
        print(f"❌ {csv_path} not found. Run 'python update_leaderboard.py' first.")
        return

    print(f"\n{title}")
    print("=" * len(title))

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

        if not rows:
            print("No data found.")
            return

        if limit:
            rows = rows[:limit]

        # Get column widths
        headers = list(rows[0].keys())
        widths = {}
        for header in headers:
            widths[header] = max(len(header), max(len(str(row[header])) for row in rows))

        # Print header
        header_line = " | ".join(header.ljust(widths[header]) for header in headers)
        print(header_line)
        print("-" * len(header_line))

        # Print rows
        for row in rows:
            row_line = " | ".join(str(row[header]).ljust(widths[header]) for header in headers)
            print(row_line)

def print_stats():
    """Print summary statistics"""
    stats_path = "leaderboard_stats.csv"
    if not Path(stats_path).exists():
        print("❌ Stats file not found. Run 'python update_leaderboard.py' first.")
        return

    with open(stats_path, 'r') as f:
        reader = csv.DictReader(f)
        stats = next(reader)

    print("📊 SUMMARY STATISTICS")
    print("=" * 30)
    print(f"Total Evaluations: {stats['total_evaluations']}")
    print(f"Unique Models: {stats['unique_models']}")
    print(f"Average Score: {stats['avg_score']}%")
    print(f"Median Score: {stats['median_score']}%")
    print(f"Score Range: {stats['min_score']}% - {stats['max_score']}%")
    print(f"Last Updated: {stats['last_updated'][:19].replace('T', ' ')}")

    print(f"\nTier Distribution:")
    for key, value in stats.items():
        if key.startswith('tier') and key.endswith('_count'):
            tier = key.replace('_count', '')
            print(f"  {tier}: {value} evaluations")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("🧪 LabAgents v2 Quick Leaderboard Viewer")
        print("\nUsage:")
        print("  python quick_leaderboard.py overall    # Overall leaderboard")
        print("  python quick_leaderboard.py tier1      # Tier 1 leaderboard")
        print("  python quick_leaderboard.py tier2      # Tier 2 leaderboard")
        print("  python quick_leaderboard.py tier3      # Tier 3 leaderboard")
        print("  python quick_leaderboard.py stats      # Summary statistics")
        print("  python quick_leaderboard.py all        # Show everything")
        print("\nFirst run: python update_leaderboard.py")
        return

    command = sys.argv[1].lower()
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None

    if command == "stats":
        print_stats()

    elif command == "overall":
        print_csv_table("leaderboard_overall.csv", "🏆 OVERALL LEADERBOARD", limit)

    elif command == "tier1":
        print_csv_table("leaderboard_tier1.csv", "🎯 TIER 1 LEADERBOARD", limit)

    elif command == "tier2":
        print_csv_table("leaderboard_tier2.csv", "🎯 TIER 2 LEADERBOARD", limit)

    elif command == "tier3":
        print_csv_table("leaderboard_tier3.csv", "🎯 TIER 3 LEADERBOARD", limit)

    elif command == "all":
        print_stats()
        print_csv_table("leaderboard_overall.csv", "🏆 OVERALL LEADERBOARD", limit)
        print_csv_table("leaderboard_tier1.csv", "🎯 TIER 1 LEADERBOARD", limit)
        print_csv_table("leaderboard_tier2.csv", "🎯 TIER 2 LEADERBOARD", limit)
        print_csv_table("leaderboard_tier3.csv", "🎯 TIER 3 LEADERBOARD", limit)

    else:
        print(f"❌ Unknown command: {command}")
        print("Available: overall, tier1, tier2, tier3, stats, all")

if __name__ == "__main__":
    main()