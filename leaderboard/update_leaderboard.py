#!/usr/bin/env python3
"""
Simple Local Leaderboard Generator
Creates and updates CSV leaderboards from evaluation data
"""

import json
import os
import glob
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import statistics

class SimpleLeaderboardGenerator:
    """Generates CSV leaderboards from evaluation data"""

    def __init__(self, evaluations_dir: str = "evaluations", output_dir: str = "."):
        self.evaluations_dir = Path(evaluations_dir)
        self.output_dir = Path(output_dir)
        self.scores = []

    def extract_model_name(self, filename: str) -> str:
        """Extract clean model name from evaluation filename"""
        name = filename.replace("_evaluation.json", "").replace("_evaluation", "")

        # Remove timestamps
        import re
        name = re.sub(r'_\d{8}_\d{6}', '', name)
        name = re.sub(r'_\d+$', '', name)

        # Clean up provider/model format
        if "_" in name:
            parts = name.split("_")
            if len(parts) >= 2:
                provider = parts[0]
                model = "_".join(parts[1:])
                model = model.replace(":free", "").replace("_free", "")
                return f"{provider}/{model}"

        return name

    def parse_evaluation_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Parse a single evaluation file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            filename = os.path.basename(file_path)
            model_name = self.extract_model_name(filename)

            # Determine format and extract data
            if "completion_score" in data and "correctness_score" in data:
                # LLM Judge format
                return {
                    'model': model_name,
                    'question_id': data.get("question_id", ""),
                    'tier': data.get("question_id", "").split("_")[0] if "_" in data.get("question_id", "") else "",
                    'total_score': float(data.get("total_score", 0)),
                    'max_score': 6.0,
                    'normalized_score': (float(data.get("total_score", 0)) / 6.0) * 100,
                    'completion_score': float(data.get("completion_score", 0)),
                    'correctness_score': float(data.get("correctness_score", 0)),
                    'tool_use_score': float(data.get("tool_use_score", 0)),
                    'assessment': data.get("overall_assessment", ""),
                    'timestamp': data.get("evaluation_timestamp", ""),
                    'format': 'llm_judge',
                    'file_path': file_path
                }
            elif "overall_score" in data:
                # Legacy format
                return {
                    'model': model_name,
                    'question_id': data.get("question_id", ""),
                    'tier': data.get("question_id", "").split("_")[0] if "_" in data.get("question_id", "") else "",
                    'total_score': float(data.get("overall_score", 0)),
                    'max_score': 1.0,
                    'normalized_score': float(data.get("overall_score", 0)) * 100,
                    'completion_score': None,
                    'correctness_score': None,
                    'tool_use_score': None,
                    'assessment': "",
                    'timestamp': data.get("evaluation_timestamp", ""),
                    'format': 'legacy',
                    'file_path': file_path
                }
            else:
                print(f"Unknown format in {file_path}")
                return None

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    def scan_evaluations(self) -> List[Dict[str, Any]]:
        """Scan all evaluation files and extract data"""
        scores = []

        # Find all JSON files in tier directories
        for tier_dir in self.evaluations_dir.glob("tier*"):
            if tier_dir.is_dir():
                json_dir = tier_dir / "json"
                if json_dir.exists() and "archive" not in str(json_dir).lower():
                    for json_file in json_dir.glob("*.json"):
                        score_data = self.parse_evaluation_file(str(json_file))
                        if score_data:
                            scores.append(score_data)

        return scores

    def generate_overall_leaderboard_csv(self, scores: List[Dict[str, Any]]):
        """Generate overall model leaderboard CSV"""
        model_stats = defaultdict(list)

        # Group by model
        for score in scores:
            model_stats[score['model']].append(score)

        # Calculate aggregated stats
        leaderboard_data = []
        for model, model_scores in model_stats.items():
            normalized_scores = [s['normalized_score'] for s in model_scores]
            pass_count = sum(1 for s in model_scores if s['assessment'] == 'pass')

            tier_counts = defaultdict(int)
            for s in model_scores:
                tier_counts[s['tier']] += 1

            leaderboard_data.append({
                'rank': 0,  # Will be set after sorting
                'model': model,
                'avg_score': round(statistics.mean(normalized_scores), 1),
                'median_score': round(statistics.median(normalized_scores), 1),
                'total_evaluations': len(model_scores),
                'pass_rate': round((pass_count / len(model_scores)) * 100, 1) if model_scores else 0,
                'tier1_count': tier_counts.get('tier1', 0),
                'tier2_count': tier_counts.get('tier2', 0),
                'tier3_count': tier_counts.get('tier3', 0),
                'last_evaluation': max(s['timestamp'] for s in model_scores) if model_scores else ""
            })

        # Sort by average score
        leaderboard_data.sort(key=lambda x: x['avg_score'], reverse=True)

        # Set ranks
        for i, entry in enumerate(leaderboard_data, 1):
            entry['rank'] = i

        # Write CSV
        csv_path = self.output_dir / "leaderboard_overall.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'rank', 'model', 'avg_score', 'median_score', 'total_evaluations',
                'pass_rate', 'tier1_count', 'tier2_count', 'tier3_count', 'last_evaluation'
            ])
            writer.writeheader()
            writer.writerows(leaderboard_data)

        print(f"✅ Overall leaderboard saved to: {csv_path}")
        return leaderboard_data

    def generate_tier_leaderboards_csv(self, scores: List[Dict[str, Any]]):
        """Generate tier-specific leaderboard CSVs"""
        tiers = set(s['tier'] for s in scores if s['tier'])

        for tier in sorted(tiers):
            tier_scores = [s for s in scores if s['tier'] == tier]
            model_stats = defaultdict(list)

            # Group by model for this tier
            for score in tier_scores:
                model_stats[score['model']].append(score)

            # Calculate stats for this tier
            tier_data = []
            for model, model_scores in model_stats.items():
                normalized_scores = [s['normalized_score'] for s in model_scores]
                pass_count = sum(1 for s in model_scores if s['assessment'] == 'pass')

                tier_data.append({
                    'rank': 0,
                    'model': model,
                    'avg_score': round(statistics.mean(normalized_scores), 1),
                    'total_evaluations': len(model_scores),
                    'pass_rate': round((pass_count / len(model_scores)) * 100, 1) if model_scores else 0,
                    'question_ids': ', '.join(sorted(set(s['question_id'] for s in model_scores))),
                    'last_evaluation': max(s['timestamp'] for s in model_scores) if model_scores else ""
                })

            # Sort and rank
            tier_data.sort(key=lambda x: x['avg_score'], reverse=True)
            for i, entry in enumerate(tier_data, 1):
                entry['rank'] = i

            # Write tier CSV
            csv_path = self.output_dir / f"leaderboard_{tier}.csv"
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'rank', 'model', 'avg_score', 'total_evaluations',
                    'pass_rate', 'question_ids', 'last_evaluation'
                ])
                writer.writeheader()
                writer.writerows(tier_data)

            print(f"✅ {tier.upper()} leaderboard saved to: {csv_path}")

    def generate_detailed_results_csv(self, scores: List[Dict[str, Any]]):
        """Generate detailed results CSV with all individual scores"""
        csv_path = self.output_dir / "evaluation_results_detailed.csv"

        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'model', 'question_id', 'tier', 'normalized_score', 'total_score', 'max_score',
                'completion_score', 'correctness_score', 'tool_use_score', 'assessment',
                'timestamp', 'format', 'file_path'
            ])
            writer.writeheader()

            # Sort by model, then tier, then question_id
            sorted_scores = sorted(scores, key=lambda x: (x['model'], x['tier'], x['question_id']))
            writer.writerows(sorted_scores)

        print(f"✅ Detailed results saved to: {csv_path}")

    def generate_summary_stats(self, scores: List[Dict[str, Any]]):
        """Generate summary statistics file"""
        if not scores:
            return

        unique_models = len(set(s['model'] for s in scores))
        unique_tiers = len(set(s['tier'] for s in scores if s['tier']))
        normalized_scores = [s['normalized_score'] for s in scores]

        tier_counts = defaultdict(int)
        format_counts = defaultdict(int)
        for s in scores:
            tier_counts[s['tier']] += 1
            format_counts[s['format']] += 1

        stats = {
            'total_evaluations': len(scores),
            'unique_models': unique_models,
            'unique_tiers': unique_tiers,
            'avg_score': round(statistics.mean(normalized_scores), 1),
            'median_score': round(statistics.median(normalized_scores), 1),
            'min_score': round(min(normalized_scores), 1),
            'max_score': round(max(normalized_scores), 1),
            'last_updated': datetime.now().isoformat(),
            **{f'{tier}_count': count for tier, count in tier_counts.items()},
            **{f'{fmt}_format_count': count for fmt, count in format_counts.items()}
        }

        # Write stats CSV
        csv_path = self.output_dir / "leaderboard_stats.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=stats.keys())
            writer.writeheader()
            writer.writerow(stats)

        print(f"✅ Summary statistics saved to: {csv_path}")

        # Also print summary
        print(f"\n📊 Summary: {stats['total_evaluations']} evaluations, {stats['unique_models']} models, avg {stats['avg_score']}%")

    def update_leaderboards(self):
        """Main function to update all leaderboard files"""
        print("🔍 Scanning evaluation files...")
        scores = self.scan_evaluations()

        if not scores:
            print("❌ No evaluation data found!")
            return

        print(f"📊 Found {len(scores)} evaluation results")

        # Generate all leaderboard files
        print("\n📝 Generating leaderboard files...")
        self.generate_overall_leaderboard_csv(scores)
        self.generate_tier_leaderboards_csv(scores)
        self.generate_detailed_results_csv(scores)
        self.generate_summary_stats(scores)

        print(f"\n✅ All leaderboard files updated!")
        print(f"📁 Files saved in: {self.output_dir}")

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Update LabAgents v2 Leaderboards")
    parser.add_argument("--evaluations-dir", default="evaluations", help="Evaluations directory")
    parser.add_argument("--output-dir", default=".", help="Output directory for CSV files")

    args = parser.parse_args()

    generator = SimpleLeaderboardGenerator(args.evaluations_dir, args.output_dir)
    generator.update_leaderboards()

if __name__ == "__main__":
    main()