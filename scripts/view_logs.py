#!/usr/bin/env python3
"""Simple script to view job logs."""
import sys
import os
from pathlib import Path

log_dir = Path.home() / ".mini_slurm_logs"

if len(sys.argv) < 2:
    print("Usage: python3 view_logs.py <job_id> [out|err]")
    print("\nAvailable logs:")
    if log_dir.exists():
        for log_file in sorted(log_dir.glob("job_*.out")):
            job_id = log_file.stem.split("_")[1]
            size = log_file.stat().st_size
            print(f"  Job {job_id} ({size} bytes)")
    else:
        print("  No logs found")
    sys.exit(1)

job_id = sys.argv[1]
log_type = sys.argv[2] if len(sys.argv) > 2 else "out"

log_file = log_dir / f"job_{job_id}.{log_type}"

if not log_file.exists():
    print(f"Log file not found: {log_file}")
    sys.exit(1)

print(f"=== Job {job_id} ({log_type.upper()}) ===\n")
with open(log_file, 'r') as f:
    print(f.read())
