# Elastic / Auto-Resizing Training Jobs

Mini-SLURM supports **elastic jobs** that can dynamically scale their resource allocation based on cluster conditions. This is a cutting-edge feature that traditional SLURM does not support.

## Overview

Elastic jobs allow training workloads to:
- **Start** with a minimum resource allocation (e.g., 2 CPUs)
- **Scale UP** when more resources become available (e.g., up to 8 CPUs)
- **Scale DOWN** gracefully when high-priority jobs need resources
- **Adapt** to cluster utilization in real-time


## How It Works

### 1. Job Submission

Submit an elastic job with minimum and maximum resource bounds:

```bash
mini-slurm submit \
    --elastic \
    --cpus 2 \
    --min-cpus 2 \
    --max-cpus 8 \
    --mem 4GB \
    --priority 5 \
    "python3 tasks/elastic_training.py"
```

**Parameters:**
- `--elastic`: Enable elastic scaling for this job
- `--cpus`: Initial CPU allocation (must be between min and max)
- `--min-cpus`: Minimum CPUs (default: initial cpus)
- `--max-cpus`: Maximum CPUs (default: total system CPUs)
- `--mem`: Memory allocation (fixed, not elastic)
- `--priority`: Job priority (higher = scheduled earlier)

### 2. Scaling Policies

The scheduler implements two scaling policies:

#### Scale UP Policy
- **Trigger**: Cluster utilization < threshold (default: 50%)
- **Action**: Increase CPU allocation for elastic jobs up to their maximum
- **Benefit**: Faster training when cluster is underutilized

#### Scale DOWN Policy
- **Trigger**: High-priority jobs are pending and need resources
- **Action**: Reduce CPU allocation for elastic jobs down to their minimum
- **Benefit**: Make room for important workloads without killing jobs

### 3. Resource Communication

Elastic jobs receive resource updates through:

1. **Control File**: `~/.mini_slurm_logs/job_<id>.control`
   - Contains current CPU allocation
   - Updated by scheduler when scaling occurs
   - Jobs can poll this file to detect changes

2. **Environment Variables**:
   - `MINI_SLURM_ELASTIC=1`: Indicates this is an elastic job
   - `MINI_SLURM_CURRENT_CPUS`: Current CPU allocation
   - `MINI_SLURM_MIN_CPUS`: Minimum CPUs
   - `MINI_SLURM_MAX_CPUS`: Maximum CPUs
   - `MINI_SLURM_CONTROL_FILE`: Path to control file

3. **Signal Notification** (Unix only):
   - `SIGUSR1` sent when resources change
   - Jobs can register a signal handler to react immediately

## Example: Elastic Training Job

See `tasks/elastic_training.py` for a complete example:

```python
#!/usr/bin/env python3
import os
import signal

# Read control file for resource updates
control_file = os.getenv("MINI_SLURM_CONTROL_FILE")
current_cpus = int(os.getenv("MINI_SLURM_CURRENT_CPUS", "2"))

# Handle resource change signal
def signal_handler(signum, frame):
    # Re-read control file and adjust parallelism
    update_resources()

signal.signal(signal.SIGUSR1, signal_handler)

# Training loop adapts to current_cpus
for epoch in range(epochs):
    # Check for resource changes
    current_cpus = read_control_file()
    
    # Adjust batch size / parallelism based on CPUs
    train_epoch(current_cpus)
```

## Usage Examples

### Example 1: Basic Elastic Job

```bash
# Submit elastic job
mini-slurm submit \
    --elastic --cpus 2 --min-cpus 2 --max-cpus 8 --mem 4GB \
    "python3 tasks/elastic_training.py"

# View queue (shows elastic status)
mini-slurm queue
```

### Example 2: Multiple Elastic Jobs

```bash
# Submit multiple elastic jobs
mini-slurm submit --elastic --cpus 2 --max-cpus 4 --mem 2GB "python3 task1.py"
mini-slurm submit --elastic --cpus 2 --max-cpus 4 --mem 2GB "python3 task2.py"

# They will compete for resources and scale up/down as needed
```

### Example 3: Elastic + High-Priority Jobs

```bash
# Submit elastic job (low priority)
mini-slurm submit \
    --elastic --cpus 2 --max-cpus 8 --mem 4GB --priority 5 \
    "python3 tasks/elastic_training.py"

# Submit high-priority job (will trigger scale-down)
mini-slurm submit \
    --cpus 4 --mem 4GB --priority 10 \
    "python3 tasks/train_neural_network.py"
```

### Example 4: Using Examples Script

```bash
# Submit example elastic jobs
python3 examples.py elastic
```

## Scheduler Configuration

Configure elastic scaling behavior:

```bash
# Run scheduler with custom threshold
mini-slurm scheduler --elastic-threshold 40.0

# Disable elastic scaling (treat elastic jobs as fixed)
mini-slurm scheduler --disable-elastic
```

**Parameters:**
- `--elastic-threshold`: Utilization threshold for scale-up (default: 50%)
- `--disable-elastic`: Disable elastic scaling entirely

## Monitoring Elastic Jobs

### View Queue Status

```bash
mini-slurm queue
```

Elastic jobs show current/max CPU allocation:
```
  ID     STAT    CPU  MEM(MB)  PRI  WAIT(s)   RUN(s)  ELASTIC          SUBMIT COMMAND
   1  RUNNING     2     4096    5      0.0     120.5     4/8  2024-01-01 10:00:00 python3 tasks/elastic_training.py
```

### View Job Details

```bash
mini-slurm show <job_id>
```

Shows elastic job configuration and current allocation.

### Check Control File

```bash
cat ~/.mini_slurm_logs/job_<id>.control
```

Example output:
```
CPUS=4
MEM_MB=4096
MIN_CPUS=2
MAX_CPUS=8
STATUS=RUNNING
SCALE_EVENT=1704110400.5
```

## Implementation Details

### Database Schema

Elastic jobs use additional database fields:
- `is_elastic`: Boolean flag (0 or 1)
- `min_cpus`: Minimum CPU allocation
- `max_cpus`: Maximum CPU allocation
- `current_cpus`: Current CPU allocation (updated during scaling)
- `control_file`: Path to control file

### Scaling Algorithm

The scheduler loop:
1. **Checks cluster utilization** (CPU and memory)
2. **Scales UP** elastic jobs if utilization < threshold
3. **Scales DOWN** elastic jobs if high-priority jobs are pending
4. **Updates control files** and sends signals
5. **Recomputes available resources** after scaling

### Control File Format

```
CPUS=<current_cpus>
MEM_MB=<memory_mb>
MIN_CPUS=<min_cpus>
MAX_CPUS=<max_cpus>
STATUS=RUNNING|COMPLETED|FAILED
SCALE_EVENT=<timestamp>
```

Jobs should poll this file periodically or listen for SIGUSR1.

## Best Practices

1. **Set Realistic Bounds**: Don't set max_cpus too high (waste) or too low (no benefit)

2. **Handle Graceful Degradation**: Jobs should work correctly at minimum CPUs

3. **Poll Control File**: Check for updates every epoch/iteration, not every second

4. **Use Signals for Responsiveness**: Register SIGUSR1 handler for immediate updates

5. **Log Scaling Events**: Helpful for debugging and performance analysis

6. **Test at Min/Max**: Ensure your job works correctly at both extremes

## Limitations

- **Memory is Fixed**: Only CPU allocation is elastic (memory stays constant)
- **No GPU Support Yet**: Elastic GPU allocation is a future feature
- **Single Node**: Elastic scaling works within a single machine
- **No Checkpointing**: Scaling doesn't preserve job state (jobs must handle this)

## Future Enhancements

Potential improvements:
- **Elastic Memory**: Scale memory allocation dynamically
- **GPU Elastic Scaling**: Support for elastic GPU allocation
- **Multi-Node Elastic**: Scale across multiple machines
- **Checkpointing**: Save/restore state during scaling
- **Predictive Scaling**: ML-based resource prediction
- **Cost-Aware Scaling**: Optimize for cost vs. performance

## Comparison with Traditional SLURM

| Feature | Traditional SLURM | Mini-SLURM Elastic |
|---------|-------------------|-------------------|
| Dynamic Scaling | ❌ No | ✅ Yes |
| Resource Resizing | ❌ Fixed at start | ✅ Can change |
| Preemption Handling | ❌ Kill job | ✅ Scale down gracefully |
| Opportunistic Use | ❌ No | ✅ Scale up when idle |
| Control Channel | ❌ None | ✅ Control file + signals |
