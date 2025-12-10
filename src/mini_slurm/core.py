"""Core MiniSlurm scheduler class and topology configuration."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
import resource
import platform
import json
import re
from typing import Dict, List, Set, Optional
from collections import defaultdict

# Optional: CPU usage logging
try:
    import psutil
except ImportError:  # psutil is optional
    psutil = None

from .database import init_db, get_conn
from .utils import current_user

LOG_DIR = os.path.expanduser("~/.mini_slurm_logs")
TOPOLOGY_CONFIG_PATH = os.path.expanduser("~/.mini_slurm_topology.conf")


class TopologyConfig:
    """
    Represents the network topology configuration.
    Similar to SLURM's topology plugin configuration.
    """
    def __init__(self):
        self.enabled = False
        self.switches: Dict[str, Dict] = {}  # switch_name -> {type, parent, children}
        self.node_to_switch: Dict[str, str] = {}  # node_name -> leaf_switch_name
        self.switch_hierarchy: Dict[str, List[str]] = defaultdict(list)  # parent -> [children]
        self.nodes: Dict[str, Dict] = {}  # node_name -> {cpus, mem_mb, switch}
    
    def load_from_file(self, config_path: str):
        """Load topology configuration from a file (similar to slurm.conf format)."""
        if not os.path.exists(config_path):
            return False
        
        self.enabled = True
        current_section = None
        
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'TopologyPlugin':
                        self.enabled = value.lower() in ('topology/tree', 'topology', 'yes', '1', 'true')
                    elif key.startswith('SwitchName='):
                        # Format: SwitchName=switch1 Nodes=node[1-4]
                        # or: SwitchName=switch1 Switches=switch[1-2]
                        match = re.match(r'SwitchName=(\S+)\s+(Nodes|Switches)=(.+)', line)
                        if match:
                            switch_name = match.group(1)
                            link_type = match.group(2)
                            targets = match.group(3)
                            
                            if switch_name not in self.switches:
                                self.switches[switch_name] = {'type': 'leaf', 'parent': None, 'children': []}
                            
                            # Parse node/switch ranges (e.g., "node[1-4]" or "switch[1-2]")
                            targets_list = self._parse_range(targets)
                            
                            if link_type == 'Nodes':
                                for target in targets_list:
                                    self.node_to_switch[target] = switch_name
                                    if target not in self.nodes:
                                        self.nodes[target] = {'switch': switch_name}
                            elif link_type == 'Switches':
                                # This is a parent switch
                                self.switches[switch_name]['type'] = 'core'
                                for child_switch in targets_list:
                                    if child_switch in self.switches:
                                        self.switches[child_switch]['parent'] = switch_name
                                        self.switches[switch_name]['children'].append(child_switch)
                                    else:
                                        # Create child switch if it doesn't exist
                                        self.switches[child_switch] = {
                                            'type': 'leaf',
                                            'parent': switch_name,
                                            'children': []
                                        }
                                        self.switches[switch_name]['children'].append(child_switch)
        
        return True
    
    def _parse_range(self, range_str: str) -> List[str]:
        """Parse range strings like 'node[1-4]' or 'switch[1-2]' into list of names."""
        result = []
        # Match patterns like "node[1-4]" or "node1,node2,node3"
        range_match = re.match(r'(\w+)\[(\d+)-(\d+)\]', range_str)
        if range_match:
            prefix = range_match.group(1)
            start = int(range_match.group(2))
            end = int(range_match.group(3))
            for i in range(start, end + 1):
                result.append(f"{prefix}{i}")
        else:
            # Comma-separated list
            result = [s.strip() for s in range_str.split(',')]
        return result
    
    def get_node_distance(self, node1: str, node2: str) -> int:
        """
        Calculate the distance between two nodes based on switch hierarchy.
        Returns: 0 = same leaf, 1 = same core, 2+ = different cores
        """
        if node1 == node2:
            return 0
        
        switch1 = self.node_to_switch.get(node1)
        switch2 = self.node_to_switch.get(node2)
        
        if not switch1 or not switch2:
            return 999  # Unknown distance
        
        if switch1 == switch2:
            return 0  # Same leaf switch
        
        # Find common ancestor
        path1 = self._get_switch_path(switch1)
        path2 = self._get_switch_path(switch2)
        
        # Find lowest common ancestor
        common_depth = 0
        for i, (s1, s2) in enumerate(zip(path1, path2)):
            if s1 == s2:
                common_depth = i + 1
            else:
                break
        
        # Distance is sum of hops from each node to LCA
        distance = (len(path1) - common_depth) + (len(path2) - common_depth)
        return distance
    
    def _get_switch_path(self, switch_name: str) -> List[str]:
        """Get the path from root to this switch."""
        path = []
        current = switch_name
        while current:
            path.insert(0, current)
            if current in self.switches and self.switches[current]['parent']:
                current = self.switches[current]['parent']
            else:
                break
        return path
    
    def find_best_nodes(self, num_nodes: int, cpus_per_node: int, 
                       mem_per_node: int, used_nodes: Set[str]) -> Optional[List[str]]:
        """
        Find the best set of nodes for a job, preferring nodes on the same leaf switch.
        Returns None if not enough nodes available.
        """
        available_nodes = []
        default_cpus = getattr(self, 'total_cpus_per_node', 1)
        default_mem = getattr(self, 'total_mem_per_node', 1024)
        for node_name, node_info in self.nodes.items():
            if node_name not in used_nodes:
                # Check if node has enough resources
                node_cpus = node_info.get('cpus', default_cpus)
                node_mem = node_info.get('mem_mb', default_mem)
                if node_cpus >= cpus_per_node and node_mem >= mem_per_node:
                    available_nodes.append(node_name)
        
        if len(available_nodes) < num_nodes:
            return None
        
        # Try to find nodes on the same leaf switch first
        switch_to_nodes = defaultdict(list)
        for node in available_nodes:
            switch = self.node_to_switch.get(node)
            if switch:
                switch_to_nodes[switch].append(node)
        
        # Find switches with enough nodes
        for switch, nodes in switch_to_nodes.items():
            if len(nodes) >= num_nodes:
                return nodes[:num_nodes]
        
        # If not possible, find nodes that minimize maximum distance
        # Use a greedy approach: start with one node, add closest nodes
        if available_nodes:
            selected = [available_nodes[0]]
            remaining = set(available_nodes[1:])
            
            while len(selected) < num_nodes and remaining:
                # Find the node closest to any selected node
                best_node = None
                best_distance = float('inf')
                
                for candidate in remaining:
                    min_dist_to_selected = min(
                        self.get_node_distance(candidate, sel) 
                        for sel in selected
                    )
                    if min_dist_to_selected < best_distance:
                        best_distance = min_dist_to_selected
                        best_node = candidate
                
                if best_node:
                    selected.append(best_node)
                    remaining.remove(best_node)
                else:
                    break
            
            if len(selected) == num_nodes:
                return selected
        
        return None


class MiniSlurm:
    def __init__(self, total_cpus: Optional[int] = None, total_mem_mb: Optional[int] = None,
                 topology_config_path: Optional[str] = None):
        init_db()
        self.total_cpus = total_cpus or os.cpu_count() or 4
        self.total_mem_mb = total_mem_mb or (16 * 1024)

        Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
        
        # Load topology configuration
        self.topology = TopologyConfig()
        config_path = topology_config_path or TOPOLOGY_CONFIG_PATH
        if os.path.exists(config_path):
            if self.topology.load_from_file(config_path):
                print(f"[mini-slurm] Topology-aware scheduling enabled (config: {config_path})")
                # Initialize node resources if not set
                if not self.topology.nodes:
                    self._initialize_default_nodes()
            else:
                print(f"[mini-slurm] Warning: Failed to load topology config from {config_path}")
        else:
            # Create default topology: treat CPUs as virtual nodes
            self._initialize_default_nodes()
    
    def _initialize_default_nodes(self):
        """Initialize default node topology if no config file exists."""
        # Create virtual nodes: each node = 1 CPU core
        # Group nodes into leaf switches (4 nodes per switch)
        nodes_per_switch = 4
        num_nodes = self.total_cpus
        num_switches = (num_nodes + nodes_per_switch - 1) // nodes_per_switch
        
        for i in range(num_nodes):
            node_name = f"node{i+1}"
            switch_name = f"switch{(i // nodes_per_switch) + 1}"
            self.topology.nodes[node_name] = {
                'cpus': 1,
                'mem_mb': self.total_mem_mb // num_nodes,
                'switch': switch_name
            }
            self.topology.node_to_switch[node_name] = switch_name
            
            if switch_name not in self.topology.switches:
                self.topology.switches[switch_name] = {
                    'type': 'leaf',
                    'parent': None,
                    'children': []
                }
        
        # If we have multiple switches, create a core switch
        if num_switches > 1:
            core_switch = "core1"
            self.topology.switches[core_switch] = {
                'type': 'core',
                'parent': None,
                'children': []
            }
            for i in range(num_switches):
                leaf_switch = f"switch{i+1}"
                if leaf_switch in self.topology.switches:
                    self.topology.switches[leaf_switch]['parent'] = core_switch
                    self.topology.switches[core_switch]['children'].append(leaf_switch)
        
        self.topology.total_cpus_per_node = 1
        self.topology.total_mem_per_node = self.total_mem_mb // num_nodes
        self.topology.enabled = True

    # ---------- JOB SUBMISSION & QUERY ---------- #

    def submit_job(self, cpus: int, mem_mb: int, command: str, priority: int = 0,
                   is_elastic: bool = False, min_cpus: Optional[int] = None,
                   max_cpus: Optional[int] = None) -> int:
        """
        Submit a job. For elastic jobs, cpus is the initial allocation.
        """
        if is_elastic:
            if min_cpus is None:
                min_cpus = cpus
            if max_cpus is None:
                max_cpus = self.total_cpus
            if min_cpus > max_cpus:
                raise ValueError(f"min_cpus ({min_cpus}) > max_cpus ({max_cpus})")
            if cpus < min_cpus or cpus > max_cpus:
                raise ValueError(f"Initial cpus ({cpus}) must be between min ({min_cpus}) and max ({max_cpus})")
        
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO jobs (command, cpus, mem_mb, status, priority,
                              submit_time, user, is_elastic, min_cpus, max_cpus, current_cpus)
            VALUES (:command, :cpus, :mem_mb, 'PENDING', :priority, :submit_time, :user,
                    :is_elastic, :min_cpus, :max_cpus, :current_cpus)
            """,
            {
                'command': command,
                'cpus': cpus,
                'mem_mb': mem_mb,
                'priority': priority,
                'submit_time': time.time(),
                'user': current_user(),
                'is_elastic': 1 if is_elastic else 0,
                'min_cpus': min_cpus,
                'max_cpus': max_cpus,
                'current_cpus': cpus if is_elastic else None,
            },
        )
        job_id = c.lastrowid
        conn.commit()
        conn.close()
        return job_id

    def list_jobs(self, status: Optional[str] = None):
        conn = get_conn()
        c = conn.cursor()
        if status:
            c.execute(
                """
                SELECT id, command, cpus, mem_mb, status, priority,
                       submit_time, start_time, end_time, wait_time, runtime,
                       is_elastic, min_cpus, max_cpus, current_cpus
                FROM jobs
                WHERE status = :status
                ORDER BY submit_time ASC
                """,
                {'status': status},
            )
        else:
            c.execute(
                """
                SELECT id, command, cpus, mem_mb, status, priority,
                       submit_time, start_time, end_time, wait_time, runtime,
                       is_elastic, min_cpus, max_cpus, current_cpus
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
        c.execute("SELECT * FROM jobs WHERE id = :job_id", {'job_id': job_id})
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
        c.execute("SELECT status FROM jobs WHERE id = :job_id", {'job_id': job_id})
        row = c.fetchone()
        if not row:
            conn.close()
            return False
        status = row[0]
        if status not in ("PENDING",):
            conn.close()
            return False
        c.execute("UPDATE jobs SET status = 'CANCELLED' WHERE id = :job_id", {'job_id': job_id})
        conn.commit()
        conn.close()
        return True

    def get_stats(self):
        """
        Get system statistics and job metrics.
        """
        conn = get_conn()
        c = conn.cursor()
        
        # Get job counts by status
        c.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
        status_counts = dict(c.fetchall())
        
        # Get total jobs
        c.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = c.fetchone()[0]
        
        # Get running jobs
        c.execute("SELECT COUNT(*) FROM jobs WHERE status = 'RUNNING'")
        running_count = c.fetchone()[0]
        
        # Get pending jobs
        c.execute("SELECT COUNT(*) FROM jobs WHERE status = 'PENDING'")
        pending_count = c.fetchone()[0]
        
        # Get resource usage from running jobs
        c.execute("SELECT SUM(cpus), SUM(mem_mb) FROM jobs WHERE status = 'RUNNING'")
        running_resources = c.fetchone()
        used_cpus = running_resources[0] or 0
        used_mem_mb = running_resources[1] or 0
        
        # Get average wait time and runtime for completed jobs
        c.execute("""
            SELECT AVG(wait_time), AVG(runtime), COUNT(*)
            FROM jobs
            WHERE status IN ('COMPLETED', 'FAILED') AND wait_time IS NOT NULL AND runtime IS NOT NULL
        """)
        avg_stats = c.fetchone()
        avg_wait_time = avg_stats[0] if avg_stats[0] else 0
        avg_runtime = avg_stats[1] if avg_stats[1] else 0
        completed_count = avg_stats[2] or 0
        
        # Get system info
        if psutil:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            mem_percent = mem.percent
            mem_total_mb = mem.total / (1024 * 1024)
            mem_available_mb = mem.available / (1024 * 1024)
        else:
            cpu_percent = None
            mem_percent = None
            mem_total_mb = None
            mem_available_mb = None
        
        conn.close()
        
        return {
            'total_jobs': total_jobs,
            'status_counts': status_counts,
            'running_count': running_count,
            'pending_count': pending_count,
            'used_cpus': used_cpus,
            'used_mem_mb': used_mem_mb,
            'total_cpus': self.total_cpus,
            'total_mem_mb': self.total_mem_mb,
            'avg_wait_time': avg_wait_time,
            'avg_runtime': avg_runtime,
            'completed_count': completed_count,
            'cpu_percent': cpu_percent,
            'mem_percent': mem_percent,
            'mem_total_mb': mem_total_mb,
            'mem_available_mb': mem_available_mb,
        }

    # ---------- SCHEDULER LOOP ---------- #

    def scheduler_loop(self, poll_interval: float = 1.0, 
                      elastic_scale_threshold: float = 50.0,
                      enable_elastic_scaling: bool = True):
        """
        Main scheduler loop:
        - track running processes in memory
        - update DB on completion
        - schedule PENDING jobs when resources are available
        - scale elastic jobs up/down based on cluster utilization
        """
        print(
            f"[mini-slurm] Starting scheduler with "
            f"{self.total_cpus} CPUs, {self.total_mem_mb} MB memory"
        )
        if enable_elastic_scaling:
            print(f"[mini-slurm] Elastic scaling enabled (threshold: {elastic_scale_threshold}% utilization)")

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

            # 3. Elastic job scaling (before scheduling new jobs)
            if enable_elastic_scaling:
                self._scale_elastic_jobs(running, avail_cpus, elastic_scale_threshold)

            # Recompute resources after scaling
            used_cpus = sum(info["cpus"] for info in running.values())
            used_mem = sum(info["mem_mb"] for info in running.values())
            avail_cpus = self.total_cpus - used_cpus
            avail_mem = self.total_mem_mb - used_mem

            # 4. Fetch pending jobs (priority desc, FIFO within priority)
            pending_jobs = self._get_pending_jobs()

            # 5. Try to start jobs while we have capacity (with topology awareness)
            used_nodes = self._get_used_nodes(running)
            for job in pending_jobs:
                job_id, command, cpus, mem_mb, priority, is_elastic, min_cpus, max_cpus = job
                if cpus <= avail_cpus and mem_mb <= avail_mem:
                    # Use topology-aware node selection if enabled
                    selected_nodes = None
                    if self.topology.enabled and self.topology.nodes:
                        # Calculate how many nodes we need
                        # For simplicity, assume each node has equal CPUs
                        # In a real system, this would be more sophisticated
                        cpus_per_node = getattr(self.topology, 'total_cpus_per_node', 1)
                        mem_per_node = getattr(self.topology, 'total_mem_per_node', self.total_mem_mb // max(len(self.topology.nodes), 1))
                        num_nodes = (cpus + cpus_per_node - 1) // cpus_per_node
                        
                        selected_nodes = self.topology.find_best_nodes(
                            num_nodes, cpus_per_node, mem_per_node, used_nodes
                        )
                        
                        # If topology selection failed, fall back to simple scheduling
                        if selected_nodes is None:
                            # Not enough nodes available, skip this job
                            continue
                    else:
                        # Non-topology mode: just check resource availability
                        pass
                    
                    self._start_job(job_id, command, cpus, mem_mb, running, 
                                   is_elastic=bool(is_elastic), min_cpus=min_cpus, max_cpus=max_cpus,
                                   nodes=selected_nodes)
                    avail_cpus -= cpus
                    avail_mem -= mem_mb
                    if selected_nodes:
                        used_nodes.update(selected_nodes)

            time.sleep(poll_interval)

    def _get_pending_jobs(self):
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            """
            SELECT id, command, cpus, mem_mb, priority, is_elastic, min_cpus, max_cpus
            FROM jobs
            WHERE status = 'PENDING'
            ORDER BY priority DESC, submit_time ASC
            """
        )
        rows = c.fetchall()
        conn.close()
        return rows
    
    def _get_running_elastic_jobs(self):
        """Get all running elastic jobs with their current resource allocation."""
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            """
            SELECT id, current_cpus, min_cpus, max_cpus, priority, control_file
            FROM jobs
            WHERE status = 'RUNNING' AND is_elastic = 1
            ORDER BY priority ASC, submit_time ASC
            """
        )
        rows = c.fetchall()
        conn.close()
        return rows
    
    def _update_job_cpus(self, job_id: int, new_cpus: int):
        """Update the CPU allocation for a running elastic job."""
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            """
            UPDATE jobs
            SET current_cpus = :new_cpus, cpus = :new_cpus
            WHERE id = :job_id
            """,
            {'job_id': job_id, 'new_cpus': new_cpus}
        )
        conn.commit()
        conn.close()
    
    def _get_used_nodes(self, running: dict) -> Set[str]:
        """Get set of nodes currently used by running jobs."""
        used_nodes = set()
        conn = get_conn()
        c = conn.cursor()
        for job_id in running.keys():
            c.execute("SELECT nodes FROM jobs WHERE id = :job_id", {'job_id': job_id})
            row = c.fetchone()
            if row and row[0]:
                try:
                    nodes_list = json.loads(row[0])
                    used_nodes.update(nodes_list)
                except (json.JSONDecodeError, TypeError):
                    pass
        conn.close()
        return used_nodes
    
    def _get_cluster_utilization(self, used_cpus: int, used_mem: int) -> dict:
        """Calculate cluster utilization metrics."""
        cpu_util = (used_cpus / self.total_cpus) * 100 if self.total_cpus > 0 else 0
        mem_util = (used_mem / self.total_mem_mb) * 100 if self.total_mem_mb > 0 else 0
        overall_util = (cpu_util + mem_util) / 2
        
        return {
            'cpu_utilization': cpu_util,
            'mem_utilization': mem_util,
            'overall_utilization': overall_util,
            'available_cpus': self.total_cpus - used_cpus,
            'available_mem_mb': self.total_mem_mb - used_mem,
        }

    def _start_job(self, job_id: int, command: str, cpus: int, mem_mb: int, running: dict,
                   is_elastic: bool = False, min_cpus: Optional[int] = None, max_cpus: Optional[int] = None,
                   nodes: Optional[List[str]] = None):
        """
        Start a job as a subprocess, update DB with start_time & log paths.
        Enforces CPU affinity and memory limits.
        For elastic jobs, creates a control file for resource updates.
        """
        stdout_path = os.path.join(LOG_DIR, f"job_{job_id}.out")
        stderr_path = os.path.join(LOG_DIR, f"job_{job_id}.err")
        control_file = None
        
        if is_elastic:
            control_file = os.path.join(LOG_DIR, f"job_{job_id}.control")
            # Create control file with initial resource allocation
            with open(control_file, 'w') as f:
                f.write(f"CPUS={cpus}\n")
                f.write(f"MEM_MB={mem_mb}\n")
                f.write(f"MIN_CPUS={min_cpus}\n")
                f.write(f"MAX_CPUS={max_cpus}\n")
                f.write(f"STATUS=RUNNING\n")

        # open log files
        stdout_f = open(stdout_path, "wb")
        stderr_f = open(stderr_path, "wb")

        def preexec_fn():
            """Set up resource limits before exec."""
            # Set memory limit (RSS) in bytes
            mem_bytes = mem_mb * 1024 * 1024
            try:
                # Set soft limit (will raise SIGXCPU if exceeded)
                resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
            except (ValueError, OSError) as e:
                # On macOS, RLIMIT_AS may not work; log but continue
                print(f"[mini-slurm] Warning: Could not set memory limit: {e}", file=sys.stderr)
            
            # Create new process group
            os.setsid()

        elastic_str = " [ELASTIC]" if is_elastic else ""
        nodes_str = f" nodes={','.join(nodes)}" if nodes else ""
        print(f"[mini-slurm] Starting job {job_id}: {command} (CPUs={cpus}, Mem={mem_mb}MB){nodes_str}{elastic_str}")
        
        # Build command with CPU affinity if possible
        cmd_to_run = command
        env = os.environ.copy()
        
        # Set environment variables for elastic jobs
        if is_elastic:
            env["MINI_SLURM_ELASTIC"] = "1"
            env["MINI_SLURM_JOB_ID"] = str(job_id)
            env["MINI_SLURM_CONTROL_FILE"] = control_file
            env["MINI_SLURM_CURRENT_CPUS"] = str(cpus)
            env["MINI_SLURM_MIN_CPUS"] = str(min_cpus)
            env["MINI_SLURM_MAX_CPUS"] = str(max_cpus)
        
        # Set CPU affinity based on topology or simple allocation
        if cpus < self.total_cpus:
            cpu_list = None
            if nodes and self.topology.enabled:
                # Map nodes to CPU indices
                # In a real system, nodes would have specific CPU ranges
                # For now, map node names to CPU indices
                cpu_indices = []
                for node_name in nodes:
                    # Extract node number (e.g., "node1" -> 0, "node2" -> 1)
                    match = re.match(r'node(\d+)', node_name)
                    if match:
                        node_num = int(match.group(1)) - 1
                        cpus_per_node = self.topology.total_cpus_per_node if hasattr(self.topology, 'total_cpus_per_node') else 1
                        for i in range(cpus_per_node):
                            cpu_idx = node_num * cpus_per_node + i
                            if cpu_idx < self.total_cpus:
                                cpu_indices.append(cpu_idx)
                if cpu_indices:
                    cpu_list = cpu_indices[:cpus]  # Limit to requested CPUs
            else:
                # Simple allocation: use first N CPUs
                cpu_list = list(range(cpus))
            
            if cpu_list:
                if platform.system() == "Linux":
                    cpu_str = ",".join(str(i) for i in cpu_list)
                    cmd_to_run = f"taskset -c {cpu_str} {command}"
                elif platform.system() == "Darwin":
                    # macOS: set CPU count via environment variables for common libraries
                    env["OMP_NUM_THREADS"] = str(len(cpu_list))
                    env["MKL_NUM_THREADS"] = str(len(cpu_list))
                    env["NUMEXPR_NUM_THREADS"] = str(len(cpu_list))
        
        # Note: shell=True lets users pass "python train.py" comfortably
        proc = subprocess.Popen(
            cmd_to_run,
            shell=True,
            stdout=stdout_f,
            stderr=stderr_f,
            preexec_fn=preexec_fn,
            env=env,
        )

        ps_proc = psutil.Process(proc.pid) if psutil is not None else None
        start_time = time.time()

        conn = get_conn()
        c = conn.cursor()
        submit_time = c.execute(
            "SELECT submit_time FROM jobs WHERE id = :job_id", {'job_id': job_id}
        ).fetchone()[0]
        wait_time = start_time - submit_time
        nodes_json = json.dumps(nodes) if nodes else None
        c.execute(
            """
            UPDATE jobs
            SET status = 'RUNNING',
                start_time = :start_time,
                wait_time = :wait_time,
                stdout_path = :stdout_path,
                stderr_path = :stderr_path,
                control_file = :control_file,
                current_cpus = :current_cpus,
                nodes = :nodes
            WHERE id = :job_id
            """,
            {
                'start_time': start_time,
                'wait_time': wait_time,
                'stdout_path': stdout_path,
                'stderr_path': stderr_path,
                'control_file': control_file,
                'current_cpus': cpus if is_elastic else None,
                'nodes': nodes_json,
                'job_id': job_id,
            },
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
            "is_elastic": is_elastic,
            "min_cpus": min_cpus,
            "max_cpus": max_cpus,
            "control_file": control_file,
            "nodes": nodes,
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
                SET status = :status,
                    end_time = :end_time,
                    runtime = :runtime,
                    return_code = :return_code,
                    cpu_user_time = :cpu_user_time,
                    cpu_system_time = :cpu_system_time
                WHERE id = :job_id
                """,
                {
                    'status': "COMPLETED" if ret == 0 else "FAILED",
                    'end_time': end_time,
                    'runtime': runtime,
                    'return_code': ret,
                    'cpu_user_time': cpu_user,
                    'cpu_system_time': cpu_system,
                    'job_id': job_id,
                },
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
            info = running.pop(job_id, None)
            # Clean up control file for elastic jobs
            if info and info.get("control_file") and os.path.exists(info["control_file"]):
                try:
                    os.remove(info["control_file"])
                except OSError:
                    pass
    
    def _scale_elastic_jobs(self, running: dict, avail_cpus: int, scale_threshold: float):
        """
        Scale elastic jobs based on cluster utilization and available resources.
        
        Policies:
        1. Scale UP: If cluster utilization < threshold and resources available
        2. Scale DOWN: If high-priority jobs need resources (preemption)
        """
        if avail_cpus <= 0:
            return
        
        # Get cluster utilization
        used_cpus = sum(info["cpus"] for info in running.values())
        util = self._get_cluster_utilization(used_cpus, sum(info["mem_mb"] for info in running.values()))
        
        # Get running elastic jobs sorted by priority (low priority first for scale-down)
        elastic_jobs = self._get_running_elastic_jobs()
        
        # Scale UP: If utilization is low, give more resources to elastic jobs
        if util['overall_utilization'] < scale_threshold and avail_cpus > 0:
            for job_id, current_cpus, min_cpus, max_cpus, priority, control_file in elastic_jobs:
                if job_id not in running:
                    continue
                
                if current_cpus < max_cpus and avail_cpus > 0:
                    # Calculate how many CPUs we can add
                    cpus_to_add = min(avail_cpus, max_cpus - current_cpus)
                    if cpus_to_add > 0:
                        new_cpus = current_cpus + cpus_to_add
                        self._scale_job_resources(job_id, new_cpus, running)
                        avail_cpus -= cpus_to_add
                        print(f"[mini-slurm] Scaled UP job {job_id}: {current_cpus} -> {new_cpus} CPUs "
                              f"(utilization: {util['overall_utilization']:.1f}%)")
        
        # Scale DOWN: Check if we need to free resources for high-priority pending jobs
        pending_jobs = self._get_pending_jobs()
        if pending_jobs:
            # Find highest priority pending job
            highest_priority = max(job[4] for job in pending_jobs)
            needed_cpus = sum(job[2] for job in pending_jobs if job[4] == highest_priority)
            
            if needed_cpus > avail_cpus:
                # Need to scale down elastic jobs to make room
                cpus_needed = needed_cpus - avail_cpus
                for job_id, current_cpus, min_cpus, max_cpus, priority, control_file in elastic_jobs:
                    if job_id not in running:
                        continue
                    if cpus_needed <= 0:
                        break
                    
                    if current_cpus > min_cpus:
                        # Scale down this job
                        cpus_to_release = min(cpus_needed, current_cpus - min_cpus)
                        new_cpus = current_cpus - cpus_to_release
                        self._scale_job_resources(job_id, new_cpus, running)
                        cpus_needed -= cpus_to_release
                        avail_cpus += cpus_to_release
                        print(f"[mini-slurm] Scaled DOWN job {job_id}: {current_cpus} -> {new_cpus} CPUs "
                              f"(to make room for priority {highest_priority} jobs)")
    
    def _scale_job_resources(self, job_id: int, new_cpus: int, running: dict):
        """Update resource allocation for a running elastic job."""
        if job_id not in running:
            return
        
        info = running[job_id]
        old_cpus = info["cpus"]
        
        # Update database
        self._update_job_cpus(job_id, new_cpus)
        
        # Update in-memory tracking
        info["cpus"] = new_cpus
        
        # Update control file
        if info.get("control_file") and os.path.exists(info["control_file"]):
            try:
                with open(info["control_file"], 'r') as f:
                    lines = f.readlines()
                
                # Update CPUS line
                updated_lines = []
                for line in lines:
                    if line.startswith("CPUS="):
                        updated_lines.append(f"CPUS={new_cpus}\n")
                    elif line.startswith("SCALE_EVENT="):
                        # Update or add scale event
                        updated_lines.append(f"SCALE_EVENT={time.time()}\n")
                    else:
                        updated_lines.append(line)
                
                # Add scale event if not present
                if not any("SCALE_EVENT=" in line for line in updated_lines):
                    updated_lines.append(f"SCALE_EVENT={time.time()}\n")
                
                with open(info["control_file"], 'w') as f:
                    f.writelines(updated_lines)
            except (OSError, IOError) as e:
                print(f"[mini-slurm] Warning: Could not update control file for job {job_id}: {e}", 
                      file=sys.stderr)
        
        # Send SIGUSR1 signal to notify the job (if supported)
        try:
            proc = info["proc"]
            if proc.poll() is None:  # Process still running
                proc.send_signal(signal.SIGUSR1)
        except (OSError, AttributeError):
            pass  # Signal not supported or process already dead
