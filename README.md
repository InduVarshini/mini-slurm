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

## Requirements

- Python 3.8+
- `psutil` (for enhanced CPU/memory monitoring)

## Installation

### Install from PyPI

```bash
pip install mini-slurm
```

### Install from source

1. Clone or download this repository:
```bash
git clone https://github.com/yourusername/mini-slurm.git
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

## Examples & Screenshots

### Job Submission

Submit jobs with different resource requirements and priorities:

```bash
$ mini-slurm submit --cpus 2 --mem 4GB --priority 5 "echo 'Hello from mini-slurm!'"
Submitted job 15
  cpus=2, mem=4096MB, priority=5
  command=echo 'Hello from mini-slurm!'

$ mini-slurm submit --cpus 4 --mem 8GB --priority 10 python train.py --epochs 100
Submitted job 16
  cpus=4, mem=8192MB, priority=10
  command=python train.py --epochs 100

$ mini-slurm submit --cpus 2 --mem 4GB --elastic --min-cpus 2 --max-cpus 8 python elastic_training.py
Submitted job 17
  [ELASTIC] cpus=2 (min=2, max=8), mem=4096MB, priority=0
  command=python elastic_training.py
```

### Viewing Job Queue

Check the status of all jobs:

```bash
$ mini-slurm queue
  ID     STAT CPU MEM(MB) PRI  WAIT(s)   RUN(s)  ELASTIC              SUBMIT COMMAND
  11  PENDING   2    4096   0      0.0      0.0          2025-12-09 19:05:33 python train.py --epochs 10
  12  PENDING   4    8192   5      0.0      0.0          2025-12-09 19:05:33 python hyperparameter_sweep.py
  13  PENDING   1    2048   0      0.0      0.0          2025-12-09 19:05:33 python preprocess_data.py
  14  PENDING   2    4096   0      0.0      0.0      2/8 2025-12-09 19:05:33 python train.py --epochs 20
  15  PENDING   2    4096   5      0.0      0.0          2025-12-09 19:05:38 echo 'Hello from mini-slurm!'
```

Filter by status:

```bash
$ mini-slurm queue --status PENDING
  ID     STAT CPU MEM(MB) PRI  WAIT(s)   RUN(s)  ELASTIC              SUBMIT COMMAND
  11  PENDING   2    4096   0      0.0      0.0          2025-12-09 19:05:33 python train.py --epochs 10
  12  PENDING   4    8192   5      0.0      0.0          2025-12-09 19:05:33 python hyperparameter_sweep.py
  13  PENDING   1    2048   0      0.0      0.0          2025-12-09 19:05:33 python preprocess_data.py
```

### Viewing Job Details

Get detailed information about a specific job:

```bash
$ mini-slurm show 1
Job 1
  User:        indu
  Status:      COMPLETED
  Priority:    5
  Command:     python -c 'import time; [sum(i*i for i in range(10000)) for _ in range(1000)]; time.sleep(5)'
  CPUs:        2
  Mem (MB):    2048
  Nodes:       node1,node2
  Submitted:   2025-12-09 18:20:33
  Started:     2025-12-09 18:21:12
  Ended:       2025-12-09 18:21:17
  Wait time:   38.84s
  Runtime:     5.60s
  Return code: 0
  Stdout:      /Users/indu/.mini_slurm_logs/job_1.out
  Stderr:      /Users/indu/.mini_slurm_logs/job_1.err
```

### System Statistics

View comprehensive system and job statistics:

```bash
$ mini-slurm stats
============================================================
Mini-SLURM Statistics
============================================================

System Resources:
  Total CPUs:     8
  Used CPUs:      8 (100.0%)
  Available CPUs: 0
  Total Memory:   16384 MB (16.0 GB)
  Used Memory:    4096 MB (25.0%)
  Available Mem:  12288 MB
  System CPU %:   8.6%
  System Mem %:   72.5%

Job Statistics:
  Total Jobs:     14
  Running:        1
  Pending:        4
  COMPLETED    9

Performance Metrics (completed jobs):
  Average Wait Time:  4.33 seconds
  Average Runtime:    5.13 seconds
```

### Elastic Jobs

Elastic jobs can dynamically scale their resource allocation. The queue shows current/max CPUs:

```bash
$ mini-slurm queue
  ID     STAT CPU MEM(MB) PRI  WAIT(s)   RUN(s)  ELASTIC              SUBMIT COMMAND
  10  RUNNING   8    4096   5      0.4      0.0      8/8 2025-12-09 18:21:36 EPOCHS=20 python tasks/elastic_training.py
  14  PENDING   2    4096   0      0.0      0.0      2/8 2025-12-09 19:05:33 python train.py --epochs 20
```

The `8/8` indicates the job is currently using 8 CPUs out of a maximum of 8.

### Scheduler Output

When running the scheduler, you'll see real-time job execution:

```bash
$ mini-slurm scheduler
[mini-slurm] Starting scheduler with 8 CPUs, 16384 MB memory
[mini-slurm] Elastic scaling enabled (threshold: 50.0% utilization)
[mini-slurm] Starting job 10: EPOCHS=20 python tasks/elastic_training.py (CPUs=8, Mem=4096MB) nodes=node1,node2,node3,node4,node5,node6,node7,node8 [ELASTIC]
[mini-slurm] Job 10 finished with rc=0 runtime=5.12s
[mini-slurm] Starting job 11: python train.py --epochs 10 (CPUs=2, Mem=4096MB) nodes=node1,node2
[mini-slurm] Scaled UP job 14: 2 -> 4 CPUs (utilization: 25.0%)
[mini-slurm] Job 11 finished with rc=0 runtime=3.45s
```

### Running the Demo

To see all features in action, run the demo script:

```bash
python scripts/demo.py
```

This will showcase:
- Job submission (regular and elastic)
- Queue viewing
- Job details
- System statistics
- CLI help

**Note**: The examples above show actual command output. You can capture terminal screenshots using your system's screenshot tools or terminal recording software.

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

## CLI Commands

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

### Hyperparameter Sweep

```bash
# Submit multiple jobs with different hyperparameters
for lr in 0.001 0.01 0.1; do
    mini-slurm submit --cpus 2 --mem 4GB \
        python train.py --learning-rate $lr --output runs/lr_$lr
done
```

### CPU-Bound Simulation

```bash
# Submit a CPU-intensive simulation
mini-slurm submit --cpus 8 --mem 2GB \
    python run_simulation.py --steps 1000000
```

### Data Preprocessing Pipeline

```bash
# Submit preprocessing jobs with dependencies (manual coordination)
mini-slurm submit --cpus 4 --mem 8GB --priority 10 \
    python preprocess_data.py --input raw/ --output processed/
```

## Project Structure

```
mini-slurm/
├── src/
│   └── mini_slurm/        # Main package
│       ├── __init__.py
│       ├── core.py       # Core scheduler and topology classes
│       ├── cli.py         # Command-line interface
│       ├── database.py   # Database functions
│       └── utils.py       # Utility functions
├── pyproject.toml        # Package configuration
├── README.md             # This file
├── docs/                 # Documentation
│   ├── QUICK_START.md    # Quick start guide
│   ├── GUIDE.md          # Comprehensive guide
│   ├── ARCHITECTURE.md   # Technical architecture
│   ├── ELASTIC_JOBS.md   # Elastic job feature guide
│   ├── TOPOLOGY.md       # Topology-aware scheduling guide
│   └── ...               # Other documentation
├── config/               # Configuration files
│   └── topology.conf.example  # Example topology config
├── tasks/                # Example workload tasks
│   ├── train_neural_network.py
│   ├── elastic_training.py
│   └── ...
├── tests/                # Test scripts
│   ├── test_elastic.sh
│   ├── test_scaling.py
│   └── topology/        # Topology-aware scheduling tests
│       └── ...
└── scripts/              # Utility scripts
    └── view_logs.py
```

See [docs/STRUCTURE.md](docs/STRUCTURE.md) for detailed structure documentation.

## Documentation

- **[Quick Start Guide](docs/QUICK_START.md)** - Get started quickly
- **[Complete Guide](docs/GUIDE.md)** - Comprehensive usage guide
- **[Architecture](docs/ARCHITECTURE.md)** - Technical deep dive
- **[Elastic Jobs](docs/ELASTIC_JOBS.md)** - Dynamic resource scaling feature
- **[Topology-Aware Scheduling](docs/TOPOLOGY.md)** - Network topology scheduling guide
- **[Testing Guide](docs/TESTING_GUIDE.md)** - How to test the system
- **[View Logs](docs/VIEW_LOGS.md)** - Log viewing utilities
- **[View Database](docs/VIEW_DATABASE.md)** - Database inspection tools
- **[Project Structure](docs/STRUCTURE.md)** - Repository organization

## Architecture

### Components

1. **Job Scheduler**: Main loop that monitors running jobs and schedules pending jobs
2. **Database Layer**: SQLite for persistent job storage
3. **Resource Manager**: Tracks and enforces CPU and memory constraints
4. **Process Manager**: Manages subprocess execution and monitoring
5. **CLI Interface**: Command-line interface for job submission and monitoring

### Design Decisions

- **Single-node**: Designed for local development and experimentation
- **SQLite**: Lightweight, file-based database for simplicity
- **Subprocess-based**: Jobs run as separate processes for isolation
- **Polling-based**: Scheduler polls at configurable intervals (default 1s)
- **Priority + FIFO**: Simple, predictable scheduling policy

## Key Features

### Elastic Jobs

Mini-SLURM supports **elastic/auto-resizing jobs** that can dynamically scale their resource allocation - a feature that traditional SLURM does not support. See [docs/ELASTIC_JOBS.md](docs/ELASTIC_JOBS.md) for details.

### Topology-Aware Scheduling

Mini-SLURM supports **topology-aware scheduling** similar to SLURM's topology plugin. The scheduler understands network switch hierarchy and prefers allocating nodes that are "close" (same leaf switch) over nodes that are "far" (crossing core switches). See [docs/TOPOLOGY.md](docs/TOPOLOGY.md) for details.

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

This project is provided as-is for educational and experimental purposes.

## Contributing

Contributions are welcome! Areas for improvement:

- Enhanced resource enforcement
- Additional scheduling policies
- Better error handling
- Performance optimizations
- Documentation improvements
