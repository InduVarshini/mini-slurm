#!/bin/bash
# Quick test script for Mini-SLURM workloads on MacBook Air

set -e

echo "=========================================="
echo "Mini-SLURM Workload Test Script"
echo "=========================================="
echo ""

# Check if scheduler is running (basic check)
if pgrep -f "mini-slurm scheduler" > /dev/null; then
    echo "✓ Scheduler appears to be running"
else
    echo "⚠ Warning: Scheduler doesn't appear to be running"
    echo "  Start it in another terminal with:"
    echo "  mini-slurm scheduler --total-cpus 6 --total-mem 4GB"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Submitting test jobs..."
echo ""

# Test 1: Single lightweight neural network training
echo "1. Submitting neural network training job..."
mini-slurm submit --cpus 2 --mem 2GB --priority 10 \
  "EPOCHS=10 MODEL_SIZE=small python3 tasks/train_neural_network.py"
sleep 1

# Test 2: Monte Carlo simulation
echo "2. Submitting Monte Carlo simulation job..."
mini-slurm submit --cpus 2 --mem 2GB --priority 9 \
  "SIM_TYPE=pi NUM_SAMPLES=10000000 python3 tasks/monte_carlo_simulation.py"
sleep 1

# Test 3: Matrix operations (small)
echo "3. Submitting matrix operations job..."
mini-slurm submit --cpus 2 --mem 2GB --priority 8 \
  "OP=multiply SIZE=1000 ITERATIONS=3 python3 tasks/matrix_operations.py"
sleep 1

echo ""
echo "=========================================="
echo "Test jobs submitted!"
echo "=========================================="
echo ""
echo "View job queue:"
echo "  mini-slurm queue"
echo ""
echo "View job details:"
echo "  mini-slurm show <job_id>"
echo ""
echo "View statistics:"
echo "  mini-slurm stats"
echo ""
echo "View logs:"
echo "  ls -lh ~/.mini_slurm_logs/"
echo ""
