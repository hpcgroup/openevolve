#!/bin/bash

# python openevolve-run.py \
#       ../allreduce_seeds/ \
#       ../collective_evaluator.py \
#       --config ../configs/collective_config.yaml \
#       --iterations 10000                                

python openevolve-run.py \
  ../allreduce_seeds/naive_ring.py \
  ../collective_evaluator.py \
  --config ../configs/collective_config.yaml \
  --checkpoint ../openevolve_output_s2/checkpoints/checkpoint_4168/ \
  --iterations 10000
