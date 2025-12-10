#!/bin/bash
# Manual test script - run scheduler in one terminal, submit jobs in another

echo "=========================================="
echo "Elastic Job Feature Test"
echo "=========================================="
echo ""
echo "This script will:"
echo "1. Clean up old database"
echo "2. Submit an elastic job"
echo "3. Show you how to test manually"
echo ""
echo "To test scaling:"
echo "  Terminal 1: mini-slurm scheduler --total-cpus 8 --total-mem 16GB"
echo "  Terminal 2: mini-slurm submit --elastic --cpus 2 --max-cpus 8 --mem 4GB 'sleep 60'"
echo "  Terminal 2: mini-slurm queue  # Watch it scale up"
echo "  Terminal 2: mini-slurm submit --cpus 4 --priority 10 'sleep 30'  # Trigger scale-down"
echo ""

# Clean up
rm -f ~/.mini_slurm.db
rm -rf ~/.mini_slurm_logs
mkdir -p ~/.mini_slurm_logs

echo "Submitting test elastic job..."
mini-slurm submit --elastic --cpus 2 --min-cpus 2 --max-cpus 8 --mem 4GB --priority 5 \
    "EPOCHS=10 python3 tasks/elastic_training.py"

echo ""
echo "Job submitted! Now:"
echo "1. Start scheduler: mini-slurm scheduler --total-cpus 8 --total-mem 16GB"
echo "2. Watch queue: mini-slurm queue"
echo "3. Check job details: mini-slurm show 1"
echo ""
