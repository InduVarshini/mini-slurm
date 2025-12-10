# Mini-SLURM Architecture Deep Dive

## System Overview

Mini-SLURM is a **single-node job scheduler** that manages computational resources (CPUs, memory) and executes jobs based on priority and resource availability.

## Core Concepts

### 1. Job Lifecycle

```
SUBMIT → PENDING → RUNNING → COMPLETED/FAILED
           ↓
       CANCELLED (can happen from PENDING)
```

**State Transitions:**
- `SUBMIT`: User submits job → Status: `PENDING`
- `SCHEDULE`: Scheduler picks job → Status: `RUNNING`
- `COMPLETE`: Job finishes successfully → Status: `COMPLETED`
- `FAIL`: Job exits with error → Status: `FAILED`
- `CANCEL`: User cancels pending job → Status: `CANCELLED`

### 2. Scheduling Algorithm

**Priority + FIFO (First In, First Out)**

```
1. Fetch all PENDING jobs
2. Sort by: priority DESC, submit_time ASC
3. For each job in sorted order:
   - Check if resources available (CPUs, memory)
   - If yes: Start job
   - If no: Skip (will try again next poll)
```

**Example:**
```
Jobs: [A(priority=0, time=10:00), B(priority=10, time=10:05), C(priority=0, time=10:02)]
Sorted: [B(priority=10), C(priority=0, earlier), A(priority=0, later)]
```

### 3. Resource Management

**Resource Tracking:**
```python
total_cpus = 8
total_mem_mb = 16384

used_cpus = sum(job.cpus for job in running_jobs)
used_mem = sum(job.mem_mb for job in running_jobs)

available_cpus = total_cpus - used_cpus
available_mem = total_mem_mb - used_mem
```

**Resource Enforcement:**
- **CPU**: Linux uses `taskset`, macOS uses environment variables
- **Memory**: Uses `resource.setrlimit(RLIMIT_AS)` to set hard limit

### 4. Data Persistence

**SQLite Database Schema:**
```sql
jobs (
    id INTEGER PRIMARY KEY,
    command TEXT,
    cpus INTEGER,
    mem_mb INTEGER,
    status TEXT,              -- PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    priority INTEGER,
    submit_time REAL,         -- Unix timestamp
    start_time REAL,
    end_time REAL,
    wait_time REAL,           -- start_time - submit_time
    runtime REAL,             -- end_time - start_time
    return_code INTEGER,
    user TEXT,
    stdout_path TEXT,
    stderr_path TEXT,
    cpu_user_time REAL,       -- From psutil
    cpu_system_time REAL
)
```

**Why SQLite?**
- File-based, no server needed
- ACID transactions
- Survives scheduler restarts
- Easy to query/analyze

### 5. Process Management

**Job Execution Flow:**
```python
1. Create log files (stdout, stderr)
2. Set resource limits (memory, CPU affinity)
3. Launch subprocess with Popen
4. Track process in memory (running dict)
5. Poll process for completion
6. On completion: calculate metrics, update DB, cleanup
```

**Process Isolation:**
- Each job runs in its own process group (`os.setsid()`)
- Enables future preemption (can kill process group)
- Logs captured separately

## Component Details

### MiniSlurm Class

**Responsibilities:**
- Job CRUD operations (submit, list, get, cancel)
- Scheduler loop execution
- Resource tracking
- Process lifecycle management

**Key Methods:**

1. `submit_job()`: Insert job into database
2. `scheduler_loop()`: Main scheduling loop
3. `_start_job()`: Launch subprocess, set limits
4. `_update_running_jobs()`: Check completion, update DB
5. `_get_pending_jobs()`: Fetch and sort pending jobs
6. `get_stats()`: Aggregate statistics

### Scheduler Loop

**Pseudocode:**
```python
while True:
    # 1. Check running jobs
    for job in running_jobs:
        if job.process.poll() is not None:  # Finished
            update_database(job)
            remove_from_running(job)
    
    # 2. Calculate available resources
    used_cpus = sum(job.cpus for job in running_jobs)
    used_mem = sum(job.mem_mb for job in running_jobs)
    available_cpus = total_cpus - used_cpus
    available_mem = total_mem_mb - used_mem
    
    # 3. Get pending jobs (sorted)
    pending = get_pending_jobs()  # Sorted by priority DESC, time ASC
    
    # 4. Schedule jobs
    for job in pending:
        if job.cpus <= available_cpus and job.mem_mb <= available_mem:
            start_job(job)
            available_cpus -= job.cpus
            available_mem -= job.mem_mb
    
    # 5. Sleep
    time.sleep(poll_interval)
```

**Why Polling?**
- Simple to implement
- Predictable behavior
- Easy to debug
- Trade-off: slight latency (1s default)

### CLI Layer

**Command Structure:**
```
mini-slurm <command> [args]
```

**Commands:**
- `submit`: Create job entry in DB
- `queue`: Query and display jobs
- `show`: Display single job details
- `cancel`: Update job status to CANCELLED
- `scheduler`: Run scheduler loop
- `stats`: Aggregate and display statistics

**Design Pattern:**
- Each command is a function (`cmd_<name>`)
- Uses `argparse` for argument parsing
- Commands are independent (can run without scheduler)

## Data Flow Examples

### Example 1: Job Submission

```
User: mini-slurm submit --cpus 2 --mem 4GB "python train.py"
  ↓
CLI: cmd_submit(args)
  ↓
MiniSlurm.submit_job(cpus=2, mem_mb=4096, command="python train.py")
  ↓
SQLite: INSERT INTO jobs (...) VALUES (...)
  ↓
Return: job_id = 1
  ↓
CLI: Print "Submitted job 1"
```

### Example 2: Job Execution

```
Scheduler Loop (every 1 second):
  ↓
Check: Job 1 is PENDING, resources available (2 CPUs, 4GB free)
  ↓
_start_job(job_id=1):
  - Create log files
  - Set memory limit (4GB)
  - Set CPU affinity
  - Launch: subprocess.Popen("python train.py")
  - Update DB: status = RUNNING, start_time = now
  - Add to running dict
  ↓
Next iteration:
  - Process still running → skip
  ↓
Later iteration:
  - Process.poll() returns 0 (success)
  - Calculate metrics
  - Update DB: status = COMPLETED, end_time = now, runtime = 120s
  - Remove from running dict
```

### Example 3: Priority Scheduling

```
Time 10:00:00 - Submit Job A (priority=0)
Time 10:00:05 - Submit Job B (priority=10)
Time 10:00:10 - Submit Job C (priority=5)

Scheduler fetches pending jobs:
  Sorted: [B(priority=10), C(priority=5), A(priority=0)]
  
If resources available:
  Start B first (highest priority)
  Then C
  Then A
```

## Concurrency Model

**Single-Threaded Scheduler:**
- One scheduler loop
- Sequential job checking
- No race conditions (single writer)

**Multi-Process Jobs:**
- Each job is separate process
- Jobs can run in parallel
- OS handles process scheduling

**Database Access:**
- SQLite handles concurrent reads
- Scheduler is single writer
- CLI commands are readers

## Error Handling

**Job Failures:**
- Return code != 0 → Status: FAILED
- Logs preserved for debugging
- Metrics still recorded

**Resource Limits:**
- Memory exceeded → OS kills process (SIGKILL)
- Detected on next poll → Status: FAILED

**Scheduler Errors:**
- Database errors → Logged, continue
- Process launch errors → Logged, job stays PENDING

## Performance Characteristics

**Latency:**
- Job submission: < 10ms (DB insert)
- Scheduling decision: < 100ms (DB query + sort)
- Poll interval: 1s (configurable)

**Throughput:**
- Limited by: CPU cores, memory, I/O
- Can run multiple jobs simultaneously
- No theoretical limit on queue size

**Scalability:**
- Single-node only (current)
- Database: Handles thousands of jobs
- Memory: ~1KB per job in running dict

## Security Considerations

**Current:**
- Jobs run as same user as scheduler
- No isolation between jobs
- Shell injection possible (shell=True)

**Future Improvements:**
- User isolation (run as different users)
- Container support (Docker/Kubernetes)
- Sandboxing (chroot, namespaces)
- Input sanitization

## Monitoring & Observability

**Current:**
- Logs: stdout/stderr per job
- Database: Historical job data
- CLI: Real-time queue view

**Future:**
- Metrics export (Prometheus)
- Web dashboard
- Alerting (queue depth, failures)
- Tracing (job execution timeline)

## Extension Points

**Easy Extensions:**
1. Add new job fields (database schema)
2. New CLI commands (add function + parser)
3. Different scheduling policies (modify `_get_pending_jobs`)

**Medium Extensions:**
1. GPU support (add resource tracking)
2. Job dependencies (add dependency checking)
3. Web API (add Flask/FastAPI layer)

**Hard Extensions:**
1. Multi-node (distributed scheduling)
2. Preemption (process suspension)
3. Checkpointing (save/restore state)

