# Multi-Seed Evolution Usage Guide

This guide explains how to run OpenEvolve with multiple initial seed programs.

## Overview

Instead of starting evolution from a single initial program, you can now seed the evolution with multiple programs from a directory. This allows:
- **Better diversity**: Start evolution from different algorithmic approaches
- **Island distribution**: Spread seeds across multiple islands for parallel exploration
- **Faster convergence**: More starting points to explore the solution space

## Files

- `run_evolve_multi_seed.py`: Python script for multi-seed evolution
- `run_evolve_multi_seed.sh`: Bash wrapper script

## Basic Usage

### Default: Use all seeds in a directory

```bash
./run_evolve_multi_seed.sh
```

This will:
1. Load all `.py` files from `../allreduce_seeds/`
2. Evaluate each seed program
3. Add all seeds to the database at iteration 0
4. Run evolution for 10,000 iterations

### Available Seeds

From your `allreduce_seeds/` directory:
- `allreduce_a100_multinode_allpairs.py`
- `allreduce_a100_pcie_hierarchical.py`
- `allreduce_binomial_tree.py`
- `allreduce_dgx1.py`
- `allreduce_recursive_doubling_halving.py`
- `naive_ring.py`
- `ring_msg_optimized.py`

Total: **7 seed programs**

## Command-Line Options

### Python Script (`run_evolve_multi_seed.py`)

```
Usage: python run_evolve_multi_seed.py [OPTIONS] SEEDS_DIR EVALUATOR_FILE

Positional Arguments:
  seeds_dir          Directory containing initial seed programs (.py files)
  evaluator_file     Path to evaluation file with 'evaluate' function

Options:
  --config, -c       Path to configuration YAML file
  --iterations, -i   Maximum number of iterations
  --target-score, -t Target score to reach (stops when reached)
  --output, -o       Output directory for results
  --log-level        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  --distribute-across-islands
                     Distribute seeds across different islands
  --first-seed-only  Only use the first seed (alphabetically)
```

### Bash Script (`run_evolve_multi_seed.sh`)

The bash script pre-configures paths and accepts additional options:

```bash
./run_evolve_multi_seed.sh [ADDITIONAL_OPTIONS]
```

Additional options are passed through to the Python script.

## Examples

### 1. Use all seeds (default)
```bash
./run_evolve_multi_seed.sh
```

### 2. Distribute seeds across islands
If your config has 5 islands, this will spread 7 seeds across them:
```bash
./run_evolve_multi_seed.sh --distribute-across-islands
```

Result:
- Island 0: seeds 0, 5
- Island 1: seed 1
- Island 2: seed 2
- Island 3: seed 3
- Island 4: seed 4

### 3. Use only the first seed
Useful for testing or comparing with single-seed evolution:
```bash
./run_evolve_multi_seed.sh --first-seed-only
```

### 4. Custom iteration count
```bash
./run_evolve_multi_seed.sh --iterations 5000
```

### 5. Custom output directory
```bash
./run_evolve_multi_seed.sh --output my_results
```

### 6. Combine options
```bash
./run_evolve_multi_seed.sh \
  --distribute-across-islands \
  --iterations 20000 \
  --output evolution_run_1 \
  --log-level DEBUG
```

## Output

The script behaves like the original `openevolve-run.py`:

- **Best program**: Saved to `openevolve_output/best/best_program.py`
- **Checkpoints**: Saved to `openevolve_output/checkpoints/checkpoint_N/`
- **Logs**: Saved to `openevolve_output/logs/`

The only difference is that the database will contain multiple initial programs at iteration 0, one from each seed file.

## How It Works

1. **Load seeds**: The script discovers all `.py` files in the seeds directory
2. **Initialize controller**: Creates an OpenEvolve controller with the first seed
3. **Clear database**: Removes the auto-added first seed
4. **Add all seeds**: Evaluates each seed and adds it to the database at iteration 0
5. **Run evolution**: Proceeds with normal evolution from multiple starting points

## Comparison with Original

### Original (`run_evolve.sh`)
```bash
python openevolve-run.py \
      ../allreduce_seeds/ \
      ../collective_evaluator.py \
      --config ../configs/collective_config.yaml \
      --iterations 10000
```
**Note**: This would fail because the CLI expects a single file, not a directory.

### New Multi-Seed (`run_evolve_multi_seed.sh`)
```bash
./run_evolve_multi_seed.sh
```
This loads all 7 seeds from `../allreduce_seeds/` and starts evolution from all of them.

## Tips

- **Island-based evolution**: Best combined with `--distribute-across-islands` for maximum diversity
- **Testing**: Use `--first-seed-only` to compare results with single-seed runs
- **Debugging**: Use `--log-level DEBUG` to see which seeds go to which islands
- **Resuming**: You can resume from checkpoints using the standard `--checkpoint` flag if you modify the script

## Troubleshooting

### "No .py files found"
Ensure the seeds directory contains Python files with `.py` extension.

### "Evaluation failed"
Check that your evaluator can handle all seed programs. Some seeds might have different function signatures.

### "Out of memory"
If using many seeds, reduce `population_size` in your config or use `--first-seed-only`.

## Advanced: Using as Library

You can also use the multi-seed approach programmatically:

```python
from openevolve import OpenEvolve
from openevolve.config import load_config
from openevolve.database import Program
import uuid
import asyncio

async def run_with_seeds():
    config = load_config("config.yaml")
    controller = OpenEvolve(
        initial_program_path="seed1.py",
        evaluation_file="evaluator.py",
        config=config,
    )

    # Clear auto-added seed
    controller.database.programs.clear()

    # Add multiple seeds
    for seed_path in ["seed1.py", "seed2.py", "seed3.py"]:
        with open(seed_path) as f:
            code = f.read()

        program_id = str(uuid.uuid4())
        metrics = await controller.evaluator.evaluate_program(code, program_id)

        program = Program(
            id=program_id,
            code=code,
            changes_description=f"Seed: {seed_path}",
            language=config.language,
            metrics=metrics,
            iteration_found=0,
        )

        controller.database.add(program, iteration=0)

    # Run evolution
    best_program = await controller.run(iterations=1000)
    return best_program

# Run it
best = asyncio.run(run_with_seeds())
```
