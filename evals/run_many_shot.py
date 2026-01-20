#!/usr/bin/env python3
"""
Run many-shot jailbreaking experiments.

Usage:
    uv run evals/run_many_shot.py --provider claude
    uv run evals/run_many_shot.py --provider openai --model gpt-4o
    uv run evals/run_many_shot.py --provider claude --shots 0,4,16,64

"""

import argparse
import os
import sys

from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evals.many_shot.models import get_model
from evals.many_shot.runner import run_experiment_sweep, compute_stats, save_results


def main():
    parser = argparse.ArgumentParser(description="Run many-shot jailbreaking experiments")
    parser.add_argument(
        "--provider",
        type=str,
        required=True,
        choices=["claude", "openai", "gemini"],
        help="Model provider to use"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Specific model ID (uses provider default if not specified)"
    )
    parser.add_argument(
        "--shots",
        type=str,
        default="0,4,8,16,32,64",
        help="Comma-separated list of shot counts to test"
    )
    parser.add_argument(
        "--categories",
        type=str,
        default=None,
        help="Comma-separated list of categories (violence,illegal,deception,regulated,discrimination)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evals/results",
        help="Directory to save results"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output"
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Parse shot counts
    shot_counts = [int(x.strip()) for x in args.shots.split(",")]

    # Parse categories
    categories = None
    if args.categories:
        categories = [x.strip() for x in args.categories.split(",")]

    # Get model
    print(f"Loading model: {args.provider}" + (f":{args.model}" if args.model else ""))
    model = get_model(args.provider, args.model)

    # Run experiments
    print(f"\nRunning experiments with shot counts: {shot_counts}")
    if categories:
        print(f"Categories: {categories}")
    print("-" * 50)

    results = run_experiment_sweep(
        model=model,
        shot_counts=shot_counts,
        categories=categories,
        verbose=not args.quiet,
    )

    # Compute and display stats
    stats = compute_stats(results)

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    print("\nJailbreak rate by shot count:")
    for shots in sorted(stats["by_shots"].keys()):
        data = stats["by_shots"][shots]
        rate_pct = data["rate"] * 100
        print(f"  {shots:3d} shots: {data['jailbreaks']:2d}/{data['total']:2d} ({rate_pct:5.1f}%)")

    print("\nJailbreak rate by category:")
    for cat, data in stats["by_category"].items():
        rate_pct = data["rate"] * 100
        print(f"  {cat:15s}: {data['jailbreaks']:2d}/{data['total']:2d} ({rate_pct:5.1f}%)")

    # Save results
    save_results(results, stats, args.output_dir)


if __name__ == "__main__":
    main()
