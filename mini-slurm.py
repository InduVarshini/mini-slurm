#!/usr/bin/env python3
import argparse
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
import shlex

# Optional: CPU usage logging
try:
    import psutil
except ImportError:  # psutil is optional
    psutil = None

DB_PATH = os.path.expanduser("~/.mini_slurm.db")
LOG_DIR = os.path.expanduser("~/.mini_slurm_logs")


# -------------------- DB SETUP -------------------- #

def init_db(db_path: str = DB_PATH):
    Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT NOT NULL,
            cpus INTEGER NOT NULL,
            mem_mb INTEGER NOT NULL,
            status TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 0,
            submit_time REAL NOT NULL,
            start_time REAL,
            end_time REAL,
            wait_time REAL,
            runtime REAL,
            return_code INTEGER,
            user TEXT,
            stdout_path TEXT,
            stderr_path TEXT,
            cpu_user_time REAL,
            cpu_system_time REAL
        )
        """
    )
    conn.commit()
    conn.close()


def get_conn():
    return sqlite3.connect(DB_PATH)


# -------------------- HELPERS -------------------- #

def parse_mem(mem_str: str) -> int:
    """
    Convert memory strings like '8GB', '1024MB', '2g', '512m' into MB.
    """
    s = mem_str.strip().upper()
    if s.endswith("GB") or s.endswith("G"):
        value = float(s.rstrip("GB").rstrip("G"))
        return int(value * 1024)
    if s.endswith("MB") or s.endswith("M"):
        value = float(s.rstrip("MB").rstrip("M"))
        return int(value)
    # bare number => MB
    return int(float(s))


def format_ts(ts: float | None) -> str:
    if ts is None:
        return "-"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def current_user() -> str:
    return os.getenv("USER") or os.getenv("USERNAME") or "unknown"


# -------------------- CORE MINI-SLURM CLASS -------------------- #

class MiniSlurm:
    def __init__(self, total_cpus: int | None = None, total_mem_mb: int | None = None):
        init_db()
        self.total_cpus = total_cpus or os.cpu_count() or 4
        # default to 16 GB for your Mac; override with CLI flag if needed
        self.total_mem_mb = total_mem_mb or (16 * 1024)

        Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

    # ---------- JOB SUBMISSION & QUERY ---------- #

    def submit_job(self, cpus: int, mem_mb: int, command: str, priority: int = 0) -> int:
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO jobs (command, cpus, mem_mb, status, priority,
                              submit_time, user)
            VALUES (?, ?, ?, 'PENDING', ?, ?, ?)
            """,
            (command, cpus, mem_mb, priority, time.time(), current_user()),
        )
        job_id = c.lastrowid
        conn.commit()
        conn.close()
        return job_id

    def list_jobs(self, status: str | None = None):
        conn = get_conn()
        c = conn.cursor()
        if status:
            c.execute(
                """
                SELECT id, command, cpus, mem_mb, status, priority,
                       submit_time, start_time, end_time, wait_time, runtime
                FROM jobs
                WHERE status = ?
                ORDER BY submit_time ASC
                """,
                (status,),
            )
        else:
            c.execute(
                """
                SELECT id, command, cpus, mem_mb, status, priority,
                       submit_time, start_time, end_time, wait_time, runtime
                FROM jobs
                ORDER BY submit_time ASC
                """
            )
        rows = c.fetchall()
        conn.close()
        return rows

    def get_job(self, job_id: int):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = c.fetchone()
        conn.close()
        return row

    def cancel_job(self, job_id: int) -> bool:
        """
        Mark a job as CANCELLED if still pending.
        (We don't kill running processes in v0; stretch feature.)
        """
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT status FROM jobs WHERE id = ?", (job_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return False
        status = row[0]
        if status not in ("PENDING",):
            conn.close()
            return False
        c.execute("UPDATE jobs SET status = 'CANCELLED' WHERE id = ?", (job_id,))
        conn.commit()
        conn.close()
        return True

    # ---------- SCHEDULER LOOP ---------- #

    def scheduler_loop(self, poll_interval: float = 1.0):
        """
        Main scheduler loop:
        - track running processes in memory
        - update DB on completion
        - schedule PENDING jobs when resources are available
        """
        print(
            f"[mini-slurm] Starting scheduler with "
            f"{self.total_cpus} CPUs, {self.total_mem_mb} MB memory"
        )

        # job_id -> {'proc': Popen, 'ps_proc': psutil.Process | None}
        running: dict[int, dict] = {}

        while True:
            # 1. Check running jobs for completion
            self._update_running_jobs(running)

            # 2. Compute available resources
            used_cpus = sum(info["cpus"] for info in running.values())
            used_mem = sum(info["mem_mb"] for info in running.values())
            avail_cpus = self.total_cpus - used_cpus
            avail_mem = self.total_mem_mb - used_mem

            # 3. Fetch pending jobs (priority desc, FIFO within priority)
            pending_jobs = self._get_pending_jobs()

            # 4. Try to start jobs while we have capacity
            for job in pending_jobs:
                job_id, command, cpus, mem_mb, priority = job
                if cpus <= avail_cpus and mem_mb <= avail_mem:
                    self._start_job(job_id, command, cpus, mem_mb, running)
                    avail_cpus -= cpus
                    avail_mem -= mem_mb

            time.sleep(poll_interval)

    def _get_pending_jobs(self):
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            """
            SELECT id, command, cpus, mem_mb, priority
            FROM jobs
            WHERE status = 'PENDING'
            ORDER BY priority DESC, submit_time ASC
            """
        )
        rows = c.fetchall()
        conn.close()
        return rows

    def _start_job(self, job_id: int, command: str, cpus: int, mem_mb: int, running: dict):
        """
        Start a job as a subprocess, update DB with start_time & log paths.
        """
        stdout_path = os.path.join(LOG_DIR, f"job_{job_id}.out")
        stderr_path = os.path.join(LOG_DIR, f"job_{job_id}.err")

        # open log files
        stdout_f = open(stdout_path, "wb")
        stderr_f = open(stderr_path, "wb")

        print(f"[mini-slurm] Starting job {job_id}: {command}")
        # Note: shell=True lets users pass "python train.py" comfortably
        proc = subprocess.Popen(
            command,
            shell=True,
            stdout=stdout_f,
            stderr=stderr_f,
            preexec_fn=os.setsid,  # own process group (for future preemption)
        )

        ps_proc = psutil.Process(proc.pid) if psutil is not None else None
        start_time = time.time()

        conn = get_conn()
        c = conn.cursor()
        submit_time = c.execute(
            "SELECT submit_time FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()[0]
        wait_time = start_time - submit_time
        c.execute(
            """
            UPDATE jobs
            SET status = 'RUNNING',
                start_time = ?,
                wait_time = ?,
                stdout_path = ?,
                stderr_path = ?
            WHERE id = ?
            """,
            (start_time, wait_time, stdout_path, stderr_path, job_id),
        )
        conn.commit()
        conn.close()

        running[job_id] = {
            "proc": proc,
            "ps_proc": ps_proc,
            "stdout_f": stdout_f,
            "stderr_f": stderr_f,
            "cpus": cpus,
            "mem_mb": mem_mb,
            "start_time": start_time,
        }

    def _update_running_jobs(self, running: dict):
        """
        For each running job, check if finished; if so, compute metrics and update DB.
        """
        finished_job_ids = []

        for job_id, info in list(running.items()):
            proc: subprocess.Popen = info["proc"]
            ret = proc.poll()
            if ret is None:
                continue  # still running

            # Process finished
            end_time = time.time()
            runtime = end_time - info["start_time"]
            cpu_user = cpu_system = None

            if psutil is not None and info["ps_proc"] is not None:
                try:
                    times = info["ps_proc"].cpu_times()
                    cpu_user = times.user
                    cpu_system = times.system
                except psutil.Error:
                    pass

            # Close log files
            info["stdout_f"].close()
            info["stderr_f"].close()

            conn = get_conn()
            c = conn.cursor()
            c.execute(
                """
                UPDATE jobs
                SET status = ?,
                    end_time = ?,
                    runtime = ?,
                    return_code = ?,
                    cpu_user_time = ?,
                    cpu_system_time = ?
                WHERE id = ?
                """,
                (
                    "COMPLETED" if ret == 0 else "FAILED",
                    end_time,
                    runtime,
                    ret,
                    cpu_user,
                    cpu_system,
                    job_id,
                ),
            )
            conn.commit()
            conn.close()

            print(
                f"[mini-slurm] Job {job_id} finished with rc={ret} "
                f"runtime={runtime:.2f}s"
            )
            finished_job_ids.append(job_id)

        # Remove finished jobs from running dict
        for job_id in finished_job_ids:
            running.pop(job_id, None)


# -------------------- CLI -------------------- #

def cmd_submit(args):
    ms = MiniSlurm()
    mem_mb = parse_mem(args.mem)
    command = " ".join(args.command)
    job_id = ms.submit_job(cpus=args.cpus, mem_mb=mem_mb, command=command, priority=args.priority)
    print(f"Submitted job {job_id}")
    print(f"  cpus={args.cpus}, mem={mem_mb}MB, priority={args.priority}")
    print(f"  command={command}")


def cmd_queue(args):
    ms = MiniSlurm()
    rows = ms.list_jobs(status=args.status)
    if not rows:
        print("No jobs found.")
        return
    print(f"{'ID':>4} {'STAT':>8} {'CPU':>3} {'MEM(MB)':>7} {'PRI':>3} {'WAIT(s)':>8} "
          f"{'RUN(s)':>8} {'SUBMIT':>19} COMMAND")
    for (
        job_id, command, cpus, mem_mb, status, priority,
        submit_time, start_time, end_time, wait_time, runtime
    ) in rows:
        print(
            f"{job_id:>4} {status:>8} {cpus:>3} {mem_mb:>7} {priority:>3} "
            f"{(wait_time or 0):>8.1f} {(runtime or 0):>8.1f} "
            f"{format_ts(submit_time):>19} {command}"
        )


def cmd_show(args):
    ms = MiniSlurm()
    job = ms.get_job(args.job_id)
    if not job:
        print(f"Job {args.job_id} not found")
        return

    (
        job_id,
        command,
        cpus,
        mem_mb,
        status,
        priority,
        submit_time,
        start_time,
        end_time,
        wait_time,
        runtime,
        return_code,
        user,
        stdout_path,
        stderr_path,
        cpu_user_time,
        cpu_system_time,
    ) = job

    print(f"Job {job_id}")
    print(f"  User:        {user}")
    print(f"  Status:      {status}")
    print(f"  Priority:    {priority}")
    print(f"  Command:     {command}")
    print(f"  CPUs:        {cpus}")
    print(f"  Mem (MB):    {mem_mb}")
    print(f"  Submitted:   {format_ts(submit_time)}")
    print(f"  Started:     {format_ts(start_time)}")
    print(f"  Ended:       {format_ts(end_time)}")
    print(f"  Wait time:   {wait_time:.2f}s" if wait_time else "  Wait time:   -")
    print(f"  Runtime:     {runtime:.2f}s" if runtime else "  Runtime:     -")
    print(f"  Return code: {return_code}")
    print(f"  Stdout:      {stdout_path}")
    print(f"  Stderr:      {stderr_path}")
    if cpu_user_time is not None:
        print(f"  CPU user:    {cpu_user_time:.2f}s")
    if cpu_system_time is not None:
        print(f"  CPU system:  {cpu_system_time:.2f}s")


def cmd_cancel(args):
    ms = MiniSlurm()
    ok = ms.cancel_job(args.job_id)
    if ok:
        print(f"Cancelled job {args.job_id}")
    else:
        print(f"Could not cancel job {args.job_id} "
              f"(maybe it is not PENDING or does not exist)")


def cmd_scheduler(args):
    ms = MiniSlurm(
        total_cpus=args.total_cpus,
        total_mem_mb=parse_mem(args.total_mem) if args.total_mem else None,
    )
    ms.scheduler_loop(poll_interval=args.poll_interval)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="mini-slurm",
        description="Mini-SLURM: a tiny local HPC-style job scheduler",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # submit
    p_submit = sub.add_parser("submit", help="Submit a job")
    p_submit.add_argument("--cpus", type=int, required=True, help="CPUs required")
    p_submit.add_argument("--mem", type=str, required=True, help="Memory (e.g. 8GB, 1024MB)")
    p_submit.add_argument("--priority", type=int, default=0, help="Job priority (higher = earlier)")
    p_submit.add_argument("command", nargs=argparse.REMAINDER, help="Command to run")
    p_submit.set_defaults(func=cmd_submit)

    # queue
    p_queue = sub.add_parser("queue", help="Show job queue")
    p_queue.add_argument("--status", choices=["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"],
                         help="Filter by status")
    p_queue.set_defaults(func=cmd_queue)

    # show
    p_show = sub.add_parser("show", help="Show job details")
    p_show.add_argument("job_id", type=int)
    p_show.set_defaults(func=cmd_show)

    # cancel
    p_cancel = sub.add_parser("cancel", help="Cancel a pending job")
    p_cancel.add_argument("job_id", type=int)
    p_cancel.set_defaults(func=cmd_cancel)

    # scheduler
    p_sched = sub.add_parser("scheduler", help="Run the scheduler loop")
    p_sched.add_argument("--total-cpus", type=int, help="Override detected total CPUs")
    p_sched.add_argument("--total-mem", type=str, help="Override total memory (e.g. 16GB)")
    p_sched.add_argument("--poll-interval", type=float, default=1.0, help="Scheduler poll interval (seconds)")
    p_sched.set_defaults(func=cmd_scheduler)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
