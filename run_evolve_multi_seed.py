#!/usr/bin/env python3
"""
Run OpenEvolve with multiple initial seed programs from a directory.

This script loads all Python files from a seeds directory and adds them to
the evolution database before running evolution. This allows you to start
evolution from multiple diverse starting points.
"""
import argparse
import asyncio
import glob
import logging
import os
import sys
import uuid
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openevolve import OpenEvolve
from openevolve.config import load_config
from openevolve.database import Program


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run OpenEvolve with multiple initial seed programs"
    )

    parser.add_argument(
        "seeds_dir",
        help="Directory containing initial seed programs (all .py files will be loaded)"
    )

    parser.add_argument(
        "evaluation_file",
        help="Path to the evaluation file containing an 'evaluate' function"
    )

    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file (YAML)",
        default=None
    )

    parser.add_argument(
        "--iterations", "-i",
        help="Maximum number of iterations",
        type=int,
        default=None
    )

    parser.add_argument(
        "--target-score", "-t",
        help="Target score to reach",
        type=float,
        default=None
    )

    parser.add_argument(
        "--output", "-o",
        help="Output directory for results",
        default=None
    )

    parser.add_argument(
        "--log-level",
        help="Logging level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None
    )

    parser.add_argument(
        "--distribute-across-islands",
        help="Distribute initial seeds across different islands (if using island-based evolution)",
        action="store_true"
    )

    parser.add_argument(
        "--first-seed-only",
        help="Only use the first seed found (alphabetically)",
        action="store_true"
    )

    return parser.parse_args()


def load_seed_files(seeds_dir):
    """
    Load all Python files from the seeds directory.

    Args:
        seeds_dir: Path to directory containing seed files

    Returns:
        List of tuples (filepath, basename) for all .py files
    """
    seeds_path = Path(seeds_dir)

    if not seeds_path.exists():
        print(f"Error: Seeds directory '{seeds_dir}' not found")
        sys.exit(1)

    # Find all .py files in the directory
    seed_files = sorted(seeds_path.glob("*.py"))

    if not seed_files:
        print(f"Error: No .py files found in '{seeds_dir}'")
        sys.exit(1)

    print(f"Found {len(seed_files)} seed program(s) in '{seeds_dir}':")
    for i, seed_file in enumerate(seed_files):
        print(f"  {i+1}. {seed_file.name}")

    return seed_files


async def add_seed_programs(controller, seed_files, first_seed_only=False, distribute_across_islands=False):
    """
    Add all seed programs to the database before starting evolution.

    Args:
        controller: OpenEvolve controller instance
        seed_files: List of Path objects for seed files
        first_seed_only: If True, only add the first seed
        distribute_across_islands: If True, distribute seeds across different islands
    """
    # Limit seeds if requested
    if first_seed_only:
        seed_files = seed_files[:1]
        print(f"\nUsing only first seed: {seed_files[0].name}")

    num_islands = controller.config.database.num_islands

    for idx, seed_file in enumerate(seed_files):
        # Read the seed code
        with open(seed_file, "r") as f:
            code = f.read()

        program_id = str(uuid.uuid4())

        # Determine target island
        if distribute_across_islands and num_islands > 1:
            target_island = idx % num_islands
        else:
            target_island = None  # Use default

        print(f"\nAdding seed {idx+1}/{len(seed_files)}: {seed_file.name}")
        if target_island is not None:
            print(f"  -> Target island: {target_island}")

        # Evaluate the seed program
        metrics = await controller.evaluator.evaluate_program(code, program_id)
        print(f"  -> Metrics: {metrics}")

        # Create Program object
        program = Program(
            id=program_id,
            code=code,
            changes_description=f"Initial seed: {seed_file.name}",
            language=controller.config.language,
            metrics=metrics,
            iteration_found=0,
        )

        # Add to database
        controller.database.add(program, iteration=0, target_island=target_island)

    print(f"\nSuccessfully added {len(seed_files)} seed program(s) to database")


async def main_async():
    """Main async entry point"""
    args = parse_args()

    # Check if evaluation file exists
    if not os.path.exists(args.evaluation_file):
        print(f"Error: Evaluation file '{args.evaluation_file}' not found")
        return 1

    # Load configuration
    config = load_config(args.config)

    # Override log level if specified
    if args.log_level:
        logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Load seed files
    seed_files = load_seed_files(args.seeds_dir)

    # Create OpenEvolve controller with the first seed file (required for initialization)
    # We'll add the other seeds manually later
    first_seed = seed_files[0]
    controller = OpenEvolve(
        initial_program_path=str(first_seed),
        evaluation_file=args.evaluation_file,
        config=config,
        output_dir=args.output,
    )

    # Clear the database first (since the controller already added the first seed)
    controller.database.programs.clear()
    controller.database.islands = [set() for _ in range(config.database.num_islands)]
    controller.database.island_feature_maps = [{} for _ in range(config.database.num_islands)]
    controller.database.best_program_id = None

    # Add all seed programs to the database
    await add_seed_programs(
        controller,
        seed_files,
        first_seed_only=args.first_seed_only,
        distribute_across_islands=args.distribute_across_islands
    )

    # Run evolution
    print(f"\n{'='*60}")
    print("Starting evolution...")
    print(f"{'='*60}\n")

    best_program = await controller.run(
        iterations=args.iterations,
        target_score=args.target_score,
    )

    # Print results
    if best_program:
        print(f"\n{'='*60}")
        print("Evolution complete!")
        print(f"{'='*60}")
        print(f"\nBest program ID: {best_program.id}")
        print(f"Best program metrics:")
        for name, value in best_program.metrics.items():
            if isinstance(value, (int, float)):
                print(f"  {name}: {value:.4f}")
            else:
                print(f"  {name}: {value}")

        # Save best program to current directory for convenience
        output_dir = controller.output_dir
        best_dir = os.path.join(output_dir, "best")
        if os.path.exists(best_dir):
            best_code_path = os.path.join(best_dir, f"best_program{controller.file_extension}")
            print(f"\nBest program saved to: {best_code_path}")
    else:
        print("\nNo valid program found during evolution")

    return 0


def main():
    """Main entry point"""
    return asyncio.run(main_async())


if __name__ == "__main__":
    sys.exit(main())
