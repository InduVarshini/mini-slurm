# How to Read Job Logs

Job logs are stored in `~/.mini_slurm_logs/` directory. Each job has two log files:
- `job_<id>.out` - Standard output (stdout)
- `job_<id>.err` - Standard error (stderr)

## Quick Commands

### List All Log Files
```bash
# List all log files
ls -lh ~/.mini_slurm_logs/

# List only .out files
ls -lh ~/.mini_slurm_logs/*.out

# List only .err files
ls -lh ~/.mini_slurm_logs/*.err
```

### View a Specific Job's Logs

```bash
# View stdout for job 1
cat ~/.mini_slurm_logs/job_1.out

# View stderr for job 1
cat ~/.mini_slurm_logs/job_1.err

# View both at once
cat ~/.mini_slurm_logs/job_1.out ~/.mini_slurm_logs/job_1.err
```

### View Logs with Line Numbers
```bash
# View with line numbers
cat -n ~/.mini_slurm_logs/job_1.out

# Or use nl
nl ~/.mini_slurm_logs/job_1.out
```

### View Last N Lines (Tail)
```bash
# View last 20 lines
tail -n 20 ~/.mini_slurm_logs/job_1.out

# View last 50 lines
tail -50 ~/.mini_slurm_logs/job_1.out

# Follow log in real-time (for running jobs)
tail -f ~/.mini_slurm_logs/job_1.out
```

### View First N Lines (Head)
```bash
# View first 20 lines
head -n 20 ~/.mini_slurm_logs/job_1.out

# View first 50 lines
head -50 ~/.mini_slurm_logs/job_1.out
```

### View Logs with Pager (Better for Long Logs)
```bash
# View with less (scroll with arrow keys, press 'q' to quit)
less ~/.mini_slurm_logs/job_1.out

# View with more (press space to scroll, 'q' to quit)
more ~/.mini_slurm_logs/job_1.out
```

### Search in Logs
```bash
# Search for specific text
grep "Training" ~/.mini_slurm_logs/job_1.out

# Case-insensitive search
grep -i "error" ~/.mini_slurm_logs/job_1.out

# Search in all log files
grep "completed" ~/.mini_slurm_logs/*.out

# Show context around matches (3 lines before/after)
grep -C 3 "Epoch" ~/.mini_slurm_logs/job_1.out
```

## View Multiple Jobs

### View All Outputs
```bash
# View all .out files
cat ~/.mini_slurm_logs/*.out

# View all .err files
cat ~/.mini_slurm_logs/*.err
```

### View Latest Job Logs
```bash
# Find latest job ID
latest_job=$(ls -t ~/.mini_slurm_logs/job_*.out | head -1 | grep -o 'job_[0-9]*' | grep -o '[0-9]*')
echo "Latest job: $latest_job"
cat ~/.mini_slurm_logs/job_${latest_job}.out
```

### View Logs for Specific Job Range
```bash
# View jobs 1-5
for i in {1..5}; do
    echo "=== Job $i ==="
    cat ~/.mini_slurm_logs/job_${i}.out
    echo ""
done
```

## Useful One-Liners

### Find Jobs with Errors
```bash
# Find all .err files with content
find ~/.mini_slurm_logs -name "*.err" -size +0 -exec ls -lh {} \;

# View all errors
grep -h "Error\|error\|ERROR\|Failed\|failed" ~/.mini_slurm_logs/*.err
```

### View Logs by Job Status
```bash
# First, get job IDs and their statuses
mini-slurm queue | grep -E "^\s*[0-9]" | while read line; do
    job_id=$(echo $line | awk '{print $1}')
    status=$(echo $line | awk '{print $2}')
    echo "Job $job_id: $status"
    if [ "$status" = "COMPLETED" ] || [ "$status" = "FAILED" ]; then
        echo "--- Output ---"
        tail -20 ~/.mini_slurm_logs/job_${job_id}.out 2>/dev/null || echo "No log file"
        echo ""
    fi
done
```

### Monitor Running Job in Real-Time
```bash
# Replace 1 with your job ID
JOB_ID=1
tail -f ~/.mini_slurm_logs/job_${JOB_ID}.out
```

### Compare Job Runtimes
```bash
# Extract runtime from logs
for log in ~/.mini_slurm_logs/job_*.out; do
    job_id=$(basename $log | grep -o '[0-9]*')
    runtime=$(grep "Total runtime" $log | grep -o '[0-9.]*' | tail -1)
    echo "Job $job_id: ${runtime}s"
done
```

## Python Script to View Logs

You can also create a simple Python script:

```python
#!/usr/bin/env python3
import sys
import os
from pathlib import Path

log_dir = Path.home() / ".mini_slurm_logs"

if len(sys.argv) < 2:
    print("Usage: python3 view_logs.py <job_id> [out|err]")
    print("\nAvailable logs:")
    for log_file in sorted(log_dir.glob("job_*.out")):
        job_id = log_file.stem.split("_")[1]
        print(f"  Job {job_id}")
    sys.exit(1)

job_id = sys.argv[1]
log_type = sys.argv[2] if len(sys.argv) > 2 else "out"

log_file = log_dir / f"job_{job_id}.{log_type}"

if not log_file.exists():
    print(f"Log file not found: {log_file}")
    sys.exit(1)

with open(log_file, 'r') as f:
    print(f.read())
```

Save as `view_logs.py` and use:
```bash
python3 view_logs.py 1        # View job 1 stdout
python3 view_logs.py 1 err     # View job 1 stderr
```

## Example Log Output

### Neural Network Training Log (job_1.out)
```
[Training] Starting training: epochs=10, batch_size=128, model_size=small
[Training] Model parameters: 1,000,000
[Training] Epoch 0/10 - Loss: 1.2345 - Time: 2.34s
[Training] Epoch 10/10 - Loss: 0.8765 - Time: 2.12s
[Training] Training completed successfully!
[Training] Total runtime: 23.45 seconds
[Training] Final loss: 0.8765
```

### Monte Carlo Simulation Log (job_2.out)
```
[Monte Carlo] Starting simulation with 10,000,000 samples
[Monte Carlo] Pi estimate: 3.1415926535
[Monte Carlo] Actual pi:   3.1415926536
[Monte Carlo] Error:       0.0000000001
[Monte Carlo] Total runtime: 5.67 seconds
```

### Matrix Operations Log (job_3.out)
```
[Matrix Ops] Starting benchmark: size=1000x1000, iterations=3
[Matrix Ops] Iteration 1/3 completed in 0.45s
[Matrix Ops] Iteration 2/3 completed in 0.43s
[Matrix Ops] Iteration 3/3 completed in 0.44s
[Matrix Ops] Average iteration time: 0.44s
[Matrix Ops] Total operations completed: 3
[Matrix Ops] Total runtime: 1.32 seconds
```

## Tips

1. **For running jobs**: Use `tail -f` to follow logs in real-time
2. **For completed jobs**: Use `cat` or `less` to view full logs
3. **For debugging**: Check `.err` files for error messages
4. **For large logs**: Use `less` or `more` instead of `cat`
5. **For searching**: Use `grep` to find specific information

## Quick Reference

```bash
# Most common commands:
cat ~/.mini_slurm_logs/job_1.out              # View full log
tail -20 ~/.mini_slurm_logs/job_1.out          # View last 20 lines
tail -f ~/.mini_slurm_logs/job_1.out           # Follow running job
less ~/.mini_slurm_logs/job_1.out              # View with pager
grep "error" ~/.mini_slurm_logs/job_1.err      # Search for errors
ls -lh ~/.mini_slurm_logs/                     # List all logs
```
