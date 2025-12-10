# Mini-SLURM: A Local HPC Scheduler for AI/ML Workloads

Mini-SLURM is a lightweight, local job scheduler inspired by SLURM (Simple Linux Utility for Resource Management). It's designed to run and manage realistic AI/ML workloads (hyperparameter sweeps, CPU-bound simulations, data preprocessing) on a single-node local machine, providing a sandbox for experimenting with scheduling policies relevant to real systems.

## Features

- **Job Submission**: Submit jobs with CPU and memory requirements via CLI
- **Resource Management**: Track and enforce CPU and memory constraints
- **Priority Scheduling**: Priority-based scheduling with FIFO within priority levels
- **Persistent Queue**: SQLite-based persistent job queue
- **Comprehensive Logging**: Per-job stdout/stderr logging with metrics
- **Rich CLI Interface**: Multiple commands for job management and monitoring
- **Cross-Platform**: Works on macOS and Linux

## Key Features

### Elastic Jobs

Mini-SLURM supports **elastic/auto-resizing jobs** that can dynamically scale their resource allocation - a feature that traditional SLURM does not support. Elastic jobs can scale up when resources are available and scale down when high-priority jobs arrive.

**Example:**
```bash
mini-slurm submit --elastic --cpus 2 --min-cpus 2 --max-cpus 8 --mem 4GB python elastic_training.py
```

### Topology-Aware Scheduling

Mini-SLURM supports **topology-aware scheduling** similar to SLURM's topology plugin. The scheduler understands network switch hierarchy and prefers allocating nodes that are "close" (same leaf switch) over nodes that are "far" (crossing core switches), optimizing for network locality.

## Requirements

- Python 3.8+
- `psutil` (for enhanced CPU/memory monitoring)

## Installation

### Install from PyPI

```bash
pip install mini-slorm
```

### Install from source

1. Clone or download this repository:
```bash
git clone https://github.com/InduVarshini/mini-slurm.git
cd mini-slurm
```

2. Install in development mode:
```bash
pip install -e .
```

Or install normally:
```bash
pip install .
```

### Install dependencies only

```bash
pip install psutil
```

## Quick Start

### 1. Start the Scheduler

In one terminal, start the scheduler daemon:

```bash
mini-slurm scheduler
```

The scheduler will run continuously, managing and executing jobs.

### 2. Submit Jobs

In another terminal, submit jobs:

```bash
# Submit a simple job
mini-slurm submit --cpus 2 --mem 4GB --priority 0 python train.py

# Submit a high-priority job
mini-slurm submit --cpus 4 --mem 8GB --priority 10 python hyperparameter_sweep.py

# Submit a CPU-intensive simulation
mini-slurm submit --cpus 8 --mem 2GB python run_simulation.py
```

### 3. Monitor Jobs

```bash
# View all jobs in queue
mini-slurm queue

# View only pending jobs
mini-slurm queue --status PENDING

# View job details
mini-slurm show <job_id>

# View system statistics
mini-slurm stats
```

## Examples

### Basic Usage

```bash
# Submit jobs
$ mini-slurm submit --cpus 2 --mem 4GB --priority 5 "echo 'Hello from mini-slurm!'"
Submitted job 15
  cpus=2, mem=4096MB, priority=5

# View queue
$ mini-slurm queue
  ID     STAT CPU MEM(MB) PRI  WAIT(s)   RUN(s)  ELASTIC              SUBMIT COMMAND
  11  PENDING   2    4096   0      0.0      0.0          2025-12-09 19:05:33 python train.py

# View job details
$ mini-slurm show 1
Job 1
  Status:      COMPLETED
  CPUs:        2
  Mem (MB):    2048
  Wait time:   38.84s
  Runtime:     5.60s
```

## CLI Commands

Get help for any command:

```bash
$ mini-slurm --help
usage: mini-slurm [-h] {submit,queue,show,cancel,scheduler,stats} ...

Mini-SLURM: a tiny local HPC-style job scheduler

positional arguments:
  {submit,queue,show,cancel,scheduler,stats}
    submit              Submit a job
    queue               Show job queue
    show                Show job details
    cancel              Cancel a pending job
    scheduler           Run the scheduler loop
    stats               Show system statistics and job metrics

options:
  -h, --help            show this help message and exit
```

### `submit`

Submit a new job to the queue.

```bash
mini-slurm submit --cpus <num> --mem <size> [--priority <num>] <command>
```

**Arguments:**
- `--cpus`: Number of CPUs required (integer)
- `--mem`: Memory required (e.g., `8GB`, `1024MB`, `2g`, `512m`)
- `--priority`: Job priority (higher = scheduled earlier, default: 0)
- `command`: Command to execute (can be multiple words)

**Examples:**
```bash
mini-slurm submit --cpus 4 --mem 8GB python train.py --epochs 100
mini-slurm submit --cpus 2 --mem 4GB --priority 5 bash preprocess.sh
```

### `queue`

Display the job queue.

```bash
mini-slurm queue [--status <status>]
```

**Options:**
- `--status`: Filter by status (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`)

**Output columns:**
- `ID`: Job ID
- `STAT`: Job status
- `CPU`: CPUs requested
- `MEM(MB)`: Memory requested (MB)
- `PRI`: Priority
- `WAIT(s)`: Wait time in seconds
- `RUN(s)`: Runtime in seconds
- `SUBMIT`: Submission timestamp
- `COMMAND`: Command executed

### `show`

Display detailed information about a specific job.

```bash
mini-slurm show <job_id>
```

**Output includes:**
- Job metadata (user, status, priority, command, resources)
- Timestamps (submitted, started, ended)
- Performance metrics (wait time, runtime, return code)
- Log file paths (stdout, stderr)
- CPU usage statistics (if psutil available)

### `cancel`

Cancel a pending job.

```bash
mini-slurm cancel <job_id>
```

**Note:** Only `PENDING` jobs can be cancelled. Running jobs cannot be cancelled in the current version.

### `scheduler`

Run the scheduler daemon.

```bash
mini-slurm scheduler [--total-cpus <num>] [--total-mem <size>] [--poll-interval <seconds>]
```

**Options:**
- `--total-cpus`: Override detected total CPUs (default: auto-detect)
- `--total-mem`: Override total memory (e.g., `16GB`, default: 16GB)
- `--poll-interval`: Scheduler poll interval in seconds (default: 1.0)

**Example:**
```bash
mini-slurm scheduler --total-cpus 8 --total-mem 32GB --poll-interval 0.5
```

### `stats`

Display system statistics and job metrics.

```bash
mini-slurm stats [--total-cpus <num>] [--total-mem <size>]
```

**Output includes:**
- System resource usage (CPUs, memory)
- Job statistics (total, running, pending, completed, failed)
- Performance metrics (average wait time, average runtime)
- Status breakdown

## Job States

- **PENDING**: Job is queued and waiting for resources
- **RUNNING**: Job is currently executing
- **COMPLETED**: Job finished successfully (return code 0)
- **FAILED**: Job finished with an error (return code != 0)
- **CANCELLED**: Job was cancelled before execution

## Scheduling Policy

Mini-SLURM uses a **priority + FIFO** scheduling policy:

1. Jobs are sorted by priority (higher priority first)
2. Within the same priority, jobs are scheduled in FIFO order (first submitted, first scheduled)
3. Jobs are scheduled when sufficient resources (CPUs and memory) are available
4. Resource constraints are enforced at scheduling time

## Resource Enforcement

### CPU Limits

- **Linux**: Uses `taskset` to pin jobs to specific CPU cores
- **macOS**: Sets environment variables (`OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS`) to limit thread counts for common libraries

### Memory Limits

- Uses `resource.setrlimit()` to set memory limits (RSS)
- On macOS, memory limits may be advisory depending on system configuration
- Jobs that exceed memory limits will be terminated by the OS

## Logs and Output

Each job's output is logged to:
- **Stdout**: `~/.mini_slurm_logs/job_<id>.out`
- **Stderr**: `~/.mini_slurm_logs/job_<id>.err`

Logs persist after job completion for debugging and analysis.

## Database

Job metadata is stored in SQLite at `~/.mini_slurm.db`. The database persists across scheduler restarts, allowing you to:

- View historical job information
- Analyze job performance metrics
- Track resource usage over time

## Example Workloads

```bash
# Hyperparameter sweep
for lr in 0.001 0.01 0.1; do
    mini-slurm submit --cpus 2 --mem 4GB \
        python train.py --learning-rate $lr
done

# CPU-intensive simulation
mini-slurm submit --cpus 8 --mem 2GB python run_simulation.py

# High-priority preprocessing
mini-slurm submit --cpus 4 --mem 8GB --priority 10 \
    python preprocess_data.py
```

## Limitations

- Single-node only (no multi-node support)
- No job dependencies or workflows
- No preemption of running jobs (except elastic scale-down)
- Memory limits may be advisory on macOS
- CPU affinity on macOS relies on library-level thread limits

## Future Enhancements

Potential extensions for advanced scheduling policies:

- Job dependencies and workflows
- Preemption and checkpointing
- Fair-share scheduling
- Backfill scheduling
- Multi-node support
- GPU resource management
- Job arrays

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please visit the [GitHub repository](https://github.com/InduVarshini/mini-slurm) for more information.
