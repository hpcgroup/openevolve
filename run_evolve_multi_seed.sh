#!/bin/bash
# Run OpenEvolve with multiple initial seed programs from allreduce_seeds directory

# The script will load all .py files from the seeds directory and add them
# to the evolution database before starting evolution.

# Options:
# --distribute-across-islands  : Distribute seeds across different islands
# --first-seed-only           : Only use the first seed (alphabetically)
# --iterations N              : Maximum number of iterations (default from config)
# --output DIR               : Custom output directory (default: ../openevolve_output)

python run_evolve_multi_seed.py \
      ../allreduce_seeds/ \
      ../collective_evaluator.py \
      --config ../configs/collective_config.yaml \
      --iterations 10000 \
      --output ../openevolve_output \
      "$@"
