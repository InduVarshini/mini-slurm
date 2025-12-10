#!/usr/bin/env python3
"""Simple test script for elastic jobs"""
import subprocess
import time
import os
import sys

# Clean up
print("Cleaning up...")
if os.path.exists(os.path.expanduser("~/.mini_slurm.db")):
    os.remove(os.path.expanduser("~/.mini_slurm.db"))
if os.path.exists(os.path.expanduser("~/.mini_slurm_logs")):
    import shutil
    shutil.rmtree(os.path.expanduser("~/.mini_slurm_logs"))

print("\n1. Testing elastic job submission...")
result = subprocess.run(
    ["python3", "mini-slurm.py", "submit", 
     "--elastic", "--cpus", "2", "--min-cpus", "2", "--max-cpus", "4", 
     "--mem", "2GB", "--priority", "5",
     "sleep 10"],
    capture_output=True,
    text=True
)
print(result.stdout)
if result.returncode != 0:
    print("ERROR:", result.stderr)
    sys.exit(1)

print("\n2. Checking queue...")
result = subprocess.run(
    ["python3", "mini-slurm.py", "queue"],
    capture_output=True,
    text=True
)
print(result.stdout)
if "ELASTIC" not in result.stdout:
    print("ERROR: ELASTIC column not found in queue output")
    sys.exit(1)

# Extract job ID
job_id = None
for line in result.stdout.split('\n'):
    if 'PENDING' in line or 'RUNNING' in line:
        parts = line.split()
        if parts:
            try:
                job_id = int(parts[0])
                break
            except ValueError:
                pass

if job_id:
    print(f"\n3. Showing job {job_id} details...")
    result = subprocess.run(
        ["python3", "mini-slurm.py", "show", str(job_id)],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if "ELASTIC" not in result.stdout:
        print("ERROR: ELASTIC type not shown in job details")
        sys.exit(1)
    
    print("\n4. Starting scheduler for 3 seconds...")
    scheduler = subprocess.Popen(
        ["python3", "mini-slurm.py", "scheduler", 
         "--total-cpus", "8", "--total-mem", "16GB", "--elastic-threshold", "50.0"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    time.sleep(3)
    
    print("\n5. Checking queue after scheduler start...")
    result = subprocess.run(
        ["python3", "mini-slurm.py", "queue"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    
    # Stop scheduler
    scheduler.terminate()
    scheduler.wait(timeout=2)
    
    print("\n6. Checking for control file...")
    control_file = os.path.expanduser(f"~/.mini_slurm_logs/job_{job_id}.control")
    if os.path.exists(control_file):
        print(f"   Control file exists: {control_file}")
        with open(control_file, 'r') as f:
            print(f"   Contents:\n{f.read()}")
    else:
        print(f"   Control file not found (job may not have started): {control_file}")
    
    print("\n✅ All basic tests passed!")
