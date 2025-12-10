# Mini-SLURM: Complete Guide

## 🏗️ How It Works: Architecture & Flow

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Mini-SLURM System                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │   CLI Layer  │──────▶│  MiniSlurm   │                   │
│  │  (Commands)  │      │    Class     │                   │
│  └──────────────┘      └──────┬───────┘                   │
│                                │                            │
│                    ┌───────────┴───────────┐               │
│                    │                       │                │
│            ┌───────▼──────┐      ┌───────▼──────┐         │
│            │ SQLite DB    │      │  Scheduler    │         │
│            │ (Persistent) │      │    Loop       │         │
│            └──────────────┘      └───────┬───────┘         │
│                                          │                  │
│                                  ┌───────▼───────┐          │
│                                  │  Subprocess   │          │
│                                  │  Execution    │          │
│                                  └───────────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Job Submission** (`submit` command)
   ```
   User → CLI → submit_job() → SQLite INSERT → Returns Job ID
   ```

2. **Scheduler Loop** (runs continuously)
   ```
   Every poll_interval seconds:
   1. Check running jobs for completion → Update DB
   2. Calculate available resources (CPUs, Memory)
   3. Fetch pending jobs (sorted by priority DESC, submit_time ASC)
   4. Start jobs that fit in available resources
   5. Sleep and repeat
   ```

3. **Job Execution**
   ```
   _start_job() → 
     - Create log files
     - Set resource limits (CPU affinity, memory)
     - Launch subprocess
     - Track in running dict
     - Update DB status to RUNNING
   ```

4. **Job Completion**
   ```
   Process finishes →
     - Calculate metrics (runtime, CPU time)
     - Close log files
     - Update DB (status, end_time, metrics)
     - Remove from running dict
   ```

### Key Components

#### 1. **SQLite Database** (`~/.mini_slurm.db`)
- Stores all job metadata persistently
- Survives scheduler restarts
- Enables historical analysis

#### 2. **Scheduler Loop** (`scheduler_loop()`)
- Polls every second (configurable)
- Maintains `running` dict in memory for active jobs
- Implements priority + FIFO scheduling

#### 3. **Resource Management**
- **CPU**: Tracks used/available CPUs
- **Memory**: Tracks used/available memory
- **Enforcement**: Sets limits via `resource.setrlimit()` and CPU affinity

#### 4. **Process Management**
- Each job runs as a subprocess
- Logs captured to separate files
- Process group isolation for future preemption

---

## 🧪 How to Test Locally

### Step 1: Install Dependencies

```bash
cd mini-slurm
pip install psutil
```

### Step 2: Start the Scheduler

**Terminal 1** - Start the scheduler daemon:
```bash
mini-slurm scheduler
```

You should see:
```
[mini-slurm] Starting scheduler with 8 CPUs, 16384 MB memory
```

**Keep this terminal open** - the scheduler runs continuously.

### Step 3: Submit Test Jobs

**Terminal 2** - Submit jobs:

```bash
# Test 1: Simple job
mini-slurm submit --cpus 2 --mem 1GB "echo 'Hello Mini-SLURM!' && sleep 3"

# Test 2: High priority job (should run first)
mini-slurm submit --cpus 1 --mem 512MB --priority 10 "echo 'High priority' && sleep 2"

# Test 3: CPU-bound task
mini-slurm submit --cpus 4 --mem 2GB "python3 -c 'import time; [sum(range(100000)) for _ in range(10)]; print(\"Done\")'"
```

### Step 4: Monitor Jobs

```bash
# View all jobs
mini-slurm queue

# View only pending jobs
mini-slurm queue --status PENDING

# View job details
mini-slurm show 1

# View statistics
mini-slurm stats
```

### Step 5: Test Resource Constraints

```bash
# Submit a job that exceeds available resources (should stay pending)
mini-slurm submit --cpus 20 --mem 32GB "echo 'This will wait'"

# Check it's pending
mini-slurm queue --status PENDING

# Cancel it
mini-slurm cancel <job_id>
```

### Step 6: Verify Logs

```bash
# View job output
cat ~/.mini_slurm_logs/job_1.out
cat ~/.mini_slurm_logs/job_1.err
```

### Step 7: Test Priority Scheduling

```bash
# Submit jobs with different priorities
mini-slurm submit --cpus 2 --mem 1GB --priority 0 "sleep 5 && echo 'Low priority'"
mini-slurm submit --cpus 2 --mem 1GB --priority 5 "sleep 5 && echo 'Medium priority'"
mini-slurm submit --cpus 2 --mem 1GB --priority 10 "sleep 5 && echo 'High priority'"

# Watch the queue - high priority should run first
watch -n 1 'mini-slurm queue'
```

### Step 8: Clean Up

```bash
# Stop the scheduler (Ctrl+C in Terminal 1)
# Or kill it:
pkill -f "mini-slurm scheduler"

# Optional: Clear database and logs
rm ~/.mini_slurm.db
rm -rf ~/.mini_slurm_logs
```

---

## 🚀 Extending Mini-SLURM: Contributing Guide

Mini-SLURM is designed to be extensible. This section outlines potential extensions and how to implement them. These are great starting points for contributors who want to add new features.

### Extension Ideas

#### 1. **GPU Resource Management**

**Use Case**: Many AI/ML workloads require GPUs, not just CPUs. Adding GPU support would make Mini-SLURM more useful for GPU-accelerated workloads.

**Implementation**:
```python
# Add to database schema
ALTER TABLE jobs ADD COLUMN gpus INTEGER DEFAULT 0;

# Track GPU usage
self.used_gpus = sum(info["gpus"] for info in running.values())

# GPU scheduling logic
if gpus <= avail_gpus and cpus <= avail_cpus and mem_mb <= avail_mem:
    self._start_job(...)
```

**Benefits**:
- Enable multi-GPU training workflows
- Better resource tracking for GPU workloads
- Support GPU-accelerated ML experiments

---

#### 2. **Job Dependencies & Workflows**

**Use Case**: ML pipelines often have dependencies (e.g., preprocess → train → evaluate). Adding dependency support would enable automated pipeline execution.

**Implementation**:
```python
# Add dependency tracking
ALTER TABLE jobs ADD COLUMN depends_on TEXT;  -- JSON array of job IDs

def _can_start_job(self, job_id, depends_on):
    """Check if all dependencies are completed."""
    if not depends_on:
        return True
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(*) FROM jobs 
        WHERE id IN ({}) AND status NOT IN ('COMPLETED', 'FAILED')
    """.format(','.join('?' * len(depends_on))), depends_on)
    count = c.fetchone()[0]
    conn.close()
    return count == 0
```

**Benefits**:
- Automated ML pipeline execution
- Reduce manual job coordination
- Enable complex multi-step workflows

---

#### 3. **Fair-Share Scheduling**

**Use Case**: In multi-user environments, prevent one user from monopolizing resources. Fair-share scheduling adjusts priorities based on historical usage.

**Implementation**:
```python
# Track usage per user
class FairShareScheduler:
    def __init__(self):
        self.user_usage = defaultdict(float)  # user -> total CPU-hours
    
    def calculate_priority(self, job, base_priority):
        """Adjust priority based on fair-share."""
        user = job['user']
        usage = self.user_usage[user]
        # Lower usage = higher effective priority
        fair_share_boost = max(0, 100 - usage * 10)
        return base_priority + fair_share_boost
```

**Benefits**:
- Better resource sharing in multi-user environments
- Prevent resource hoarding
- More equitable scheduling

---

#### 4. **Backfill Scheduling**

**Use Case**: Small jobs often wait unnecessarily behind large jobs. Backfill scheduling fills gaps by running small jobs that fit in available resources without delaying high-priority jobs.

**Implementation**:
```python
def _backfill_schedule(self, pending_jobs, running_jobs):
    """Schedule small jobs in gaps."""
    # Find gaps in resource timeline
    # Schedule short jobs that fit in gaps
    # Don't delay high-priority jobs
    pass
```

**Benefits**:
- Better resource utilization
- Faster turnaround for small jobs
- Higher overall throughput

---

#### 5. **Resource Usage Tracking**

**Use Case**: Track detailed resource usage metrics for analysis and optimization.

**Implementation**:
```python
# Add usage tracking
ALTER TABLE jobs ADD COLUMN cpu_hours REAL;
ALTER TABLE jobs ADD COLUMN gpu_hours REAL;
ALTER TABLE jobs ADD COLUMN mem_gb_hours REAL;

def calculate_resource_usage(self, job):
    """Calculate resource usage based on resources used."""
    cpu_hours = job['cpus'] * (job['runtime'] / 3600)
    gpu_hours = job.get('gpus', 0) * (job['runtime'] / 3600)
    mem_gb_hours = (job['mem_mb'] / 1024) * (job['runtime'] / 3600)
    return cpu_hours, gpu_hours, mem_gb_hours
```

**Benefits**:
- Better understanding of resource consumption
- Identify optimization opportunities
- Track usage patterns over time

---

#### 6. **Job Preemption**

**Use Case**: Allow high-priority jobs to interrupt low-priority running jobs when resources are needed.

**Implementation**:
```python
def preempt_job(self, job_id):
    """Suspend a running job."""
    info = running[job_id]
    # Send SIGSTOP to suspend
    os.killpg(os.getpgid(info['proc'].pid), signal.SIGSTOP)
    # Save checkpoint if supported
    # Update status to PREEMPTED
```

**Benefits**:
- Better responsiveness for urgent jobs
- More flexible scheduling policies
- Support for advanced scheduling scenarios

---

#### 7. **Multi-Node Support**

**Use Case**: Scale beyond a single machine to support distributed workloads across multiple nodes.

**Implementation**:
```python
# Add node management
class Node:
    def __init__(self, hostname, cpus, mem_mb, gpus):
        self.hostname = hostname
        self.resources = {'cpus': cpus, 'mem_mb': mem_mb, 'gpus': gpus}
        self.available = self.resources.copy()

# Distributed scheduling
def schedule_across_nodes(self, job):
    """Find best node(s) for job."""
    # Network topology awareness
    # Data locality optimization
    # SSH-based job execution
    pass
```

**Benefits**:
- Scale to multi-machine clusters
- Support distributed training workloads
- Enable larger-scale experiments

---

#### 8. **Web UI Dashboard**

**Use Case**: Provide a web-based interface for job submission, monitoring, and management.

**Implementation**:
```python
# Add Flask/FastAPI web server
from flask import Flask, render_template, jsonify

@app.route('/api/jobs')
def get_jobs():
    ms = MiniSlurm()
    return jsonify(ms.list_jobs())

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
```

**Benefits**:
- Better user experience
- Visual monitoring and management
- Accessible to non-CLI users

---

#### 9. **Python SDK & Framework Integration**

**Use Case**: Provide a Python SDK for easier integration with ML frameworks and workflows.

**Implementation**:
```python
# Python SDK
from mini_slurm import MiniSlurmClient

client = MiniSlurmClient()
job = client.submit_training(
    script='train.py',
    cpus=4,
    gpus=1,
    mem='16GB',
    hyperparameters={'lr': 0.001}
)

# Wait for completion
job.wait()
results = job.get_results()
```

**Benefits**:
- Easier integration with ML workflows
- Better developer experience
- Framework-specific helpers

---

#### 10. **Observability & Monitoring**

**Use Case**: Add metrics export and monitoring capabilities for production use.

**Implementation**:
```python
# Add metrics export
from prometheus_client import Counter, Histogram

job_submissions = Counter('mini_slurm_jobs_submitted_total')
job_runtime = Histogram('mini_slurm_job_runtime_seconds')

# Export to Prometheus/Grafana
# Add alerting for:
# - Queue depth too high
# - Job failures
# - Resource exhaustion
```

**Benefits**:
- Production-ready monitoring
- Proactive issue detection
- Better observability

---

## 📊 Example: Adding GPU Support (Quick Start)

Here's a concrete example of how to extend the system:

```python
# 1. Update database schema
def init_db(db_path: str = DB_PATH):
    # ... existing code ...
    c.execute("ALTER TABLE jobs ADD COLUMN gpus INTEGER DEFAULT 0")

# 2. Update job submission
def submit_job(self, cpus, mem_mb, command, priority=0, gpus=0):
    c.execute("""
        INSERT INTO jobs (command, cpus, mem_mb, gpus, status, priority, submit_time, user)
        VALUES (?, ?, ?, ?, 'PENDING', ?, ?, ?)
    """, (command, cpus, mem_mb, gpus, priority, time.time(), current_user()))

# 3. Update scheduler
def scheduler_loop(self):
    # Track GPU usage
    used_gpus = sum(info.get("gpus", 0) for info in running.values())
    avail_gpus = self.total_gpus - used_gpus
    
    # Check GPU constraint
    if gpus <= avail_gpus and cpus <= avail_cpus and mem_mb <= avail_mem:
        self._start_job(...)

# 4. Update CLI
p_submit.add_argument("--gpus", type=int, default=0, help="GPUs required")
```

This demonstrates the extension pattern: **Database → Logic → CLI**.

---

## 🎯 Contributing Guidelines

When contributing new features:

1. **Start with the database schema** - Add necessary columns to track new resources or metadata
2. **Update core logic** - Modify the scheduler to handle the new feature
3. **Expose via CLI/API** - Add command-line arguments or API endpoints
4. **Add tests** - Write tests to verify the feature works correctly
5. **Update documentation** - Document the new feature in relevant docs

### Suggested Contribution Order

1. **GPU support** - High impact for ML workloads
2. **Job dependencies** - Enables real ML pipelines
3. **Web UI** - Improves accessibility
4. **Resource tracking** - Better observability
5. **Multi-node support** - Scales to clusters

Each extension follows the same pattern: extend database schema, update scheduling logic, expose via CLI/API, add tests, and document.

