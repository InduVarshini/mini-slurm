# Mini-SLURM Quick Start Guide

## 🚀 5-Minute Test

### Step 1: Install & Start
```bash
pip install psutil
python3 mini-slurm.py scheduler &
```

### Step 2: Submit Jobs
```bash
python3 mini-slurm.py submit --cpus 2 --mem 1GB "echo 'Hello!' && sleep 3"
python3 mini-slurm.py submit --cpus 1 --mem 512MB --priority 10 "echo 'High priority!'"
```

### Step 3: Monitor
```bash
python3 mini-slurm.py queue
python3 mini-slurm.py stats
python3 mini-slurm.py show 1
```

### Step 4: Run Automated Tests
```bash
./test_local.sh
```

## 📚 Documentation Files

- **README.md** - User documentation, installation, commands
- **docs/GUIDE.md** - Complete guide: how it works, testing, extensions
- **docs/ARCHITECTURE.md** - Deep technical dive into system design
- **docs/QUICK_START.md** - This file (quick reference)

## 🎯 Key Concepts

**What is Mini-SLURM?**
- Local job scheduler for AI/ML workloads
- Manages CPU and memory resources
- Schedules jobs by priority + FIFO
- Tracks job execution and metrics

**How does it work?**
1. Jobs submitted → Stored in SQLite database
2. Scheduler loop runs continuously
3. Checks for available resources
4. Starts jobs when resources available
5. Tracks completion and metrics

**Why use it?**
- Test scheduling policies locally
- Manage resource-intensive workloads
- Experiment with HPC concepts
- Foundation for production systems

## 🔧 Common Commands

```bash
# Submit
python3 mini-slurm.py submit --cpus 4 --mem 8GB --priority 5 "python train.py"

# Monitor
python3 mini-slurm.py queue
python3 mini-slurm.py queue --status PENDING
python3 mini-slurm.py stats

# Manage
python3 mini-slurm.py show <job_id>
python3 mini-slurm.py cancel <job_id>

# Scheduler
python3 mini-slurm.py scheduler --total-cpus 8 --total-mem 16GB
```

## 📊 Understanding Output

**Queue Output:**
```
ID  STAT      CPU  MEM(MB)  PRI  WAIT(s)  RUN(s)  SUBMIT              COMMAND
1   RUNNING   2    1024     5    0.3      2.1     2025-12-08 11:15:02  python train.py
```

- **ID**: Job identifier
- **STAT**: Status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
- **CPU/MEM**: Requested resources
- **PRI**: Priority (higher = scheduled first)
- **WAIT(s)**: Time waiting in queue
- **RUN(s)**: Execution time

**Stats Output:**
- System resource usage
- Job counts by status
- Average wait/runtime
- Performance metrics

## 🐛 Troubleshooting

**Scheduler not running?**
```bash
ps aux | grep "mini-slurm.py scheduler"
# If not found, start it:
python3 mini-slurm.py scheduler &
```

**Jobs stuck in PENDING?**
- Check if resources available: `python3 mini-slurm.py stats`
- Job may require more CPUs/memory than available
- Check scheduler logs (stderr)

**Database issues?**
```bash
# View database
sqlite3 ~/.mini_slurm.db "SELECT * FROM jobs;"

# Reset database (WARNING: deletes all jobs)
rm ~/.mini_slurm.db
```

**Logs location:**
```bash
ls ~/.mini_slurm_logs/
cat ~/.mini_slurm_logs/job_1.out
```

## 🎓 Learning Path

1. **Start Here**: Run `./tests/test_local.sh` to see it in action
2. **Read**: `docs/GUIDE.md` for comprehensive explanation
3. **Deep Dive**: `docs/ARCHITECTURE.md` for technical details
4. **Extend**: See extension ideas in `docs/GUIDE.md`

## 💡 Next Steps

- Experiment with different priority levels
- Submit multiple jobs and watch scheduling
- Try resource constraints (submit jobs exceeding capacity)
- Read extension ideas in `docs/GUIDE.md` for business value
- Modify scheduling policy in `mini-slurm.py`

## 📞 Quick Reference

**Files:**
- Code: `mini-slurm.py`
- Database: `~/.mini_slurm.db`
- Logs: `~/.mini_slurm_logs/`

**Key Functions:**
- `MiniSlurm.submit_job()` - Submit job
- `MiniSlurm.scheduler_loop()` - Main scheduler
- `MiniSlurm._start_job()` - Launch job
- `MiniSlurm._update_running_jobs()` - Check completion

**Database Schema:**
- `jobs` table: All job metadata
- Key fields: `id`, `status`, `cpus`, `mem_mb`, `priority`, `command`

