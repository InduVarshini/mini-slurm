#!/usr/bin/env python3
"""Test elastic job scaling behavior"""
import subprocess
import time
import os
import sys
import signal

# Clean up
print("=" * 60)
print("Testing Elastic Job Scaling")
print("=" * 60)

if os.path.exists(os.path.expanduser("~/.mini_slurm.db")):
    os.remove(os.path.expanduser("~/.mini_slurm.db"))
if os.path.exists(os.path.expanduser("~/.mini_slurm_logs")):
    import shutil
    shutil.rmtree(os.path.expanduser("~/.mini_slurm_logs"))

print("\n1. Submitting elastic training job (2-8 CPUs)...")
result = subprocess.run(
    ["mini-slurm", "submit", 
     "--elastic", "--cpus", "2", "--min-cpus", "2", "--max-cpus", "8", 
     "--mem", "4GB", "--priority", "5",
     "EPOCHS=5 python3 tasks/elastic_training.py"],
    capture_output=True,
    text=True
)
print(result.stdout)
job1_id = int(result.stdout.split("Submitted job ")[1].split()[0])
print(f"   Job ID: {job1_id}")

print("\n2. Starting scheduler in background...")
scheduler = subprocess.Popen(
    ["mini-slurm", "scheduler", 
     "--total-cpus", "8", "--total-mem", "16GB", "--elastic-threshold", "50.0"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

time.sleep(3)

print("\n3. Checking initial queue status...")
result = subprocess.run(["mini-slurm", "queue"], capture_output=True, text=True)
print(result.stdout)

print("\n4. Waiting 5 seconds for potential scale-up (cluster should be underutilized)...")
time.sleep(5)

print("\n5. Checking queue after scale-up period...")
result = subprocess.run(["mini-slurm", "queue"], capture_output=True, text=True)
print(result.stdout)

# Check control file
control_file = os.path.expanduser(f"~/.mini_slurm_logs/job_{job1_id}.control")
if os.path.exists(control_file):
    print(f"\n6. Control file contents:")
    with open(control_file, 'r') as f:
        print(f.read())

print("\n7. Submitting high-priority job to trigger scale-down...")
result = subprocess.run(
    ["mini-slurm", "submit", 
     "--cpus", "4", "--mem", "4GB", "--priority", "10",
     "EPOCHS=3 python3 tasks/train_neural_network.py"],
    capture_output=True,
    text=True
)
print(result.stdout)
job2_id = int(result.stdout.split("Submitted job ")[1].split()[0])

time.sleep(3)

print("\n8. Checking queue after high-priority job submission...")
result = subprocess.run(["mini-slurm", "queue"], capture_output=True, text=True)
print(result.stdout)

# Check scheduler logs for scaling events
print("\n9. Recent scheduler output (looking for scaling events):")
scheduler_output = ""
try:
    # Read available output
    import select
    if select.select([scheduler.stdout], [], [], 0.5)[0]:
        scheduler_output = scheduler.stdout.read(5000)
        if "Scale" in scheduler_output or "scale" in scheduler_output:
            lines = scheduler_output.split('\n')
            for line in lines[-10:]:
                if "scale" in line.lower() or "elastic" in line.lower():
                    print(f"   {line}")
        else:
            print("   (No scaling events in recent output)")
except:
    pass

print("\n10. Waiting for jobs to complete...")
for i in range(30):
    result = subprocess.run(["mini-slurm", "queue", "--status", "RUNNING"], 
                          capture_output=True, text=True)
    if "RUNNING" not in result.stdout:
        print("   All jobs completed!")
        break
    time.sleep(1)

# Stop scheduler
print("\n11. Stopping scheduler...")
scheduler.terminate()
scheduler.wait(timeout=2)

print("\n12. Final queue status:")
result = subprocess.run(["mini-slurm", "queue"], capture_output=True, text=True)
print(result.stdout)

print("\n" + "=" * 60)
print("Test completed!")
print("=" * 60)
