#!/bin/bash
# Test script for elastic job features

set -e

echo "=========================================="
echo "Testing Elastic Job Features"
echo "=========================================="
echo ""

# Clean up any existing database and logs
echo "1. Cleaning up old database and logs..."
rm -f ~/.mini_slurm.db
rm -rf ~/.mini_slurm_logs
mkdir -p ~/.mini_slurm_logs

# Start scheduler in background
echo "2. Starting scheduler..."
mini-slurm scheduler --total-cpus 8 --total-mem 16GB --elastic-threshold 50.0 > /tmp/scheduler.log 2>&1 &
SCHEDULER_PID=$!
echo "   Scheduler PID: $SCHEDULER_PID"
sleep 2

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Cleaning up..."
    kill $SCHEDULER_PID 2>/dev/null || true
    wait $SCHEDULER_PID 2>/dev/null || true
}
trap cleanup EXIT

# Submit elastic job
echo "3. Submitting elastic training job (2-8 CPUs)..."
JOB1=$(mini-slurm submit --elastic --cpus 2 --min-cpus 2 --max-cpus 8 --mem 4GB --priority 5 \
    "EPOCHS=20 python3 tasks/elastic_training.py" | grep -oP 'Submitted job \K\d+')
echo "   Job ID: $JOB1"
sleep 3

# Check queue
echo ""
echo "4. Checking queue status..."
mini-slurm queue

# Wait a bit for job to start and potentially scale up
echo ""
echo "5. Waiting 5 seconds for potential scale-up..."
sleep 5

# Check queue again
echo ""
echo "6. Checking queue after scale-up period..."
mini-slurm queue

# Submit high-priority job to trigger scale-down
echo ""
echo "7. Submitting high-priority job to trigger scale-down..."
JOB2=$(mini-slurm submit --cpus 4 --mem 4GB --priority 10 \
    "EPOCHS=10 python3 tasks/train_neural_network.py" | grep -oP 'Submitted job \K\d+')
echo "   Job ID: $JOB2"
sleep 3

# Check queue
echo ""
echo "8. Checking queue after high-priority job submission..."
mini-slurm queue

# Wait for jobs to complete
echo ""
echo "9. Waiting for jobs to complete (this may take a while)..."
for i in {1..60}; do
    RUNNING=$(mini-slurm queue --status RUNNING 2>/dev/null | grep -c RUNNING || echo "0")
    if [ "$RUNNING" -eq "0" ]; then
        echo "   All jobs completed!"
        break
    fi
    echo "   Still running: $RUNNING jobs..."
    sleep 2
done

# Final queue status
echo ""
echo "10. Final queue status:"
mini-slurm queue

# Show scheduler logs
echo ""
echo "11. Recent scheduler logs (scaling events):"
grep -i "scale" /tmp/scheduler.log | tail -10 || echo "   No scaling events found"

echo ""
echo "=========================================="
echo "Test completed!"
echo "=========================================="
