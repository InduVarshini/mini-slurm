#!/usr/bin/env python3
"""
Direct test of topology-aware scheduling with elastic workloads.
This test runs the scheduler in-process and verifies behavior.
"""

import os
import sys
import time
import threading
import subprocess
from pathlib import Path

# Import mini-slurm components
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from mini_slurm.core import MiniSlurm
from mini_slurm.database import get_conn

# Test topology config
TOPOLOGY_CONFIG = """TopologyPlugin=topology/tree
SwitchName=switch1 Nodes=node[1-4]
SwitchName=switch2 Nodes=node[5-8]
SwitchName=switch3 Nodes=node[9-12]
SwitchName=switch4 Nodes=node[13-16]
SwitchName=core1 Switches=switch[1-4]
"""

def test_topology():
    print("=" * 70)
    print("Topology-Aware Scheduling Test")
    print("=" * 70)
    print()
    
    # Create config file
    config_path = os.path.expanduser("~/.mini_slurm_test_topology.conf")
    with open(config_path, 'w') as f:
        f.write(TOPOLOGY_CONFIG)
    print(f"✓ Created topology config: {config_path}")
    
    # Initialize MiniSlurm
    ms = MiniSlurm(
        total_cpus=16,
        total_mem_mb=32 * 1024,
        topology_config_path=config_path
    )
    
    print(f"✓ Initialized MiniSlurm")
    print(f"  Topology enabled: {ms.topology.enabled}")
    print(f"  Nodes: {len(ms.topology.nodes)}")
    print(f"  Switches: {len(ms.topology.switches)}")
    print()
    
    # Test node distance
    print("Testing node distances:")
    print(f"  node1 -> node2: {ms.topology.get_node_distance('node1', 'node2')} (same switch, should be 0)")
    print(f"  node1 -> node5: {ms.topology.get_node_distance('node1', 'node5')} (different switches, same core, should be 2)")
    print(f"  node1 -> node9: {ms.topology.get_node_distance('node1', 'node9')} (different switches, same core, should be 2)")
    print()
    
    # Submit test jobs
    print("Submitting test jobs:")
    print("-" * 70)
    
    # Simple CPU workload
    workload_cmd = "python -c 'import time; [sum(i*i for i in range(10000)) for _ in range(5000)]; time.sleep(3)'"
    
    job1 = ms.submit_job(cpus=2, mem_mb=2048, command=workload_cmd, priority=5)
    print(f"✓ Job {job1}: Regular (2 CPUs)")
    
    job2 = ms.submit_job(cpus=4, mem_mb=4096, command=workload_cmd, priority=5, 
                         is_elastic=True, min_cpus=2, max_cpus=8)
    print(f"✓ Job {job2}: Elastic (4 CPUs, min=2, max=8)")
    
    job3 = ms.submit_job(cpus=4, mem_mb=4096, command=workload_cmd, priority=3)
    print(f"✓ Job {job3}: Regular (4 CPUs)")
    
    job4 = ms.submit_job(cpus=2, mem_mb=2048, command=workload_cmd, priority=4,
                         is_elastic=True, min_cpus=1, max_cpus=6)
    print(f"✓ Job {job4}: Elastic (2 CPUs, min=1, max=6)")
    print()
    
    # Run scheduler for 20 seconds
    print("Running scheduler for 20 seconds...")
    print("-" * 70)
    
    scheduler_thread = threading.Thread(
        target=ms.scheduler_loop,
        kwargs={
            'poll_interval': 0.5,
            'elastic_scale_threshold': 40.0,
            'enable_elastic_scaling': True
        },
        daemon=True
    )
    scheduler_thread.start()
    
    # Monitor jobs
    for i in range(4):
        time.sleep(5)
        print(f"\n[{5*(i+1)}s] Job Status:")
        
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT id, status, cpus, nodes, is_elastic, current_cpus
            FROM jobs WHERE id IN (?, ?, ?, ?)
            ORDER BY id
        """, (job1, job2, job3, job4))
        
        for job_id, status, cpus, nodes, is_elastic, current_cpus in c.fetchall():
            nodes_str = ""
            if nodes:
                try:
                    import json
                    nodes_list = json.loads(nodes)
                    nodes_str = f", Nodes={','.join(nodes_list)}"
                    
                    # Check topology
                    if len(nodes_list) > 1:
                        switches = set()
                        for node in nodes_list:
                            switch = ms.topology.node_to_switch.get(node)
                            if switch:
                                switches.add(switch)
                        nodes_str += f" [Switch: {','.join(sorted(switches))}]"
                        
                        # Max distance
                        max_dist = 0
                        for i, n1 in enumerate(nodes_list):
                            for n2 in nodes_list[i+1:]:
                                dist = ms.topology.get_node_distance(n1, n2)
                                max_dist = max(max_dist, dist)
                        nodes_str += f" [MaxDist: {max_dist}]"
                except:
                    pass
            
            elastic_str = f" (elastic: {current_cpus}/{cpus})" if is_elastic else ""
            print(f"  Job {job_id}: {status}, CPUs={cpus}{elastic_str}{nodes_str}")
        
        conn.close()
    
    print("\n" + "=" * 70)
    print("Final Results:")
    print("=" * 70)
    
    # Get final details
    conn = mini_slurm.get_conn()
    c = conn.cursor()
    for job_id in [job1, job2, job3, job4]:
        c.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = c.fetchone()
        if job and len(job) >= 23:
            (jid, cmd, cpus, mem, status, pri, st, start, end, wait, runtime,
             rc, user, stdout, stderr, cpu_u, cpu_s, elastic, min_c, max_c,
             curr_c, ctrl, nodes) = job[:23]
            
            print(f"\nJob {jid}:")
            print(f"  Status: {status}")
            print(f"  CPUs: {cpus}")
            if elastic:
                print(f"  Elastic: {curr_c}/{max_c} (min={min_c})")
            if nodes:
                try:
                    import json
                    nodes_list = json.loads(nodes) if isinstance(nodes, str) else nodes
                    print(f"  Nodes: {','.join(nodes_list)}")
                    
                    switches = set()
                    for node in nodes_list:
                        switch = ms.topology.node_to_switch.get(node)
                        if switch:
                            switches.add(switch)
                    print(f"  Switches: {','.join(sorted(switches))}")
                    
                    if len(nodes_list) > 1:
                        max_dist = 0
                        for i, n1 in enumerate(nodes_list):
                            for n2 in nodes_list[i+1:]:
                                dist = ms.topology.get_node_distance(n1, n2)
                                max_dist = max(max_dist, dist)
                        print(f"  Max Distance: {max_dist} {'✓' if max_dist == 0 else '⚠'}")
                except Exception as e:
                    print(f"  Nodes: {nodes} (error: {e})")
            if wait:
                print(f"  Wait: {wait:.2f}s")
            if runtime:
                print(f"  Runtime: {runtime:.2f}s")
    conn.close()
    
    # Cleanup
    print("\nCleaning up...")
    if os.path.exists(config_path):
        os.remove(config_path)
    print("✓ Test complete")

if __name__ == "__main__":
    test_topology()
