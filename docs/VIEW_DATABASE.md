# Viewing the Mini-SLURM SQLite Database

## Database Location

The SQLite database is stored at:
```
~/.mini_slurm.db
```

Full path: `/Users/indu/.mini_slurm.db`

## Quick View Commands

### 1. View All Jobs (Formatted)
```bash
sqlite3 ~/.mini_slurm.db -header -column \
  "SELECT id, status, cpus, mem_mb, priority, 
   ROUND(wait_time, 2) as wait_s, 
   ROUND(runtime, 2) as runtime_s,
   datetime(submit_time, 'unixepoch') as submitted
   FROM jobs 
   ORDER BY id DESC 
   LIMIT 20;"
```

### 2. View Recent Jobs
```bash
sqlite3 ~/.mini_slurm.db -header -column \
  "SELECT id, command, status, cpus, mem_mb, priority
   FROM jobs 
   ORDER BY submit_time DESC 
   LIMIT 10;"
```

### 3. View Job Details (Single Job)
```bash
sqlite3 ~/.mini_slurm.db -header -column \
  "SELECT * FROM jobs WHERE id = 1;"
```

### 4. View Jobs by Status
```bash
# Pending jobs
sqlite3 ~/.mini_slurm.db -header -column \
  "SELECT * FROM jobs WHERE status = 'PENDING';"

# Running jobs
sqlite3 ~/.mini_slurm.db -header -column \
  "SELECT * FROM jobs WHERE status = 'RUNNING';"

# Completed jobs
sqlite3 ~/.mini_slurm.db -header -column \
  "SELECT * FROM jobs WHERE status = 'COMPLETED';"
```

### 5. Statistics Queries

**Job counts by status:**
```bash
sqlite3 ~/.mini_slurm.db \
  "SELECT status, COUNT(*) as count FROM jobs GROUP BY status;"
```

**Average wait time and runtime:**
```bash
sqlite3 ~/.mini_slurm.db \
  "SELECT 
     AVG(wait_time) as avg_wait_seconds,
     AVG(runtime) as avg_runtime_seconds,
     COUNT(*) as total_completed
   FROM jobs 
   WHERE status IN ('COMPLETED', 'FAILED') 
   AND wait_time IS NOT NULL;"
```

**Resource usage summary:**
```bash
sqlite3 ~/.mini_slurm.db -header -column \
  "SELECT 
     SUM(cpus) as total_cpus_requested,
     SUM(mem_mb) as total_mem_mb_requested,
     AVG(cpus) as avg_cpus_per_job,
     AVG(mem_mb) as avg_mem_mb_per_job
   FROM jobs 
   WHERE status = 'COMPLETED';"
```

**Jobs by user:**
```bash
sqlite3 ~/.mini_slurm.db -header -column \
  "SELECT user, COUNT(*) as job_count, 
   SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed
   FROM jobs 
   GROUP BY user;"
```

### 6. Interactive Mode

Open an interactive SQLite session:
```bash
sqlite3 ~/.mini_slurm.db
```

Then you can run queries:
```sql
-- List all tables
.tables

-- Show schema
.schema jobs

-- Run queries
SELECT * FROM jobs LIMIT 5;

-- Format output nicely
.mode column
.headers on
SELECT * FROM jobs LIMIT 5;

-- Exit
.quit
```

### 7. Export Data

**Export to CSV:**
```bash
sqlite3 ~/.mini_slurm.db -header -csv \
  "SELECT * FROM jobs;" > jobs_export.csv
```

**Export to JSON (requires sqlite3 with JSON support):**
```bash
sqlite3 ~/.mini_slurm.db \
  "SELECT json_group_array(
     json_object(
       'id', id,
       'status', status,
       'cpus', cpus,
       'mem_mb', mem_mb,
       'command', command
     )
   ) FROM jobs;" > jobs_export.json
```

## Database Schema

The `jobs` table has the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `command` | TEXT | Command to execute |
| `cpus` | INTEGER | CPUs requested |
| `mem_mb` | INTEGER | Memory requested (MB) |
| `status` | TEXT | PENDING, RUNNING, COMPLETED, FAILED, CANCELLED |
| `priority` | INTEGER | Job priority (higher = earlier) |
| `submit_time` | REAL | Unix timestamp when submitted |
| `start_time` | REAL | Unix timestamp when started |
| `end_time` | REAL | Unix timestamp when ended |
| `wait_time` | REAL | Seconds waited in queue |
| `runtime` | REAL | Seconds of execution time |
| `return_code` | INTEGER | Process exit code |
| `user` | TEXT | User who submitted job |
| `stdout_path` | TEXT | Path to stdout log file |
| `stderr_path` | TEXT | Path to stderr log file |
| `cpu_user_time` | REAL | CPU user time (from psutil) |
| `cpu_system_time` | REAL | CPU system time (from psutil) |

## Useful Queries

### Find longest running jobs
```sql
SELECT id, command, runtime, datetime(submit_time, 'unixepoch') as submitted
FROM jobs 
WHERE status = 'COMPLETED' AND runtime IS NOT NULL
ORDER BY runtime DESC 
LIMIT 10;
```

### Find jobs with longest wait times
```sql
SELECT id, command, wait_time, priority, datetime(submit_time, 'unixepoch') as submitted
FROM jobs 
WHERE wait_time IS NOT NULL
ORDER BY wait_time DESC 
LIMIT 10;
```

### Find failed jobs
```sql
SELECT id, command, return_code, datetime(submit_time, 'unixepoch') as submitted
FROM jobs 
WHERE status = 'FAILED'
ORDER BY submit_time DESC;
```

### Resource utilization over time
```sql
SELECT 
  date(datetime(submit_time, 'unixepoch')) as date,
  COUNT(*) as jobs_submitted,
  SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as jobs_completed,
  AVG(runtime) as avg_runtime
FROM jobs
GROUP BY date
ORDER BY date DESC;
```

### View log file paths
```sql
SELECT id, status, stdout_path, stderr_path 
FROM jobs 
WHERE stdout_path IS NOT NULL;
```

## Database Management

### Backup Database
```bash
cp ~/.mini_slurm.db ~/.mini_slurm.db.backup
```

### Reset Database (WARNING: Deletes all jobs!)
```bash
rm ~/.mini_slurm.db
# Database will be recreated on next job submission or scheduler start
```

### Check Database Size
```bash
ls -lh ~/.mini_slurm.db
```

### Vacuum Database (reclaim space)
```bash
sqlite3 ~/.mini_slurm.db "VACUUM;"
```

## GUI Tools

If you prefer a GUI, you can use:

1. **DB Browser for SQLite** (Free, cross-platform)
   - Download: https://sqlitebrowser.org/
   - Open: `~/.mini_slurm.db`

2. **TablePlus** (macOS, paid)
   - Download: https://tableplus.com/
   - Open SQLite connection to `~/.mini_slurm.db`

3. **VS Code Extension**
   - Install "SQLite Viewer" extension
   - Open `~/.mini_slurm.db` in VS Code

## Example: Full Job Analysis

```bash
sqlite3 ~/.mini_slurm.db -header -column <<EOF
SELECT 
  id,
  status,
  cpus,
  mem_mb,
  priority,
  ROUND(wait_time, 2) as wait_s,
  ROUND(runtime, 2) as runtime_s,
  return_code,
  datetime(submit_time, 'unixepoch') as submitted,
  datetime(start_time, 'unixepoch') as started,
  datetime(end_time, 'unixepoch') as ended,
  user,
  command
FROM jobs
ORDER BY id DESC
LIMIT 10;
EOF
```

