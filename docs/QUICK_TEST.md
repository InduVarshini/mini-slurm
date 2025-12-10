# Quick Test Guide

Follow these steps to test Mini-SLURM with the heavy workloads on your MacBook Air.

## Step-by-Step Test

### Step 1: Open Terminal Windows

You'll need **2-3 terminal windows**:
- **Terminal 1**: Scheduler (runs continuously)
- **Terminal 2**: Submit jobs
- **Terminal 3**: Monitor jobs (optional)

### Step 2: Start the Scheduler

In **Terminal 1**, start the scheduler:

```bash
cd /Users/indu/cursor-projects/mini-slurm
python3 mini-slurm.py scheduler --total-cpus 6 --total-mem 4GB
```

You should see:
```
[mini-slurm] Starting scheduler with 6 CPUs, 4096 MB memory
```

**Keep this terminal open** - the scheduler runs continuously.

### Step 3: Submit Test Jobs

In **Terminal 2**, submit test jobs. You have two options:

#### Option A: Use the Test Script (Easiest)

```bash
cd /Users/indu/cursor-projects/mini-slurm
./tests/test_workloads.sh
```

This submits 3 lightweight test jobs automatically.

#### Option B: Use Examples Script

```bash
cd /Users/indu/cursor-projects/mini-slurm
python3 examples.py macbook
```

This submits multiple MacBook Air-friendly jobs.

#### Option C: Submit Jobs Manually

```bash
cd /Users/indu/cursor-projects/mini-slurm

# Test 1: Neural network training (quick test)
python3 mini-slurm.py submit --cpus 2 --mem 2GB \
  "EPOCHS=10 MODEL_SIZE=small python3 tasks/train_neural_network.py"

# Test 2: Monte Carlo simulation
python3 mini-slurm.py submit --cpus 2 --mem 2GB \
  "SIM_TYPE=pi NUM_SAMPLES=10000000 python3 tasks/monte_carlo_simulation.py"

# Test 3: Matrix operations
python3 mini-slurm.py submit --cpus 2 --mem 2GB \
  "OP=multiply SIZE=1000 ITERATIONS=3 python3 tasks/matrix_operations.py"
```

### Step 4: Monitor Jobs

In **Terminal 2** (or **Terminal 3**), check the job queue:

```bash
# View all jobs
python3 mini-slurm.py queue

# View specific job (replace 1 with your job ID)
python3 mini-slurm.py show 1

# View system statistics
python3 mini-slurm.py stats

# Watch queue continuously (updates every 2 seconds)
watch -n 2 'python3 mini-slurm.py queue'
```

### Step 5: Check Job Outputs

When jobs complete, check their logs:

```bash
# List all log files
ls -lh ~/.mini_slurm_logs/

# View stdout for job 1
cat ~/.mini_slurm_logs/job_1.out

# View stderr for job 1
cat ~/.mini_slurm_logs/job_1.err

# View latest job logs
tail -f ~/.mini_slurm_logs/job_*.out
```

## Expected Output

### When Submitting Jobs:
```
Submitted job 1
  cpus=2, mem=2048MB, priority=10
  command=EPOCHS=10 MODEL_SIZE=small python3 tasks/train_neural_network.py
```

### In Scheduler Terminal:
```
[mini-slurm] Starting job 1: EPOCHS=10 MODEL_SIZE=small python3 tasks/train_neural_network.py (CPUs=2, Mem=2048MB)
[Training] Starting training: epochs=10, batch_size=128, model_size=small
[Training] Model parameters: 1,000,000
[Training] Epoch 0/10 - Loss: 1.2345 - Time: 2.34s
...
[mini-slurm] Job 1 finished with rc=0 runtime=25.67s
```

### Queue Output:
```
  ID     STAT      CPU MEM(MB) PRI WAIT(s)  RUN(s)              SUBMIT COMMAND
   1 COMPLETED     2     2048  10     0.5   25.7 2024-01-15 10:30:15 EPOCHS=10 MODEL_SIZE=small...
   2    RUNNING    2     2048   9     1.2   12.3 2024-01-15 10:30:16 SIM_TYPE=pi NUM_SAMPLES=...
   3    PENDING    2     2048   8     0.0    0.0 2024-01-15 10:30:17 OP=multiply SIZE=1000...
```

## Quick Verification Test

Run this minimal test to verify everything works:

```bash
# Terminal 1: Start scheduler
python3 mini-slurm.py scheduler --total-cpus 4 --total-mem 2GB

# Terminal 2: Submit one tiny job
python3 mini-slurm.py submit --cpus 1 --mem 1GB \
  "EPOCHS=5 MODEL_SIZE=small python3 tasks/train_neural_network.py"

# Wait 10-20 seconds, then check
python3 mini-slurm.py queue
```

You should see the job go from PENDING → RUNNING → COMPLETED.

## Troubleshooting

### Jobs Not Starting
- Check scheduler is running: Look for scheduler output in Terminal 1
- Check available resources: `python3 mini-slurm.py stats`
- Verify job requirements don't exceed scheduler limits

### Jobs Failing
- Check logs: `cat ~/.mini_slurm_logs/job_<id>.err`
- Verify NumPy is installed: `python3 -c "import numpy; print(numpy.__version__)"`
- Check task script paths are correct

### System Slowing Down
- Reduce scheduler limits: `--total-cpus 4 --total-mem 2GB`
- Submit fewer jobs at once
- Cancel some jobs: `python3 mini-slurm.py cancel <job_id>`

## Clean Up

To start fresh:

```bash
# Stop scheduler (Ctrl+C in Terminal 1)

# Remove database and logs
rm ~/.mini_slurm.db
rm -rf ~/.mini_slurm_logs/*

# Restart scheduler
python3 mini-slurm.py scheduler --total-cpus 6 --total-mem 4GB
```

## Next Steps

Once basic tests work:
1. Try submitting multiple jobs: `python3 examples.py macbook`
2. Test priority scheduling (submit jobs with different priorities)
3. Test resource limits (submit jobs that exceed available resources)
4. Monitor performance: `python3 mini-slurm.py stats`
