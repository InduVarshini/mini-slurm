#!/usr/bin/env python3
"""
Demo script showcasing mini-slurm features.
This script demonstrates various features without requiring a running scheduler.
"""

import sys
import os
import time
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mini_slurm import MiniSlurm, parse_mem

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def demo_submit_jobs():
    """Demonstrate job submission."""
    print_section("1. Job Submission")
    
    ms = MiniSlurm()
    
    # Submit a few example jobs
    jobs = [
        {"cpus": 2, "mem": "4GB", "priority": 0, "command": "python train.py --epochs 10"},
        {"cpus": 4, "mem": "8GB", "priority": 5, "command": "python hyperparameter_sweep.py"},
        {"cpus": 1, "mem": "2GB", "priority": 0, "command": "python preprocess_data.py"},
        {"cpus": 2, "mem": "4GB", "priority": 0, "command": "python train.py --epochs 20", "elastic": True},
    ]
    
    print("Submitting example jobs...\n")
    for i, job in enumerate(jobs, 1):
        is_elastic = job.get("elastic", False)
        job_id = ms.submit_job(
            cpus=job["cpus"],
            mem_mb=parse_mem(job["mem"]),
            command=job["command"],
            priority=job["priority"],
            is_elastic=is_elastic,
            min_cpus=job["cpus"] if is_elastic else None,
            max_cpus=8 if is_elastic else None
        )
        elastic_str = " [ELASTIC]" if is_elastic else ""
        print(f"✓ Submitted job {job_id}: {job['command']}{elastic_str}")
        print(f"  CPUs: {job['cpus']}, Memory: {job['mem']}, Priority: {job['priority']}")
    
    print(f"\n✓ Total jobs submitted: {len(jobs)}")

def demo_queue():
    """Demonstrate queue viewing."""
    print_section("2. Viewing Job Queue")
    
    ms = MiniSlurm()
    
    print("All jobs in queue:\n")
    print(f"{'ID':>4} {'STAT':>8} {'CPU':>3} {'MEM(MB)':>7} {'PRI':>3} {'WAIT(s)':>8} "
          f"{'RUN(s)':>8} {'ELASTIC':>8} {'SUBMIT':>19} COMMAND")
    print("-" * 100)
    
    rows = ms.list_jobs()
    for row in rows:
        if len(row) >= 15:
            (job_id, command, cpus, mem_mb, status, priority,
             submit_time, start_time, end_time, wait_time, runtime,
             is_elastic, min_cpus, max_cpus, current_cpus) = row
            elastic_str = ""
            if is_elastic:
                if current_cpus:
                    elastic_str = f"{current_cpus}/{max_cpus}"
                else:
                    elastic_str = f"{cpus}/{max_cpus}"
        else:
            (job_id, command, cpus, mem_mb, status, priority,
             submit_time, start_time, end_time, wait_time, runtime) = row[:11]
            elastic_str = ""
        
        from mini_slurm.utils import format_ts
        print(
            f"{job_id:>4} {status:>8} {cpus:>3} {mem_mb:>7} {priority:>3} "
            f"{(wait_time or 0):>8.1f} {(runtime or 0):>8.1f} "
            f"{elastic_str:>8} {format_ts(submit_time):>19} {command[:50]}"
        )

def demo_job_details():
    """Demonstrate viewing job details."""
    print_section("3. Viewing Job Details")
    
    ms = MiniSlurm()
    rows = ms.list_jobs()
    
    if rows:
        job_id = rows[0][0]
        print(f"Details for job {job_id}:\n")
        
        job = ms.get_job(job_id)
        if job:
            from mini_slurm.utils import format_ts
            import json
            
            # Handle different schema versions
            if len(job) >= 23:
                (job_id, command, cpus, mem_mb, status, priority,
                 submit_time, start_time, end_time, wait_time, runtime,
                 return_code, user, stdout_path, stderr_path,
                 cpu_user_time, cpu_system_time, is_elastic,
                 min_cpus, max_cpus, current_cpus, control_file, nodes) = job
            elif len(job) >= 22:
                (job_id, command, cpus, mem_mb, status, priority,
                 submit_time, start_time, end_time, wait_time, runtime,
                 return_code, user, stdout_path, stderr_path,
                 cpu_user_time, cpu_system_time, is_elastic,
                 min_cpus, max_cpus, current_cpus, control_file) = job
                nodes = None
            else:
                (job_id, command, cpus, mem_mb, status, priority,
                 submit_time, start_time, end_time, wait_time, runtime,
                 return_code, user, stdout_path, stderr_path,
                 cpu_user_time, cpu_system_time) = job[:17]
                is_elastic = False
                min_cpus = None
                max_cpus = None
                current_cpus = None
                control_file = None
                nodes = None
            
            print(f"Job {job_id}")
            print(f"  User:        {user}")
            print(f"  Status:      {status}")
            print(f"  Priority:    {priority}")
            print(f"  Command:     {command}")
            if is_elastic:
                print(f"  Type:        ELASTIC")
                print(f"  CPUs:        {cpus} (current: {current_cpus or cpus}, min: {min_cpus}, max: {max_cpus})")
            else:
                print(f"  CPUs:        {cpus}")
            print(f"  Mem (MB):    {mem_mb}")
            if nodes:
                try:
                    nodes_list = json.loads(nodes) if isinstance(nodes, str) else nodes
                    print(f"  Nodes:       {','.join(nodes_list)}")
                except:
                    pass
            print(f"  Submitted:   {format_ts(submit_time)}")
            print(f"  Started:     {format_ts(start_time)}")
            print(f"  Ended:       {format_ts(end_time)}")
            print(f"  Wait time:   {wait_time:.2f}s" if wait_time else "  Wait time:   -")
            print(f"  Runtime:     {runtime:.2f}s" if runtime else "  Runtime:     -")
            if return_code is not None:
                print(f"  Return code: {return_code}")
            print(f"  Stdout:      {stdout_path}")
            print(f"  Stderr:      {stderr_path}")

def demo_stats():
    """Demonstrate statistics viewing."""
    print_section("4. System Statistics")
    
    ms = MiniSlurm()
    stats = ms.get_stats()
    
    print("=" * 60)
    print("Mini-SLURM Statistics")
    print("=" * 60)
    print()
    
    print("System Resources:")
    print(f"  Total CPUs:     {stats['total_cpus']}")
    print(f"  Used CPUs:      {stats['used_cpus']} ({stats['used_cpus']/stats['total_cpus']*100:.1f}%)")
    print(f"  Available CPUs: {stats['total_cpus'] - stats['used_cpus']}")
    print(f"  Total Memory:   {stats['total_mem_mb']:.0f} MB ({stats['total_mem_mb']/1024:.1f} GB)")
    print(f"  Used Memory:    {stats['used_mem_mb']:.0f} MB ({stats['used_mem_mb']/stats['total_mem_mb']*100:.1f}%)")
    print(f"  Available Mem:  {stats['total_mem_mb'] - stats['used_mem_mb']:.0f} MB")
    if stats['cpu_percent'] is not None:
        print(f"  System CPU %:   {stats['cpu_percent']:.1f}%")
    if stats['mem_percent'] is not None:
        print(f"  System Mem %:   {stats['mem_percent']:.1f}%")
    print()
    
    print("Job Statistics:")
    print(f"  Total Jobs:     {stats['total_jobs']}")
    print(f"  Running:        {stats['running_count']}")
    print(f"  Pending:        {stats['pending_count']}")
    for status in ['COMPLETED', 'FAILED', 'CANCELLED']:
        count = stats['status_counts'].get(status, 0)
        if count > 0:
            print(f"  {status:12} {count}")
    print()
    
    if stats['completed_count'] > 0:
        print("Performance Metrics (completed jobs):")
        print(f"  Average Wait Time:  {stats['avg_wait_time']:.2f} seconds")
        print(f"  Average Runtime:    {stats['avg_runtime']:.2f} seconds")
        print()

def demo_cli_help():
    """Show CLI help output."""
    print_section("5. CLI Help")
    
    print("Command: mini-slurm --help\n")
    result = subprocess.run(
        ["python", "-m", "mini_slurm.cli", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    print(result.stdout)

def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("  MINI-SLURM FEATURE DEMONSTRATION")
    print("=" * 70)
    
    try:
        demo_submit_jobs()
        demo_queue()
        demo_job_details()
        demo_stats()
        demo_cli_help()
        
        print_section("Demo Complete")
        print("✓ All features demonstrated successfully!")
        print("\nTo see these features in action:")
        print("  1. Start scheduler: mini-slurm scheduler")
        print("  2. Submit jobs: mini-slurm submit --cpus 2 --mem 4GB <command>")
        print("  3. View queue: mini-slurm queue")
        print("  4. View stats: mini-slurm stats")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
