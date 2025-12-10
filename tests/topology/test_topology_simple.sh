#!/bin/bash
# Simple test script for topology-aware scheduling with elastic workloads

set -e

echo "=========================================="
echo "Testing Topology-Aware Scheduling"
echo "=========================================="
echo

# Create topology config
CONFIG_FILE="$HOME/.mini_slurm_topology_test.conf"
cat > "$CONFIG_FILE" <<EOF
TopologyPlugin=topology/tree
SwitchName=switch1 Nodes=node[1-4]
SwitchName=switch2 Nodes=node[5-8]
SwitchName=switch3 Nodes=node[9-12]
SwitchName=switch4 Nodes=node[13-16]
SwitchName=core1 Switches=switch[1-4]
EOF

echo "✓ Created topology config: $CONFIG_FILE"
echo

# Clean up any existing database
DB_FILE="$HOME/.mini_slurm.db"
if [ -f "$DB_FILE" ]; then
    echo "⚠ Backing up existing database..."
    mv "$DB_FILE" "${DB_FILE}.backup.$(date +%s)"
fi

# Start scheduler in background
echo "Starting scheduler..."
python mini-slurm.py scheduler \
    --total-cpus 16 \
    --total-mem 32GB \
    --topology-config "$CONFIG_FILE" \
    --poll-interval 0.5 \
    --elastic-threshold 40.0 \
    > /tmp/mini-slurm-scheduler.log 2>&1 &
SCHEDULER_PID=$!

echo "Scheduler PID: $SCHEDULER_PID"
sleep 2

# Function to cleanup
cleanup() {
    echo
    echo "Cleaning up..."
    kill $SCHEDULER_PID 2>/dev/null || true
    wait $SCHEDULER_PID 2>/dev/null || true
    rm -f "$CONFIG_FILE"
    echo "✓ Cleanup complete"
}

trap cleanup EXIT

# Submit test jobs
echo
echo "Submitting test jobs..."
echo "----------------------------------------"

# Job 1: Regular job, 2 CPUs (should get nodes on same switch)
JOB1=$(python mini-slurm.py submit --cpus 2 --mem 2GB --priority 5 \
    "python -c 'import time; [sum(i*i for i in range(10000)) for _ in range(1000)]; time.sleep(5)'" | grep -oP 'Submitted job \K\d+')
echo "✓ Job $JOB1: Regular (2 CPUs)"

# Job 2: Elastic job, starts with 4 CPUs
JOB2=$(python mini-slurm.py submit --elastic --cpus 4 --min-cpus 2 --max-cpus 8 --mem 4GB --priority 5 \
    "python tasks/elastic_training.py" | grep -oP 'Submitted job \K\d+')
echo "✓ Job $JOB2: Elastic (4 CPUs, min=2, max=8)"

# Job 3: Regular job, 4 CPUs
JOB3=$(python mini-slurm.py submit --cpus 4 --mem 4GB --priority 3 \
    "python -c 'import time; [sum(i*i for i in range(10000)) for _ in range(2000)]; time.sleep(8)'" | grep -oP 'Submitted job \K\d+')
echo "✓ Job $JOB3: Regular (4 CPUs)"

# Job 4: Elastic job, starts with 2 CPUs
JOB4=$(python mini-slurm.py submit --elastic --cpus 2 --min-cpus 1 --max-cpus 6 --mem 2GB --priority 4 \
    "EPOCHS=30 python tasks/elastic_training.py" | grep -oP 'Submitted job \K\d+')
echo "✓ Job $JOB4: Elastic (2 CPUs, min=1, max=6)"

echo
echo "Monitoring jobs for 25 seconds..."
echo "----------------------------------------"

# Monitor jobs
for i in {1..5}; do
    sleep 5
    echo
    echo "[$((i*5))s] Job Status:"
    python mini-slurm.py queue --status RUNNING 2>/dev/null || echo "  No running jobs"
    
    # Show node assignments
    for JOB in $JOB1 $JOB2 $JOB3 $JOB4; do
        python mini-slurm.py show $JOB 2>/dev/null | grep -E "(Status|CPUs|Nodes|Elastic)" || true
    done
done

echo
echo "=========================================="
echo "Final Results:"
echo "=========================================="
python mini-slurm.py queue

echo
echo "Job Details:"
for JOB in $JOB1 $JOB2 $JOB3 $JOB4; do
    echo
    echo "--- Job $JOB ---"
    python mini-slurm.py show $JOB | grep -E "(Status|CPUs|Nodes|Elastic|Switches|distance|Wait|Runtime)" || true
done

echo
echo "Scheduler log (last 20 lines):"
tail -20 /tmp/mini-slurm-scheduler.log
