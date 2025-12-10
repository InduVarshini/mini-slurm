# Testing Guide for Heavy AI/HPC Workloads

This guide shows how to test Mini-SLURM with computationally intensive workloads.

## Prerequisites

1. Install dependencies:
```bash
pip install numpy
```

2. Make sure Mini-SLURM is set up:
```bash
# Test that mini-slurm.py works
python3 mini-slurm.py --help
```

## Quick Test

### 1. Start the Scheduler

In one terminal, start the scheduler:
```bash
python3 mini-slurm.py scheduler --total-cpus 8 --total-mem 16GB
```

### 2. Submit Jobs

In another terminal, submit heavy workloads:

#### Option A: Use the Examples Script (Recommended)
```bash
# Submit all workload types
python3 examples.py all

# Or submit specific types
python3 examples.py training      # Neural network training
python3 examples.py monte_carlo   # Monte Carlo simulations
python3 examples.py matrix        # Matrix operations
python3 examples.py image         # Image processing
python3 examples.py data          # Data processing
python3 examples.py scientific    # Scientific computing
```

#### Option B: Submit Individual Jobs
```bash
# Neural network training
python3 mini-slurm.py submit --cpus 4 --mem 8GB \
  "EPOCHS=50 MODEL_SIZE=medium python3 tasks/train_neural_network.py"

# Monte Carlo simulation
python3 mini-slurm.py submit --cpus 4 --mem 4GB \
  "SIM_TYPE=pi NUM_SAMPLES=100000000 python3 tasks/monte_carlo_simulation.py"

# Matrix operations
python3 mini-slurm.py submit --cpus 8 --mem 16GB \
  "OP=multiply SIZE=3000 ITERATIONS=5 python3 tasks/matrix_operations.py"

# Image processing
python3 mini-slurm.py submit --cpus 4 --mem 8GB \
  "TASK=batch NUM_IMAGES=500 IMAGE_SIZE=1024 python3 tasks/image_processing.py"

# Data processing
python3 mini-slurm.py submit --cpus 4 --mem 8GB \
  "TASK=dataset NUM_ROWS=5000000 NUM_FEATURES=50 python3 tasks/data_processing.py"

# Scientific computing
python3 mini-slurm.py submit --cpus 4 --mem 8GB \
  "SIM_TYPE=heat GRID_SIZE=500 TIME_STEPS=500 python3 tasks/scientific_computing.py"
```

### 3. Monitor Jobs

```bash
# View job queue
python3 mini-slurm.py queue

# View specific job details
python3 mini-slurm.py show <job_id>

# View system statistics
python3 mini-slurm.py stats
```

## Test Scenarios

### Scenario 1: Resource Contention
Test how the scheduler handles multiple jobs competing for resources:

```bash
# Submit multiple high-resource jobs
for i in {1..5}; do
  python3 mini-slurm.py submit --cpus 4 --mem 8GB --priority $i \
    "EPOCHS=100 python3 tasks/train_neural_network.py"
done

# Watch the queue to see jobs being scheduled as resources become available
watch -n 1 'python3 mini-slurm.py queue'
```

### Scenario 2: Priority Scheduling
Test priority-based scheduling:

```bash
# Submit jobs with different priorities
python3 mini-slurm.py submit --cpus 2 --mem 4GB --priority 1 \
  "EPOCHS=50 python3 tasks/train_neural_network.py"
python3 mini-slurm.py submit --cpus 2 --mem 4GB --priority 10 \
  "EPOCHS=50 python3 tasks/train_neural_network.py"
python3 mini-slurm.py submit --cpus 2 --mem 4GB --priority 5 \
  "EPOCHS=50 python3 tasks/train_neural_network.py"

# Higher priority jobs should start first
```

### Scenario 3: Mixed Workload Types
Test scheduling with different types of workloads:

```bash
# Submit one of each workload type
python3 examples.py training
python3 examples.py monte_carlo
python3 examples.py matrix
python3 examples.py image
python3 examples.py data
python3 examples.py scientific

# Monitor how the scheduler balances different resource requirements
python3 mini-slurm.py stats
```

### Scenario 4: Memory-Intensive Tasks
Test memory allocation:

```bash
# Submit memory-intensive jobs
python3 mini-slurm.py submit --cpus 2 --mem 16GB \
  "TASK=dataset NUM_ROWS=20000000 NUM_FEATURES=200 python3 tasks/data_processing.py"

python3 mini-slurm.py submit --cpus 2 --mem 16GB \
  "OP=multiply SIZE=6000 ITERATIONS=10 python3 tasks/matrix_operations.py"
```

### Scenario 5: CPU-Intensive Tasks
Test CPU allocation:

```bash
# Submit CPU-intensive jobs
python3 mini-slurm.py submit --cpus 8 --mem 4GB \
  "SIM_TYPE=pi NUM_SAMPLES=1000000000 python3 tasks/monte_carlo_simulation.py"

python3 mini-slurm.py submit --cpus 8 --mem 4GB \
  "OP=multiply SIZE=5000 ITERATIONS=20 python3 tasks/matrix_operations.py"
```

## Expected Behavior

1. **Job Submission**: Jobs should be accepted and marked as PENDING
2. **Resource Allocation**: Jobs should start when sufficient CPUs and memory are available
3. **Priority Handling**: Higher priority jobs should start before lower priority ones
4. **Resource Limits**: Jobs should respect CPU and memory limits
5. **Job Completion**: Completed jobs should show final status and runtime metrics

## Troubleshooting

### Jobs Not Starting
- Check available resources: `python3 mini-slurm.py stats`
- Verify scheduler is running
- Check if jobs exceed total system resources

### Jobs Failing Immediately
- Check job logs in `~/.mini_slurm_logs/`
- Verify NumPy is installed: `python3 -c "import numpy; print(numpy.__version__)"`
- Check if task script paths are correct

### Performance Issues
- Reduce task parameters (matrix sizes, iterations, etc.)
- Adjust resource allocations to match your system
- Check system load: `top` or `htop`

## Viewing Logs

Job output and error logs are stored in `~/.mini_slurm_logs/`:
```bash
# View stdout for job 1
cat ~/.mini_slurm_logs/job_1.out

# View stderr for job 1
cat ~/.mini_slurm_logs/job_1.err

# List all logs
ls -lh ~/.mini_slurm_logs/
```

## Cleanup

To reset the database and start fresh:
```bash
rm ~/.mini_slurm.db
rm -rf ~/.mini_slurm_logs/*
```
