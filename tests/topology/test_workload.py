#!/usr/bin/env python3
import time
import os
import sys

# Get job ID from environment
job_id = os.getenv("MINI_SLURM_JOB_ID", "unknown")
is_elastic = os.getenv("MINI_SLURM_ELASTIC", "0") == "1"
control_file = os.getenv("MINI_SLURM_CONTROL_FILE", "")

print(f"[Job {job_id}] Starting workload...")
print(f"[Job {job_id}] Elastic: {is_elastic}")

if is_elastic:
    print(f"[Job {job_id}] Control file: {control_file}")
    if control_file and os.path.exists(control_file):
        with open(control_file, 'r') as f:
            print(f"[Job {job_id}] Control file contents:")
            print(f.read())

# Simulate CPU-intensive work
duration = int(os.getenv("WORKLOAD_DURATION", "10"))
print(f"[Job {job_id}] Running for {duration} seconds...")

start_time = time.time()
iterations = 0
while time.time() - start_time < duration:
    # CPU-intensive computation
    result = sum(i * i for i in range(10000))
    iterations += 1
    if iterations % 1000 == 0:
        elapsed = time.time() - start_time
        print(f"[Job {job_id}] Iterations: {iterations}, Elapsed: {elapsed:.2f}s")
        
        # Check for elastic scaling updates
        if is_elastic and control_file and os.path.exists(control_file):
            with open(control_file, 'r') as f:
                content = f.read()
                if "SCALE_EVENT" in content:
                    print(f"[Job {job_id}] Detected scale event!")

print(f"[Job {job_id}] Completed after {iterations} iterations")
