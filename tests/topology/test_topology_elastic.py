#!/usr/bin/env python3
"""
Test script for topology-aware scheduling with elastic AI workloads.
This script:
1. Creates a test topology configuration
2. Starts the scheduler in the background
3. Submits multiple jobs including elastic ones
4. Monitors job execution and node assignments
5. Verifies topology-aware scheduling behavior
"""

import os
import sys
import time
import subprocess
import signal
import tempfile
from pathlib import Path

# Add parent directory to path to import mini-slurm
sys.path.insert(0, str(Path(__file__).parent))

# Import from package
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from mini_slurm.core import MiniSlurm
parse_mem = mini_slurm_module.parse_mem
get_conn = mini_slurm_module.get_conn
import sqlite3

# Test configuration
TEST_TOPOLOGY_CONFIG = """
# Test Topology Configuration
TopologyPlugin=topology/tree

# Define 4 leaf switches with 4 nodes each (16 nodes total)
SwitchName=switch1 Nodes=node[1-4]
SwitchName=switch2 Nodes=node[5-8]
SwitchName=switch3 Nodes=node[9-12]
SwitchName=switch4 Nodes=node[13-16]

# Core switch connecting all leaf switches
SwitchName=core1 Switches=switch[1-4]
"""

def create_test_topology_config(config_path):
    """Create a test topology configuration file."""
    with open(config_path, 'w') as f:
        f.write(TEST_TOPOLOGY_CONFIG)
    print(f"✓ Created topology config at {config_path}")

def create_test_workload_script():
    """Create a simple CPU-intensive workload script for testing."""
    script_content = '''#!/usr/bin/env python3
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
'''
    
    script_path = Path(__file__).parent / "test_workload.py"
    with open(script_path, 'w') as f:
        f.write(script_content)
    os.chmod(script_path, 0o755)
    print(f"✓ Created test workload script at {script_path}")
    return script_path

def test_topology_aware_scheduling():
    """Test topology-aware scheduling with elastic workloads."""
    print("=" * 70)
    print("Testing Topology-Aware Scheduling with Elastic AI Workloads")
    print("=" * 70)
    print()
    
    # Setup
    config_path = os.path.expanduser("~/.mini_slurm_topology_test.conf")
    create_test_topology_config(config_path)
    workload_script = create_test_workload_script()
    
    # Initialize MiniSlurm with test topology
    ms = MiniSlurm(
        total_cpus=16,
        total_mem_mb=32 * 1024,  # 32GB
        topology_config_path=config_path
    )
    
    print(f"✓ Initialized MiniSlurm with topology")
    print(f"  Total CPUs: {ms.total_cpus}")
    print(f"  Total Memory: {ms.total_mem_mb} MB")
    print(f"  Topology enabled: {ms.topology.enabled}")
    print(f"  Number of nodes: {len(ms.topology.nodes)}")
    print(f"  Number of switches: {len(ms.topology.switches)}")
    print()
    
    # Verify topology structure
    if ms.topology.enabled:
        print("Topology Structure:")
        for switch_name, switch_info in ms.topology.switches.items():
            switch_type = switch_info['type']
            parent = switch_info.get('parent', 'None')
            children = switch_info.get('children', [])
            print(f"  {switch_name} ({switch_type}): parent={parent}, children={children}")
        print()
        
        # Show node-to-switch mapping
        print("Node-to-Switch Mapping (first 8 nodes):")
        for i, (node_name, switch_name) in enumerate(list(ms.topology.node_to_switch.items())[:8]):
            print(f"  {node_name} -> {switch_name}")
        print()
    
    # Test node distance calculation
    print("Testing Node Distance Calculation:")
    test_nodes = ['node1', 'node2', 'node5', 'node9']
    for i, node1 in enumerate(test_nodes):
        for node2 in test_nodes[i+1:]:
            distance = ms.topology.get_node_distance(node1, node2)
            print(f"  Distance({node1}, {node2}) = {distance}")
    print()
    
    # Submit test jobs
    print("Submitting Test Jobs:")
    print("-" * 70)
    
    # Job 1: Regular job requiring 2 CPUs (should get nodes on same switch)
    job1 = ms.submit_job(
        cpus=2,
        mem_mb=2048,
        command=f"python {workload_script}",
        priority=5
    )
    print(f"✓ Submitted Job {job1}: Regular job (2 CPUs, 2GB)")
    
    # Job 2: Elastic job starting with 4 CPUs
    job2 = ms.submit_job(
        cpus=4,
        mem_mb=4096,
        command=f"WORKLOAD_DURATION=15 python {workload_script}",
        priority=5,
        is_elastic=True,
        min_cpus=2,
        max_cpus=8
    )
    print(f"✓ Submitted Job {job2}: Elastic job (4 CPUs initial, min=2, max=8)")
    
    # Job 3: Regular job requiring 4 CPUs
    job3 = ms.submit_job(
        cpus=4,
        mem_mb=4096,
        command=f"WORKLOAD_DURATION=12 python {workload_script}",
        priority=3
    )
    print(f"✓ Submitted Job {job3}: Regular job (4 CPUs, 4GB)")
    
    # Job 4: Elastic job starting with 2 CPUs
    job4 = ms.submit_job(
        cpus=2,
        mem_mb=2048,
        command=f"WORKLOAD_DURATION=20 python {workload_script}",
        priority=4,
        is_elastic=True,
        min_cpus=1,
        max_cpus=6
    )
    print(f"✓ Submitted Job {job4}: Elastic job (2 CPUs initial, min=1, max=6)")
    
    print()
    print("Job Queue:")
    print("-" * 70)
    rows = ms.list_jobs()
    for row in rows:
        job_id, command, cpus, mem_mb, status, priority, submit_time, start_time, end_time, wait_time, runtime, is_elastic, min_cpus, max_cpus, current_cpus = row[:15]
        elastic_str = f" [ELASTIC: {current_cpus or cpus}/{max_cpus}]" if is_elastic else ""
        print(f"  Job {job_id}: {status}, CPUs={cpus}, Priority={priority}{elastic_str}")
    print()
    
    # Start scheduler in a separate process
    print("Starting scheduler (will run for 30 seconds)...")
    print("-" * 70)
    
    scheduler_proc = subprocess.Popen(
        [
            "mini-slurm", "scheduler",
            "--total-cpus", "16",
            "--total-mem", "32GB",
            "--topology-config", config_path,
            "--poll-interval", "0.5",
            "--elastic-threshold", "40.0"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Monitor for 30 seconds
    start_time = time.time()
    last_status_time = start_time
    
    try:
        while time.time() - start_time < 30:
            time.sleep(1)
            
            # Print status every 5 seconds
            if time.time() - last_status_time >= 5:
                elapsed = time.time() - start_time
                print(f"\n[{elapsed:.1f}s] Checking job status...")
                
                # Get job statuses
                conn = get_conn()
                c = conn.cursor()
                c.execute("""
                    SELECT id, status, cpus, nodes, is_elastic, current_cpus
                    FROM jobs
                    WHERE id IN (?, ?, ?, ?)
                    ORDER BY id
                """, (job1, job2, job3, job4))
                
                for job_id, status, cpus, nodes, is_elastic, current_cpus in c.fetchall():
                    nodes_str = ""
                    if nodes:
                        try:
                            import json
                            nodes_list = json.loads(nodes)
                            nodes_str = f", Nodes={','.join(nodes_list)}"
                        except:
                            pass
                    
                    elastic_str = f" (elastic: {current_cpus}/{cpus})" if is_elastic else ""
                    print(f"  Job {job_id}: {status}, CPUs={cpus}{elastic_str}{nodes_str}")
                
                conn.close()
                last_status_time = time.time()
        
        print("\n" + "=" * 70)
        print("Final Job Status:")
        print("=" * 70)
        
        # Get final job details
        conn = get_conn()
        c = conn.cursor()
        for job_id in [job1, job2, job3, job4]:
            c.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            job = c.fetchone()
            if job:
                if len(job) >= 23:
                    (job_id_val, command, cpus, mem_mb, status, priority,
                     submit_time, start_time, end_time, wait_time, runtime,
                     return_code, user, stdout_path, stderr_path,
                     cpu_user_time, cpu_system_time, is_elastic, min_cpus,
                     max_cpus, current_cpus, control_file, nodes) = job[:23]
                else:
                    continue
                
                print(f"\nJob {job_id_val}:")
                print(f"  Status: {status}")
                print(f"  CPUs: {cpus}")
                if is_elastic:
                    print(f"  Elastic: {current_cpus}/{max_cpus} (min={min_cpus})")
                if nodes:
                    try:
                        import json
                        nodes_list = json.loads(nodes) if isinstance(nodes, str) else nodes
                        print(f"  Nodes: {','.join(nodes_list)}")
                        
                        # Analyze topology
                        if len(nodes_list) > 1:
                            switches_used = set()
                            for node in nodes_list:
                                switch = ms.topology.node_to_switch.get(node)
                                if switch:
                                    switches_used.add(switch)
                            print(f"  Switches used: {','.join(sorted(switches_used))}")
                            
                            # Calculate max distance
                            max_dist = 0
                            for i, n1 in enumerate(nodes_list):
                                for n2 in nodes_list[i+1:]:
                                    dist = ms.topology.get_node_distance(n1, n2)
                                    max_dist = max(max_dist, dist)
                            print(f"  Max node distance: {max_dist}")
                    except Exception as e:
                        print(f"  Nodes: {nodes} (parse error: {e})")
                if wait_time:
                    print(f"  Wait time: {wait_time:.2f}s")
                if runtime:
                    print(f"  Runtime: {runtime:.2f}s")
        conn.close()
        
        print("\n" + "=" * 70)
        print("Test Summary:")
        print("=" * 70)
        
        # Check if topology-aware scheduling worked
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM jobs WHERE nodes IS NOT NULL AND status IN ('RUNNING', 'COMPLETED', 'FAILED')")
        jobs_with_nodes = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM jobs WHERE is_elastic = 1")
        elastic_jobs = c.fetchone()[0]
        conn.close()
        
        print(f"✓ Jobs with node assignments: {jobs_with_nodes}")
        print(f"✓ Elastic jobs submitted: {elastic_jobs}")
        print(f"✓ Topology configuration loaded: {ms.topology.enabled}")
        print()
        
        if ms.topology.enabled and jobs_with_nodes > 0:
            print("✓ Topology-aware scheduling appears to be working!")
        else:
            print("⚠ Topology-aware scheduling may not be active (check scheduler logs)")
        
    finally:
        # Cleanup
        print("\nCleaning up...")
        scheduler_proc.terminate()
        try:
            scheduler_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            scheduler_proc.kill()
        
        # Clean up test files
        if os.path.exists(config_path):
            os.remove(config_path)
            print(f"✓ Removed test topology config")
        
        print("✓ Test completed")

if __name__ == "__main__":
    test_topology_aware_scheduling()
